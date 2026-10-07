"""Landed cost data: cost breakdowns for POs, freight rates, tariffs, and FX rates."""
from datetime import datetime, timedelta


def generate(g):
    r = g.rng

    # Get unique suppliers, factories, products, carriers, and ports from master
    suppliers = g.master("suppliers")
    factories = g.master("factories")
    products = g.master("products")
    carriers = g.master("carriers")
    ports = g.master("ports")
    purchase_orders = g.master("purchase_orders")
    po_lines = g.master("po_lines")

    # Build lookup dictionaries
    supplier_map = {s["supplier_id"]: s for s in suppliers}
    factory_map = {f["factory_id"]: f for f in factories}
    product_map = {p["sku"]: p for p in products}
    port_map = {p["port_code"]: p for p in ports}

    ocean_carriers = [c for c in carriers if c["mode"] == "ocean"]
    air_carriers = [c for c in carriers if c["mode"] == "air"]
    forwarders = [c for c in carriers if c["mode"] == "forwarder"]

    # Generate landed cost summaries for recent POs
    lc_summaries = []
    fc_rates = []
    tariff_rates_list = []
    fx_rates_list = []
    scenarios = []

    # Track carriers for freight rates
    all_carriers_for_freight = ocean_carriers + air_carriers + forwarders

    # Generate landed cost data for POs in the last 180 days
    for po in purchase_orders:
        po_date = datetime.fromisoformat(po["order_date"])
        days_from_now = (po_date.date() - g.as_of).days

        # Only include recent POs (last 180 days)
        if not -180 <= days_from_now <= 0 or po["status"] in ("draft", "cancelled"):
            continue

        # Get supplier and factory details
        supplier = supplier_map.get(po["supplier_id"])
        factory = factory_map.get(po["factory_id"])
        if not supplier or not factory:
            continue

        # Get PO lines for cost info
        po_line_costs = []
        for line in po_lines:
            if line["po_id"] == po["po_id"]:
                po_line_costs.append(line)

        if not po_line_costs:
            continue

        # Calculate landed cost for this PO
        for line in po_line_costs:
            sku = line["sku"]
            if sku not in product_map:
                continue

            product = product_map[sku]
            units = int(line["qty_ordered"])

            # FOB unit cost (from PO)
            fob_unit = float(line["unit_cost"])

            # Freight cost varies by mode and origin
            freight_unit = 0
            lead_time = 0
            mode = po["mode"]

            if mode == "sea":
                freight_unit = r.uniform(1.5, 5.0)  # £1.50-5.00 per unit for sea
                lead_time = r.randint(20, 45)
            elif mode == "air":
                freight_unit = r.uniform(5.0, 15.0)  # £5-15 per unit for air
                lead_time = r.randint(5, 15)
            elif mode == "rail":
                freight_unit = r.uniform(2.0, 4.0)
                lead_time = r.randint(15, 30)
            else:  # road
                freight_unit = r.uniform(0.5, 2.0)
                lead_time = r.randint(3, 10)

            # Duty rate based on origin country and HS code
            origin = factory["country"]
            duty_rate = r.choice([5, 8, 10, 12, 15]) if origin not in ("GB", "EU") else 0
            duty_unit = fob_unit * (duty_rate / 100.0)

            # FX rate (if not GBP)
            fx_rate = 1.0
            if supplier["currency"] != "GBP":
                fx_rates_dict = {
                    "USD": r.uniform(0.78, 0.82),
                    "EUR": r.uniform(1.15, 1.25),
                    "CNY": r.uniform(0.11, 0.12),
                    "INR": r.uniform(0.011, 0.012),
                    "VND": r.uniform(0.000031, 0.000034),
                }
                fx_rate = fx_rates_dict.get(supplier["currency"], 1.0)

            # Insurance and handling
            insurance_unit = (fob_unit + freight_unit) * 0.005  # 0.5% of value
            handling_unit = (fob_unit + freight_unit) * 0.01  # 1% of value

            # Inventory holding cost (annual rate / 52 weeks * lead time)
            holding_rate = 0.15  # 15% per annum
            weeks_held = max(1, lead_time // 7)
            inventory_holding_unit = fob_unit * (holding_rate / 52.0) * weeks_held

            # Total landed cost
            landed_cost_unit = fob_unit + freight_unit + duty_unit + insurance_unit + handling_unit + inventory_holding_unit
            total_landed_cost = landed_cost_unit * units

            lc_summaries.append({
                "lc_id": f"LC-{len(lc_summaries) + 1:06d}",
                "po_id": po["po_id"],
                "sku": sku,
                "supplier_id": po["supplier_id"],
                "origin_country": origin,
                "units": units,
                "fob_unit_gbp": fob_unit,
                "freight_unit_gbp": freight_unit,
                "duty_unit_gbp": duty_unit,
                "insurance_unit_gbp": insurance_unit,
                "handling_unit_gbp": handling_unit,
                "inventory_holding_unit_gbp": inventory_holding_unit,
                "landed_cost_unit_gbp": landed_cost_unit,
                "total_landed_cost_gbp": total_landed_cost,
                "fx_rate": fx_rate,
                "mode": mode,
                "lead_time_days": lead_time,
                "updated_at": po_date,
            })

    # Generate freight rates for key routes
    unique_origins = set()
    unique_dests = set()
    for lc in lc_summaries:
        # Match to a port based on origin country
        for port in ports:
            if port["country"] == lc["origin_country"]:
                unique_origins.add(port["port_code"])
                break
        unique_dests.add(lc.get("dest_site_id", "DC1"))

    # Build freight rates
    for origin_port in list(unique_origins)[:5]:
        for dest_site in ["DC1", "DC2", "DC3"]:
            for mode in ["sea", "air", "rail"]:
                for carrier in all_carriers_for_freight[:2]:
                    if carrier["mode"] not in (mode, "forwarder"):
                        continue

                    rate_unit = r.uniform(1, 8) if mode == "sea" else (r.uniform(5, 15) if mode == "air" else r.uniform(2, 4))
                    rate_container = rate_unit * 5000 if mode == "sea" else 0
                    lead = r.randint(5, 45) if mode == "sea" else (r.randint(5, 15) if mode == "air" else r.randint(15, 30))
                    reliability = r.uniform(85, 99)

                    fc_rates.append({
                        "rate_id": f"FR-{len(fc_rates) + 1:06d}",
                        "origin_port": origin_port,
                        "dest_port": "GBFXT",  # Felixstowe as destination
                        "dest_site_id": dest_site,
                        "mode": mode,
                        "carrier_id": carrier["carrier_id"],
                        "rate_per_unit_gbp": rate_unit,
                        "rate_per_container_gbp": rate_container,
                        "min_qty": 100 if mode == "air" else 500,
                        "lead_time_days": lead,
                        "effective_from": g.as_of - timedelta(days=90),
                        "effective_to": g.as_of + timedelta(days=365),
                        "transit_days_p50": lead,
                        "transit_days_p95": lead + 5,
                        "reliability_pct": reliability,
                    })

    # Generate tariff rates for key origins and HS codes
    origins_for_tariffs = ["CN", "VN", "BD", "IN", "ID", "TH", "KH", "MM"]
    hs_codes_samples = ["6109", "6204", "6205", "6206", "6209", "6211", "6212", "5911"]  # Apparel codes

    for origin in origins_for_tariffs:
        for hs_code in hs_codes_samples:
            duty_rate = r.choice([5, 8, 10, 12, 15, 18, 20])
            vat_rate = 20 if origin != "GB" else 0
            contingency = r.uniform(2, 8)

            tariff_rates_list.append({
                "tariff_id": f"TAR-{len(tariff_rates_list) + 1:06d}",
                "hs_code": hs_code,
                "origin_country": origin,
                "dest_country": "GB",
                "duty_rate_pct": duty_rate,
                "vat_rate_pct": vat_rate,
                "effective_from": g.as_of - timedelta(days=180),
                "effective_to": g.as_of + timedelta(days=365),
                "contingency_pct": contingency,
                "notes": "",
            })

    # Generate FX rates
    currencies = ["USD", "EUR", "CNY", "INR", "VND"]
    for curr in currencies:
        pair = f"{curr}/GBP"
        rates_dict = {
            "USD": 0.8,
            "EUR": 1.2,
            "CNY": 0.115,
            "INR": 0.0115,
            "VND": 0.000032,
        }
        spot = rates_dict.get(curr, 1.0)

        for i in range(52):  # 52 weeks of rates
            rate_date = g.as_of - timedelta(days=i*7)
            spot_var = r.uniform(-0.02, 0.02)

            fx_rates_list.append({
                "currency_pair": pair,
                "rate_date": rate_date,
                "spot_rate": spot + spot_var,
                "forward_30d": spot + spot_var + r.uniform(0.002, 0.005),
                "forward_90d": spot + spot_var + r.uniform(0.005, 0.01),
                "forward_180d": spot + spot_var + r.uniform(0.01, 0.02),
            })

    # Generate cost scenarios
    for i in range(5):
        sku = r.choice(list(product_map.keys()))
        supplier_id = r.choice([s["supplier_id"] for s in suppliers])
        origin = r.choice(["CN", "VN", "BD", "IN"])

        fob = r.uniform(5, 30)
        freight = r.uniform(1, 8)
        duty_pct = r.choice([5, 10, 15, 20])
        fx = r.uniform(0.7, 1.2)
        insurance_pct = 0.5
        holding_pct = 15
        units = r.randint(5000, 50000)

        landed_cost_unit = fob * fx + freight + (fob * fx * duty_pct / 100) + (fob * fx * insurance_pct / 100)
        total_landed = landed_cost_unit * units

        scenarios.append({
            "scenario_id": f"SC-{len(scenarios) + 1:06d}",
            "scenario_name": f"Analysis {i+1}: {sku} from {origin}",
            "sku": sku,
            "supplier_id": supplier_id,
            "origin_country": origin,
            "dest_site_id": r.choice(["DC1", "DC2", "DC3"]),
            "units": units,
            "mode": r.choice(["sea", "air", "rail"]),
            "fob_unit_gbp": fob,
            "freight_unit_gbp": freight,
            "duty_rate_pct": duty_pct,
            "fx_rate": fx,
            "insurance_pct": insurance_pct,
            "holding_cost_pct_pa": holding_pct,
            "total_landed_cost_gbp": total_landed,
            "landed_cost_per_unit_gbp": landed_cost_unit,
            "created_at": g.as_of,
            "created_by": "EMP-00001",
        })

    return {
        "landed_cost_summary": lc_summaries,
        "freight_rates": fc_rates,
        "tariff_rates": tariff_rates_list,
        "fx_rates": fx_rates_list,
        "cost_scenarios": scenarios,
    }
