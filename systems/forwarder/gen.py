"""Background freight forwarder data: ocean and air bookings, invoices, demurrage/detention charges."""
from datetime import datetime, timedelta


def generate(g):
    """Generate forwarder data: ocean bookings, air freight bookings, invoices, charges."""
    r = g.rng

    # Get carriers and ports from master
    all_carriers = g.master("carriers")
    ocean_carriers = [c for c in all_carriers if c["mode"] in ["ocean", "forwarder"]]
    air_carriers = [c for c in all_carriers if c["mode"] == "air"]

    # Common ports
    ports = {
        "SGSIN": "Singapore",
        "CNSHA": "Shanghai",
        "HKHKG": "Hong Kong",
        "JPTYO": "Tokyo",
        "THBKK": "Bangkok",
        "GBFXT": "Felixstowe",
        "NLRTM": "Rotterdam",
        "FRPAR": "Paris",
        "DEWCY": "Cyprus"
    }

    ocean_bookings = []
    air_freight_bookings = []
    air_freight_invoices = []
    booking_events = []
    demurrage_detention = []

    # Generate ocean bookings from recent POs
    booking_id = 1
    event_id = 1
    po_idx = 0

    for po in g.master("purchase_orders"):
        if po_idx > 60:  # Limit POs to avoid too many bookings
            break
        po_idx += 1

        if po["status"] in ("cancelled", "draft"):
            continue

        due = datetime.fromisoformat(po["due_date"])
        days_to_due = (due.date() - g.as_of).days

        # Create ocean bookings for POs due in the next 120 days
        if -30 <= days_to_due <= 120:
            # Pick a random carrier and port pair
            carrier = r.choice(ocean_carriers)
            origin = r.choice(["SGSIN", "CNSHA", "HKHKG", "JPTYO"])
            dest = r.choice(["GBFXT", "NLRTM"])

            booking_date = due - timedelta(days=r.randint(35, 55))  # Book 5-8 weeks ahead
            sailing = booking_date + timedelta(days=r.randint(7, 21))
            cut_off = sailing - timedelta(days=r.randint(2, 5))
            eta = sailing + timedelta(days=r.randint(14, 18))

            # 15% of bookings get rolled
            rolled = r.random() < 0.15
            status = "rolled" if rolled else r.choices(["booked", "sailed", "in_transit", "delivered"], [0.2, 0.3, 0.3, 0.2])[0]

            booking = {
                "booking_id": f"OBK-{booking_id:06d}",
                "po_id": po["po_id"],
                "carrier_id": carrier["carrier_id"],
                "origin_port": origin,
                "dest_port": dest,
                "booking_date": booking_date,
                "planned_sailing": sailing,
                "cut_off_date": cut_off,
                "planned_eta": eta,
                "actual_departure": sailing + timedelta(days=r.randint(0, 3)) if status in ["sailed", "in_transit", "delivered"] else None,
                "actual_arrival": eta + timedelta(days=r.randint(-2, 5)) if status in ["in_transit", "delivered"] else None,
                "container_count": r.randint(2, 15),
                "booking_status": status,
                "roll_reason": r.choice(["Vessel blank sailed", "Equipment shortage", "Space allocation changed"]) if rolled else None,
                "cost_gbp": r.uniform(3000, 8000),
                "updated_at": datetime.combine(g.as_of, datetime.min.time()) + timedelta(days=r.randint(-30, 1))
            }
            ocean_bookings.append(booking)

            # Add demurrage/detention charges for some bookings
            if status == "delivered" and r.random() < 0.1:  # 10% have charges
                charge_date = datetime.fromisoformat(booking["actual_arrival"]).date() + timedelta(days=r.randint(1, 3))
                demurrage_detention.append({
                    "charge_id": f"CHG-{len(demurrage_detention) + 1:06d}",
                    "booking_id": booking["booking_id"],
                    "charge_type": r.choice(["demurrage", "detention"]),
                    "charge_date": charge_date,
                    "amount_gbp": r.uniform(500, 3000),
                    "days_or_units": r.randint(1, 7),
                    "port_id": booking["dest_port"],
                    "description": r.choice(["Dwell time at discharge", "Storage beyond free period", "Port congestion delay"])
                })

            # Add expedite events for some bookings (5%)
            if r.random() < 0.05 and status in ["booked", "sailed", "in_transit"]:
                booking_events.append({
                    "event_id": f"EVT-{event_id:06d}",
                    "booking_id": booking["booking_id"],
                    "event_type": "expedite_request",
                    "from_sailing": None,
                    "to_sailing": None,
                    "reason": r.choice(["Store stockout risk", "Promotional window closing", "Quality issue on backup"]),
                    "created_at": datetime.combine(g.as_of, datetime.min.time()) - timedelta(days=r.randint(1, 7))
                })
                event_id += 1

            # Add sailing change events for some bookings (3%)
            if r.random() < 0.03 and status in ["booked"]:
                original = booking["planned_sailing"]
                new_sailing = original + timedelta(days=r.randint(3, 14))
                booking_events.append({
                    "event_id": f"EVT-{event_id:06d}",
                    "booking_id": booking["booking_id"],
                    "event_type": "sailing_changed",
                    "from_sailing": original,
                    "to_sailing": new_sailing,
                    "reason": r.choice(["Avoid blank sailing", "Surcharge window", "Better rate"]),
                    "created_at": datetime.combine(g.as_of, datetime.min.time()) - timedelta(days=r.randint(1, 3))
                })
                event_id += 1

            booking_id += 1

    # Generate air freight bookings (fewer than ocean)
    air_booking_id = 1
    for i in range(8):
        carrier = r.choice(air_carriers)
        origin = r.choice(["SGSIN", "CNSHA", "HKHKG"])
        dest = "GBFXT"

        booking_date = g.date_between(60, 1)
        cut_off = booking_date + timedelta(days=r.randint(1, 3))
        departure = booking_date + timedelta(days=r.randint(3, 7))
        arrival = departure + timedelta(days=r.randint(2, 4))

        status = r.choices(["booked", "departed", "arrived", "delivered"], [0.15, 0.25, 0.35, 0.25])[0]

        air_booking = {
            "booking_id": f"ABK-{air_booking_id:06d}",
            "po_id": g.pick(g.master("purchase_orders"), 1)[0]["po_id"] if r.random() < 0.7 else None,
            "style_id": None,
            "carrier_id": carrier["carrier_id"],
            "origin_airport": origin,
            "dest_airport": dest,
            "booking_date": booking_date,
            "cut_off_date": cut_off,
            "planned_departure": departure,
            "planned_arrival": arrival,
            "actual_departure": departure if status in ["departed", "arrived", "delivered"] else None,
            "actual_arrival": arrival if status in ["arrived", "delivered"] else None,
            "units": r.randint(100, 2000),
            "booking_status": status,
            "cost_gbp": r.uniform(8000, 25000),
            "cost_per_unit_gbp": 0,  # Will be calculated
            "updated_at": datetime.combine(g.as_of, datetime.min.time()) + timedelta(days=r.randint(-30, 0))
        }
        air_booking["cost_per_unit_gbp"] = round(air_booking["cost_gbp"] / air_booking["units"], 2)
        air_freight_bookings.append(air_booking)
        air_booking_id += 1

    # Generate air freight invoices (quarterly summary)
    invoice_id = 1
    for quarter in range(4):  # Last 4 quarters
        period_start = g.date_between(365 - (quarter * 90), 365 - (quarter * 90) - 90)
        period_end = period_start + timedelta(days=90)

        for carrier in r.sample(air_carriers, min(2, len(air_carriers))):
            invoice = {
                "invoice_id": f"INV-{invoice_id:06d}",
                "carrier_id": carrier["carrier_id"],
                "period_start": period_start,
                "period_end": period_end,
                "shipment_count": r.randint(3, 12),
                "total_units": r.randint(500, 8000),
                "total_cost_gbp": r.uniform(15000, 120000),
                "reason_code": r.choices(
                    ["delayed_factory", "late_arrival", "promotional_surge", "supply_issue"],
                    [0.4, 0.25, 0.2, 0.15]
                )[0],
                "supplier_id": g.pick(g.master("suppliers"), 1)[0]["supplier_id"] if r.random() < 0.6 else None,
                "created_date": period_end
            }
            air_freight_invoices.append(invoice)
            invoice_id += 1

    return {
        "ocean_bookings": ocean_bookings,
        "air_freight_bookings": air_freight_bookings,
        "air_freight_invoices": air_freight_invoices,
        "booking_events": booking_events,
        "demurrage_detention": demurrage_detention
    }
