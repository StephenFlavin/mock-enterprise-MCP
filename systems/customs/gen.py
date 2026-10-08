def generate(g):
    """Generate customs and trade compliance data."""
    from datetime import timedelta

    # Master data
    suppliers = g.master("suppliers")
    pos = g.master("purchase_orders")
    pos_lines = g.master("po_lines")
    products = g.master("products")
    shipments = g.master("shipments")

    # Get unique origin countries and suppliers
    origin_countries = ["Bangladesh", "China", "India", "Indonesia", "Vietnam", "Turkey", "GB", "USA"]
    destination_countries = ["GB", "US", "DE", "FR", "IE"]
    hs_codes_data = {
        "6110": {"desc": "Jerseys, pullovers, cardigans (knitted)", "category": "Apparel", "duty": 12.0},
        "6114": {"desc": "Other garments (knitted)", "category": "Apparel", "duty": 12.0},
        "6204": {"desc": "Women's skirts and trousers", "category": "Apparel", "duty": 12.5},
        "3004": {"desc": "Medicinal preparations", "category": "Pharma", "duty": 0.0},
        "2710": {"desc": "Petroleum oils", "category": "Energy", "duty": 2.5},
        "2207": {"desc": "Undenatured ethanol", "category": "Chemicals", "duty": 5.5},
        "7326": {"desc": "Articles of iron or steel", "category": "Metals", "duty": 4.0},
        "8407": {"desc": "Piston engines", "category": "Machinery", "duty": 0.0},
    }

    STORY_HS = {"6109", "6110", "6201", "6202", "6403", "8507", "8414"}  # tariffs, rules, volumes for these are seeded
    cc = {"CN": "China", "VN": "Vietnam", "BD": "Bangladesh", "TR": "Turkey", "IN": "India", "ID": "Indonesia"}
    sup_by_id = {s["supplier_id"]: s for s in suppliers}
    pos_by_sup = {}
    for po in pos:
        pos_by_sup.setdefault(po["supplier_id"], []).append(po["po_id"])
    ship_sups = [s["supplier_id"] for s in suppliers if s["country"] in cc and s["supplier_id"] in pos_by_sup
                 and s["supplier_id"] not in ("SUP-0008", "SUP-0001", "SUP-0023", "SUP-0053")]

    # Generate shipments
    shipments_data = []
    for i, shp in enumerate(shipments[:120]):
        shipment_id = f"SHP-{i+1:06d}"
        sup_id = g.pick(ship_sups)
        origin = cc[sup_by_id[sup_id]["country"]]
        destination = "GB"

        # Random dates
        ship_date = g.days_ago(g.rng.randint(10, 180))
        expected_arrival = ship_date + timedelta(days=g.rng.randint(14, 40))

        # Some arrive, some are pending/held
        if g.rng.random() > 0.15:
            actual_arrival = expected_arrival + timedelta(days=g.rng.randint(-5, 15))
            clearance_status = g.rng.choices(["cleared", "released"], [0.9, 0.1])[0]
        else:
            actual_arrival = None
            clearance_status = g.rng.choices(["pending", "held"], [0.6, 0.4])[0]

        lead_time_days = (actual_arrival - ship_date).days if actual_arrival else None

        shipments_data.append({
            "shipment_id": shipment_id,
            "po_id": g.pick(pos_by_sup[sup_id]),
            "supplier_id": sup_id,
            "origin_country": origin,
            "destination": "DC1" if g.rng.random() > 0.3 else g.pick(["DC2", "DC3", "DC4", "DC5"]),
            "ship_date": ship_date,
            "expected_arrival": expected_arrival,
            "actual_arrival": actual_arrival,
            "clearance_status": clearance_status,
            "hold_reason": "Classification issue" if clearance_status == "held" else None,
            "cleared_at": actual_arrival if clearance_status in ["cleared", "released"] else None,
            "lead_time_days": lead_time_days,
            "updated_at": g.days_ago(0),
            "destination_country": "GB",
            "partner_id": None,
        })

    # Generate customs declarations
    declarations_data = []
    for i, shp_rec in enumerate(shipments_data[:100]):
        declaration_id = f"DEC-{i+1:06d}"
        hs_code = g.pick(list(hs_codes_data.keys()))
        quantity = g.rng.randint(50, 5000)
        declared_value = quantity * g.rng.uniform(2, 50)
        duty_amount = declared_value * (hs_codes_data[hs_code]["duty"] / 100)

        # Declaration status correlated with shipment clearance
        if shp_rec["clearance_status"] == "cleared":
            dec_status = "cleared"
            cleared_at = shp_rec["actual_arrival"]
        elif shp_rec["clearance_status"] == "held":
            dec_status = g.rng.choices(["queried", "pending"], [0.7, 0.3])[0]
            cleared_at = None
        else:
            dec_status = "pending"
            cleared_at = None

        declarations_data.append({
            "declaration_id": declaration_id,
            "shipment_id": shp_rec["shipment_id"],
            "po_id": shp_rec["po_id"],
            "supplier_id": shp_rec["supplier_id"],
            "origin_country": shp_rec["origin_country"],
            "destination_country": "GB",
            "hs_code": hs_code,
            "product_description": hs_codes_data[hs_code]["desc"],
            "quantity": quantity,
            "declared_value_gbp": round(declared_value, 2),
            "duty_amount_gbp": round(duty_amount, 2),
            "status": dec_status,
            "declared_at": shp_rec["ship_date"],
            "cleared_at": cleared_at,
            "query_id": f"QRY-{i+1:06d}" if dec_status == "queried" else None,
            "updated_at": g.days_ago(0),
        })

    # Generate customs queries
    queries_data = []
    for i, dec in enumerate(declarations_data):
        if dec["status"] == "queried" and dec["query_id"]:
            query_type = g.pick(["classification", "valuation", "origin", "documentation"])
            queries_data.append({
                "query_id": dec["query_id"],
                "declaration_id": dec["declaration_id"],
                "supplier_id": dec["supplier_id"],
                "query_date": dec["declared_at"],
                "query_type": query_type,
                "description": f"Query on {query_type} for HS {dec['hs_code']}",
                "response_date": dec["declared_at"] + timedelta(days=1),
                "response_text": f"Clarification requested on {query_type}",
                "resolved_at": None,
            })

    # Generate customs holds
    holds_data = []
    for i, shp_rec in enumerate(shipments_data[:30]):
        if shp_rec["clearance_status"] == "held":
            hold_id = f"HLD-{i+1:06d}"
            holds_data.append({
                "hold_id": hold_id,
                "shipment_id": shp_rec["shipment_id"],
                "declaration_id": f"DEC-{i+1:06d}",
                "supplier_id": shp_rec["supplier_id"],
                "hold_date": shp_rec["expected_arrival"],
                "hold_type": "hold",
                "destination_country": "GB",
                "hold_reason": g.pick(["classification", "valuation", "origin", "dangerous_goods", "documentation"]),
                "resolved_at": shp_rec["actual_arrival"] if g.rng.random() > 0.3 else None,
                "resolution_notes": "Issue resolved" if g.rng.random() > 0.3 else None,
                "financial_impact_gbp": round(g.rng.uniform(100, 5000), 2),
            })

    # Generate HS codes
    hs_codes_table = []
    for hs_code, info in hs_codes_data.items():
        hs_codes_table.append({
            "hs_code": hs_code,
            "description": info["desc"],
            "category": info["category"],
            "base_duty_rate_pct": info["duty"],
            "classification_guidance": f"Classification rules for {hs_code}: examine materials and construction",
            "updated_at": g.days_ago(30),
        })

    # Generate tariffs
    tariffs_data = []
    tariff_id = 1
    for hs_code in hs_codes_data.keys():
        if hs_code in STORY_HS:
            continue
        for origin in origin_countries[:6]:
            for dest in ["GB", "EU", "US"]:
                # Base and preferential rates
                base_rate = hs_codes_data[hs_code]["duty"]
                pref_rate = base_rate * 0.75 if origin not in ["USA"] else base_rate

                tariffs_data.append({
                    "tariff_id": f"TAR-{tariff_id:06d}",
                    "hs_code": hs_code,
                    "origin_country": origin,
                    "destination_country": dest,
                    "base_rate_pct": base_rate,
                    "preferential_rate_pct": pref_rate if pref_rate < base_rate else None,
                    "effective_from": g.days_ago(365),
                    "effective_to": None,
                    "trade_agreement": "UK-Vietnam" if origin == "Vietnam" else "CPTPP" if origin in ["Vietnam", "Indonesia"] else None,
                })
                tariff_id += 1

    # Generate tariff changes
    tariff_changes = []
    change_id = 1
    for hs_code in ["3004", "2710"]:
        for origin in origin_countries[:3]:
            old_rate = hs_codes_data[hs_code]["duty"]
            new_rate = old_rate * g.rng.uniform(1.05, 1.15)
            tariff_changes.append({
                "change_id": f"CHG-{change_id:06d}",
                "hs_code": hs_code,
                "origin_country": origin,
                "destination_country": "GB",
                "old_rate_pct": old_rate,
                "new_rate_pct": round(new_rate, 2),
                "change_date": g.days_ago(30),
                "effective_date": g.days_ago(15),
                "reason": "Section 301 investigation" if g.rng.random() > 0.5 else "Tariff review",
            })
            change_id += 1

    # Generate additional remedies
    remedies_data = []
    remedy_id = 1
    for hs_code in ["2710"]:
        for origin in ["China", "Vietnam"]:
            remedies_data.append({
                "remedy_id": f"REM-{remedy_id:06d}",
                "hs_code": hs_code,
                "origin_country": origin,
                "destination_country": "GB",
                "remedy_type": g.pick(["safeguard", "anti_dumping", "countervailing"]),
                "additional_rate_pct": round(g.rng.uniform(5, 25), 2),
                "effective_from": g.days_ago(60),
                "effective_to": g.days_ago(-180),
                "description": "Additional tariff on goods from this origin",
            })
            remedy_id += 1

    # Generate origin rules
    origin_rules = []
    rule_id = 1
    for hs_code in hs_codes_data.keys():
        if hs_code.startswith(("61", "62")):
            continue  # apparel origin rules are seeded at chapter level
        for origin in ["Vietnam", "Bangladesh"]:
            origin_rules.append({
                "rule_id": f"ORG-{rule_id:06d}",
                "destination_country": "GB",
                "how_to_qualify": "Meet the regional value content threshold with originating inputs",
                "hs_code": hs_code,
                "origin_country": origin,
                "trade_agreement": "UK-Vietnam" if origin == "Vietnam" else "GSP",
                "rule_description": f"Rule of origin for {hs_code} from {origin}: minimum {60 + g.rng.randint(0, 20)}% regional value content",
                "value_content_threshold_pct": 60 + g.rng.randint(0, 20),
                "required_documents": "Certificate of origin, invoice, packing list",
                "eligibility_criteria": f"Goods must be substantially transformed in {origin}",
            })
            rule_id += 1

    # Generate de minimis thresholds
    de_minimis = []
    thresholds = {"GB": 135, "US": 0, "DE": 0, "FR": 0, "IE": 0}
    for country_code, threshold in thresholds.items():
        de_minimis.append({
            "country_code": country_code,
            "country_name": {"GB": "United Kingdom", "US": "United States", "DE": "Germany", "FR": "France", "IE": "Ireland"}[country_code],
            "threshold_gbp": threshold,
            "effective_from": g.days_ago(365),
            "effective_to": None,
        })

    # Generate dangerous goods restrictions
    dangerous_goods = []
    dg_id = 1
    for hs_code in ["3004", "2207"]:
        for origin in ["China", "India"]:
            dangerous_goods.append({
                "restriction_id": f"DGR-{dg_id:06d}",
                "hs_code": hs_code,
                "material_code": "UN1090" if hs_code == "2207" else "UN3082",
                "origin_country": origin,
                "destination_country": "GB",
                "restriction_type": g.pick(["prohibited", "licensed", "limited"]),
                "description": f"Dangerous goods restrictions for {hs_code} from {origin}",
                "transport_mode": "all",
                "updated_at": g.days_ago(0),
            })
            dg_id += 1

    # Generate binding rulings (background rulings on non-story goods)
    binding_rulings = []
    bg = [("Industrial ethanol 96% in drums", "2207", "2710", "UK", "GBBTI-2025-0150"),
          ("Steel storage racking components", "7326", "8407", "UK", "GBBTI-2025-0721"),
          ("Liquid paracetamol oral suspension", "3004", "2207", "EU", "EBTI-2025-NL-3302"),
          ("Aluminium-coated steel shelving brackets", "7326", "2710", "EU", "EBTI-2026-DE-0088")]
    for i, (prod, hs_applied, hs_alt, jur, ref) in enumerate(bg):
        binding_rulings.append({
            "ruling_id": f"BRG-{i+1:06d}",
            "jurisdiction": jur,
            "ruling_reference": ref,
            "status": "approved",
            "product_description": prod,
            "hs_code_applied": hs_applied,
            "hs_code_alternative": hs_alt,
            "duty_difference_pct": round(hs_codes_data[hs_applied]["duty"] - hs_codes_data[hs_alt]["duty"], 2),
            "argument_for_applied": f"Goods fall under the terms of heading {hs_applied}",
            "argument_for_alternative": f"Could alternatively be argued under heading {hs_alt}",
            "created_date": g.days_ago(300 + 20 * i),
            "submitted_date": g.days_ago(300 + 20 * i),
            "decided_date": g.days_ago(260 + 20 * i),
            "ruling_decision": f"Classified {hs_applied}",
            "effective_from": g.days_ago(260 + 20 * i),
        })

    # Generate customs authorisations
    auths_data = [
        {"auth_id": "AUTH-000001", "status": "approved", "auth_type": "temporary_admission", "supplier_id": None,
         "description": "Temporary admission of trade show and photography samples", "created_date": g.days_ago(400),
         "submitted_date": g.days_ago(390), "decided_date": g.days_ago(360),
         "conditions_text": "Goods re-exported within 12 months; samples register kept; guarantee 20,000 GBP",
         "valid_from": g.days_ago(360), "valid_to": g.days_ago(-370)},
        {"auth_id": "AUTH-000002", "status": "rejected", "auth_type": "inward_processing", "supplier_id": None,
         "description": "IPR for fabric finishing, application withdrawn after records review", "created_date": g.days_ago(330),
         "submitted_date": g.days_ago(320), "decided_date": g.days_ago(270),
         "conditions_text": "Rejected: stock and processing records could not show goods identity",
         "valid_from": None, "valid_to": None},
    ]

    # Generate duty drawback claims
    drawback_claims = []
    for i, dec in enumerate(declarations_data[:15]):
        claim_id = f"DBC-{i+1:06d}"
        status = g.rng.choices(["draft", "submitted", "approved"], [0.3, 0.4, 0.3])[0]

        drawback_claims.append({
            "claim_id": claim_id,
            "status": status,
            "po_id": dec["po_id"],
            "declaration_id": dec["declaration_id"],
            "claim_amount_gbp": dec["duty_amount_gbp"] * g.rng.uniform(0.5, 0.9),
            "created_date": g.days_ago(g.rng.randint(10, 90)),
            "submitted_date": g.days_ago(g.rng.randint(0, 60)) if status in ["submitted", "approved"] else None,
            "decided_date": g.days_ago(g.rng.randint(0, 30)) if status == "approved" else None,
            "paid_date": g.days_ago(g.rng.randint(0, 10)) if status == "approved" else None,
            "reason": "Goods re-exported to third country",
        })

    # Generate classification positions
    positions_data = []
    for i, sku in enumerate(g.pick([p for p in g.master("products") if p["status"] != "new"], 10)):
        position_id = f"POS-{i+1:06d}"
        positions_data.append({
            "position_id": position_id,
            "sku": sku["sku"],
            "hs_code": g.pick(list(hs_codes_data.keys())),
            "status": g.rng.choices(["active", "review"], [0.8, 0.2])[0],  # weakest/high-risk positions are seeded
            "valuation_method": g.pick(["transaction_value", "identical_goods", "similar_goods", "deductive", "computed", "fallback"]),
            "risk_rating": g.rng.choices(["low", "medium"], [0.7, 0.3])[0],
            "created_date": g.days_ago(g.rng.randint(90, 365)),
            "last_reviewed_date": g.days_ago(g.rng.randint(0, 30)),
            "notes": "Position under review",
        })

    # Generate first sale transactions
    first_sale = []
    for i, po_line in enumerate(g.pick(pos_lines, 12)):
        transaction_id = f"FST-{i+1:06d}"
        price = g.rng.uniform(5, 50)
        first_sale_price = price * g.rng.uniform(0.7, 0.95)

        first_sale.append({
            "transaction_id": transaction_id,
            "po_id": po_line.get("po_id", "PO-2026-000001"),
            "sku": po_line.get("sku", "SKU-0001"),
            "supplier_id": g.pick([s["supplier_id"] for s in suppliers[:10]]),
            "price_gbp": round(price, 2),
            "transaction_date": g.days_ago(g.rng.randint(30, 180)),
            "original_buyer_name": g.fake.company(),
            "first_sale_purchase_price_gbp": round(first_sale_price, 2),
            "our_purchase_price_gbp": round(price, 2),
            "eligible_for_first_sale": g.rng.random() > 0.3,
            "evidence_held": g.rng.random() > 0.4,
        })

    # Generate lead times
    lead_times_data = []
    routes = [
        ("Dhaka", "London", "Bangladesh", "GB"),
        ("Ho Chi Minh", "London", "Vietnam", "GB"),
        ("Shanghai", "London", "China", "GB"),
        ("Dubai", "London", "UAE", "GB"),
        ("Mumbai", "London", "India", "GB"),
        ("Istanbul", "London", "Turkey", "GB"),
    ]

    route_id = 1
    for origin, dest, orig_country, dest_country in routes:
        for mode in ["air", "sea", "rail"]:
            if mode == "air":
                days = g.rng.randint(5, 12)
            elif mode == "sea":
                days = g.rng.randint(25, 45)
            else:
                days = g.rng.randint(20, 35)

            lead_times_data.append({
                "route_id": f"RT-{route_id:06d}",
                "origin_port": origin,
                "destination_port": dest,
                "origin_country": orig_country,
                "destination_country": dest_country,
                "mode": mode,
                "lead_time_days": days,
                "variance_days": g.rng.randint(1, 5),
                "last_updated": g.days_ago(0),
            })
            route_id += 1

    # Generate required origin documents (background lanes; Vietnam, Bangladesh and Turkey are seeded)
    required_docs = []
    doc_id = 1
    for origin in ["China", "India"]:
        for dest in ["GB", "EU"]:
            for doc_type in ["certificate_of_origin", "invoice", "packing_list"]:
                required_docs.append({
                    "doc_id": f"DOC-{doc_id:06d}",
                    "origin_country": origin,
                    "destination_country": dest,
                    "trade_agreement": "MFN",
                    "document_type": doc_type,
                    "required": doc_type != "packing_list",
                    "issuing_body": "China Council for Promotion of International Trade" if doc_type == "certificate_of_origin" and origin == "China" else "Exporter",
                    "validity_period_months": 12 if doc_type == "certificate_of_origin" else 3,
                })
                doc_id += 1

    # Generate import volumes: cotton apparel and linen (story) by origin with a stable mix, plus background codes
    import_volumes = []
    volume_id = 1
    cotton = {  # hs: (monthly units, value per unit, {origin: share})
        "6109": (180000, 3.8, {"China": 0.38, "Bangladesh": 0.27, "India": 0.12, "Vietnam": 0.14, "Turkey": 0.09}),
        "6110": (95000, 9.0, {"China": 0.30, "Bangladesh": 0.28, "Vietnam": 0.22, "Turkey": 0.12, "India": 0.08}),
        "6203": (60000, 11.0, {"China": 0.22, "Bangladesh": 0.30, "Vietnam": 0.20, "Turkey": 0.18, "India": 0.10}),
        "6302": (70000, 8.0, {"China": 0.20, "India": 0.35, "Turkey": 0.30, "Bangladesh": 0.10, "Vietnam": 0.05}),
    }
    eff = {"China": 12.0, "Bangladesh": 0.0, "Vietnam": 8.0, "Turkey": 9.0, "India": 10.0}
    for hs_code, (units_m, unit_val, shares) in cotton.items():
        for origin, share in shares.items():
            for i in range(12):
                month_str = g.days_ago(30 * (12 - i)).strftime("%Y-%m")
                season = 1.0 + 0.15 * ((i % 12) in (3, 4, 8, 9)) - 0.1 * ((i % 12) in (0, 1))
                units = int(units_m * share * season * g.rng.uniform(0.95, 1.05))
                value = units * unit_val
                import_volumes.append({
                    "volume_id": f"VOL-{volume_id:06d}", "hs_code": hs_code, "origin_country": origin,
                    "destination_country": "GB", "period_month": month_str, "quantity_units": units,
                    "value_gbp": round(value, 2), "duty_paid_gbp": round(value * eff[origin] / 100, 2),
                })
                volume_id += 1
    for hs_code in ["3004", "2710", "2207", "7326"]:
        for origin in origin_countries[:3]:
            for i in range(12):
                month_str = g.days_ago(30 * (12 - i)).strftime("%Y-%m")
                volume = g.rng.randint(100, 2000)
                value = volume * g.rng.uniform(5, 100)
                import_volumes.append({
                    "volume_id": f"VOL-{volume_id:06d}", "hs_code": hs_code, "origin_country": origin,
                    "destination_country": "GB", "period_month": month_str, "quantity_units": volume,
                    "value_gbp": round(value, 2), "duty_paid_gbp": round(value * hs_codes_data[hs_code]["duty"] / 100, 2),
                })
                volume_id += 1

    # Generate broker amendment requests
    broker_requests = []
    for i, hold in enumerate(holds_data[:10]):
        request_id = f"BAR-{i+1:06d}"
        broker_requests.append({
            "request_id": request_id,
            "declaration_id": hold["declaration_id"],
            "supplier_id": hold["supplier_id"],
            "amendment_type": hold["hold_reason"],
            "description": f"Please amend declaration due to {hold['hold_reason']} issue",
            "status": g.rng.choices(["sent", "acknowledged", "completed"], [0.3, 0.4, 0.3])[0],
            "sent_date": hold["hold_date"],
            "completed_date": hold["hold_date"] + timedelta(days=g.rng.randint(5, 20)) if g.rng.random() > 0.3 else None,
        })

    # Generate declaration amendments
    amendments = []
    for i, dec in enumerate(declarations_data[:20]):
        if i % 4 == 0:  # Create amendments for ~25% of declarations
            amendment_id = f"AMN-{i+1:06d}"
            amendments.append({
                "amendment_id": amendment_id,
                "declaration_id": dec["declaration_id"],
                "amendment_type": g.pick(["valuation", "classification", "documentation", "origin"]),
                "description": f"Amendment to correct {dec['product_description']}",
                "status": g.rng.choices(["draft", "submitted", "approved"], [0.2, 0.5, 0.3])[0],
                "submitted_date": dec["declared_at"] + timedelta(days=g.rng.randint(1, 10)) if g.rng.random() > 0.4 else None,
                "approved_date": dec["declared_at"] + timedelta(days=g.rng.randint(5, 30)) if g.rng.random() > 0.5 else None,
                "created_date": dec["declared_at"],
            })

    return {
        "customs_declarations": declarations_data,
        "shipments": shipments_data,
        "customs_queries": queries_data,
        "customs_holds": holds_data,
        "hs_codes": hs_codes_table,
        "tariffs": tariffs_data,
        "tariff_changes": tariff_changes,
        "additional_remedies": remedies_data,
        "origin_rules": origin_rules,
        "de_minimis_thresholds": de_minimis,
        "dangerous_goods_restrictions": dangerous_goods,
        "binding_rulings": binding_rulings,
        "customs_authorisations": auths_data,
        "duty_drawback_claims": drawback_claims,
        "classification_positions": positions_data,
        "first_sale_transactions": first_sale,
        "lead_times": lead_times_data,
        "required_origin_documents": required_docs,
        "import_volumes": import_volumes,
        "broker_amendment_requests": broker_requests,
        "declaration_amendments": amendments,
    }
