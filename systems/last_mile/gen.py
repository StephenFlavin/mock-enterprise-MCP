def generate(g):
    """Generate last-mile delivery data."""

    # Get reference data
    couriers = g.master("carriers")
    orders = g.master("orders")
    products = g.master("products")

    # Filter to parcel couriers
    parcel_couriers = [c for c in couriers if c.get("mode") == "parcel"][:5]

    # UK postcode areas for distribution
    uk_postcode_areas = ["N1", "N4", "N7", "N15", "SW1", "W1", "WC1", "E1", "SE1", "M1", "B1", "L1"]

    delivery_attempts = []
    delivery_scans = []
    address_validation_issues = []
    delivery_complaints = []

    attempt_counter = 1
    issue_counter = 1
    complaint_counter = 1

    # Generate delivery attempts from orders
    selected_orders = g.pick(orders, k=300)

    for order in selected_orders:
        order_id = order.get("order_id", f"ORD-{attempt_counter:07d}")

        # Determine region from order
        region = order.get("country", "GB")
        if region != "GB":
            continue  # Skip non-GB for this first version

        # Pick a postcode area
        postcode_area = g.pick(uk_postcode_areas)

        # Pick a courier
        courier = g.pick(parcel_couriers)
        courier_id = courier.get("carrier_id", f"CAR-{attempt_counter % 20:03d}")

        # Get main SKU from order (use first line's sku if available)
        sku = order.get("sku", "SKU-100001")

        # Determine number of delivery attempts (mostly 1, sometimes 2-3 for failures)
        num_attempts = 1
        if g.rng.random() < 0.15:  # 15% have failures that lead to retries
            num_attempts = g.rng.randint(2, 3)

        for attempt_num in range(1, num_attempts + 1):
            attempt_id = f"ATT-{attempt_counter:06d}"
            attempt_counter += 1

            # Date from 8 weeks ago to now
            weeks_back = g.rng.randint(0, 8)
            attempt_date = g.as_of - __import__("datetime").timedelta(weeks=weeks_back)

            # Promised delivery
            delivery_service = g.pick(["standard", "next_day", "same_day"])
            promised_offset = {"standard": 5, "next_day": 1, "same_day": 0}[delivery_service]
            promised_delivery_date = attempt_date + __import__("datetime").timedelta(days=promised_offset)

            # Delivery option
            delivery_option = g.pick(["door", "safe_place", "locker", "collect_point"])

            # Determine success/failure
            is_first_attempt = attempt_num == 1

            # Failure patterns: address (10%), customer (12%), courier quality (5%)
            address_fail = is_first_attempt and g.rng.random() < 0.10
            customer_fail = is_first_attempt and g.rng.random() < 0.12
            courier_fail = is_first_attempt and g.rng.random() < 0.05

            status = "failed" if (address_fail or customer_fail or courier_fail) else "delivered"

            # After failure, next attempt is more likely to succeed
            if attempt_num > 1:
                status = "delivered" if g.rng.random() < 0.85 else "failed"

            failure_reason = ""
            if status == "failed":
                if address_fail:
                    failure_reason = "Address not found"
                elif customer_fail:
                    failure_reason = "Customer not available"
                else:
                    failure_reason = "Delivery access issue"

            # Damage rate
            damage_reported = g.rng.random() < 0.02 if status == "delivered" else False

            # Complaint rate
            complaint_raised = g.rng.random() < 0.03 if status == "delivered" else g.rng.random() < 0.15

            # Cost per drop
            cost_gbp = round(g.rng.uniform(2.0, 6.0), 2)

            # Tracking scans
            if status == "delivered":
                has_tracking_scans = g.rng.randint(3, 8)
            elif status == "failed":
                has_tracking_scans = g.rng.randint(1, 3)
            else:
                has_tracking_scans = 0

            # Delivery time (if delivered)
            delivery_time = None
            if status == "delivered":
                delivery_time = attempt_date + __import__("datetime").timedelta(
                    hours=g.rng.randint(2, 36),
                    minutes=g.rng.randint(0, 59)
                )

            attempt = {
                "attempt_id": attempt_id,
                "order_id": order_id,
                "courier_id": courier_id,
                "sku": sku,
                "postcode_area": postcode_area,
                "delivery_service": delivery_service,
                "delivery_option": delivery_option,
                "attempt_number": attempt_num,
                "promised_delivery_date": promised_delivery_date,
                "actual_delivery_date": delivery_time.date() if delivery_time else None,
                "attempt_time": attempt_date,
                "delivery_time": delivery_time,
                "status": status,
                "failure_reason": failure_reason,
                "address_issue": address_fail,
                "customer_availability": customer_fail,
                "damage_reported": damage_reported,
                "complaint_raised": complaint_raised,
                "has_tracking_scans": has_tracking_scans,
                "cost_gbp": cost_gbp,
                "region": "UK North" if postcode_area in ["M1", "L1"] else "UK South" if postcode_area in ["SW1", "SE1"] else "London",
                "updated_at": attempt_date,
            }

            delivery_attempts.append(attempt)

            # Generate tracking scans
            if has_tracking_scans > 0:
                for scan_num in range(1, has_tracking_scans + 1):
                    scan_time = attempt_date + __import__("datetime").timedelta(
                        hours=scan_num * 8,
                        minutes=g.rng.randint(0, 59)
                    )

                    events = [
                        "Picked up from depot",
                        "Out for delivery",
                        "Delivery attempted",
                        "Delivered",
                        "Left with neighbour",
                        "Left in safe place"
                    ]

                    scan = {
                        "attempt_id": attempt_id,
                        "scan_number": scan_num,
                        "scanned_at": scan_time,
                        "location": f"Hub {g.pick(['A', 'B', 'C', 'D', 'E'])}",
                        "event": g.pick(events),
                    }
                    delivery_scans.append(scan)

            # Generate address validation issues for failed attempts
            if status == "failed" and address_fail:
                issue = {
                    "issue_id": f"AVI-{issue_counter:06d}",
                    "order_id": order_id,
                    "postcode_area": postcode_area,
                    "issue_type": g.pick(["no_match", "partial_match", "invalid_postcode", "ambiguous"]),
                    "validation_timestamp": attempt_date,
                    "resolved": g.rng.random() < 0.6,
                }
                address_validation_issues.append(issue)
                issue_counter += 1

            # Generate complaints for some failed/damaged deliveries
            if complaint_raised and status == "delivered":
                complaint = {
                    "complaint_id": f"CMPLT-{complaint_counter:06d}",
                    "order_id": order_id,
                    "courier_id": courier_id,
                    "complaint_date": delivery_time or attempt_date,
                    "issue_type": "Damage" if damage_reported else "Late delivery" if delivery_time and delivery_time.date() > promised_delivery_date else "Other",
                    "resolved": g.rng.random() < 0.7,
                }
                delivery_complaints.append(complaint)
                complaint_counter += 1

    # Generate couriers
    couriers_data = []
    for i, courier in enumerate(parcel_couriers):
        courier_record = {
            "courier_id": courier.get("carrier_id", f"CAR-{i:03d}"),
            "name": courier.get("name", f"Courier {i}"),
            "mode": "parcel",
            "scope": "UK domestic",
            "region": g.pick(["London", "UK North", "UK South", "Midlands"]),
            "peak_capacity_units_month": g.rng.randint(50000, 200000),
            "rating": round(g.rng.uniform(3.5, 4.9), 1),
            "contract_end": g.as_of + __import__("datetime").timedelta(days=g.rng.randint(30, 365)),
        }
        couriers_data.append(courier_record)

    # Generate courier allocation rules
    allocation_rules = []
    for i in range(3):
        rule = {
            "rule_id": f"RULE-{i+1:06d}",
            "rule_name": f"Allocation rule {i+1}",
            "courier_id": g.pick([c["courier_id"] for c in couriers_data]),
            "postcode_areas": ",".join(g.pick(uk_postcode_areas, k=g.rng.randint(2, 4))),
            "volume_share_pct": round(g.rng.uniform(10.0, 50.0), 1),
            "region": g.pick(["London", "UK North", "UK South"]),
            "status": g.pick(["active", "trial", "archived"]),
            "created_at": g.as_of - __import__("datetime").timedelta(days=g.rng.randint(30, 180)),
            "updated_at": g.as_of - __import__("datetime").timedelta(days=g.rng.randint(0, 30)),
            "trial_end_date": g.as_of + __import__("datetime").timedelta(days=g.rng.randint(7, 42)) if g.rng.random() < 0.3 else None,
        }
        allocation_rules.append(rule)

    return {
        "delivery_attempts": delivery_attempts,
        "couriers": couriers_data,
        "courier_allocation_rules": allocation_rules,
        "delivery_scans": delivery_scans,
        "address_validation_issues": address_validation_issues,
        "delivery_complaints": delivery_complaints,
    }
