"""IMS background data: inventory positions, adjustments, cycle counts, shrink tracking, availability."""
from datetime import datetime, timedelta
import random


def generate(g):
    r = g.rng

    # Get master data
    skus = g.master("products")
    stores = [s for s in g.master("sites") if s["type"] in ("dc", "store")]
    locations = g.master("locations")  # DC bin locations

    # Initialize collections
    positions = []
    adjustments = []
    cycle_counts = []
    cycle_results = []
    reservations = []
    transfers = []
    release_plans = []
    shrink = []
    availability = []
    losses = []

    # Generate inventory positions for each SKU x site combination
    for sku_row in skus[:500]:  # Sample of SKUs for performance
        sku = sku_row["sku"]

        # Position at DCs and major stores
        for site in stores:
            site_id = site["site_id"]

            # Probability of having stock decreases for stores, higher for DCs
            has_stock = r.random() < (0.7 if site["type"] == "dc" else 0.4)

            if has_stock:
                on_hand = r.randint(10, 500) if site["type"] == "dc" else r.randint(0, 50)
                allocated = int(on_hand * r.uniform(0.1, 0.4))
                available = on_hand - allocated
                reserved = int(available * r.uniform(0, 0.2))
                hold_qty = r.randint(0, min(5, on_hand // 10))

                # For DCs, add location-level detail
                if site["type"] == "dc":
                    location_id = r.choice([l["location_id"] for l in locations if l["site_id"] == site_id]) if locations else None
                else:
                    location_id = None

                positions.append({
                    "sku": sku,
                    "site_id": site_id,
                    "location_id": location_id,
                    "on_hand": on_hand,
                    "allocated": allocated,
                    "available": available,
                    "reserved_for_channel": reserved,
                    "hold_qty": hold_qty,
                    "updated_at": g.fake.date_time_this_month(tzinfo=None),
                })

    # Generate adjustments (shrink, damage, variance)
    adj_id = 0
    for _ in range(200):
        adj_id += 1
        sku = r.choice(skus)["sku"]
        site = r.choice(stores)
        cause_choices = ["shrink", "damage", "receiving_variance", "cycle_count_variance", "picking_error"]

        adjustments.append({
            "adjustment_id": f"INV-ADJ-{adj_id:06d}",
            "sku": sku,
            "site_id": site["site_id"],
            "location_id": None,
            "quantity_delta": -r.randint(1, 20),
            "cause_code": r.choice(cause_choices),
            "reference_id": None,
            "status": r.choices(["pending", "posted"], [0.2, 0.8])[0],
            "user_id": f"EMP-{r.randint(1, 500):05d}",
            "reason_notes": "Variance found during count" if r.random() < 0.5 else "",
            "value_impact_gbp": -r.uniform(10, 500),
            "created_at": g.days_ago(r.randint(0, 60)),
            "posted_at": g.days_ago(r.randint(0, 60)) if r.random() < 0.8 else None,
            "updated_at": g.days_ago(r.randint(0, 30)),
        })

    # Generate cycle count tasks
    cc_id = 0
    for _ in range(20):
        cc_id += 1
        site = r.choice(stores)
        cycle_counts.append({
            "cycle_count_id": f"CC-{cc_id:06d}",
            "site_id": site["site_id"],
            "category": r.choice(["Dresses", "Bedding", "Home", None]),
            "location_id": r.choice([l["location_id"] for l in locations if l["site_id"] == site["site_id"]]) if site["type"] == "dc" and locations else None,
            "scheduled_date": g.days_ago(-r.randint(0, 30)),
            "status": r.choices(["scheduled", "completed"], [0.3, 0.7])[0],
            "reason": "Regular inventory check",
            "counted_by": f"EMP-{r.randint(1, 500):05d}" if r.random() < 0.7 else None,
            "counted_at": g.days_ago(r.randint(0, 30)) if r.random() < 0.7 else None,
            "result_summary": "Minor variances found" if r.random() < 0.5 else None,
            "created_at": g.days_ago(r.randint(5, 60)),
        })

    # Generate cycle count results (for completed counts)
    for cc in cycle_counts:
        if cc["status"] == "completed" and r.random() < 0.7:
            for _ in range(r.randint(3, 10)):
                cycle_results.append({
                    "cycle_count_id": cc["cycle_count_id"],
                    "sku": r.choice(skus)["sku"],
                    "location_id": cc["location_id"] or f"{cc['site_id']}-A-01-01",
                    "system_qty": r.randint(0, 100),
                    "counted_qty": r.randint(0, 100),
                    "variance": r.randint(-10, 10),
                    "variance_pct": r.uniform(-5, 5),
                })

    # Generate stock reservations (for channels)
    res_id = 0
    for _ in range(30):
        res_id += 1
        reservations.append({
            "reservation_id": f"RESV-{res_id:06d}",
            "sku": r.choice(skus)["sku"],
            "site_id": r.choice(stores)["site_id"],
            "channel": r.choice(["click_collect", "online", "promotion"]),
            "quantity": r.randint(5, 50),
            "status": r.choices(["active", "released"], [0.6, 0.4])[0],
            "expiry_date": g.days_ago(-r.randint(0, 30)),
            "reference_id": None,
            "created_at": g.days_ago(r.randint(0, 30)),
            "released_at": g.days_ago(r.randint(0, 30)) if r.random() < 0.4 else None,
        })

    # Generate store transfers
    tr_id = 0
    for _ in range(20):
        tr_id += 1
        from_site = r.choice(stores)
        to_site = r.choice([s for s in stores if s["site_id"] != from_site["site_id"]])
        transfers.append({
            "transfer_id": f"STR-{tr_id:06d}",
            "sku": r.choice(skus)["sku"],
            "from_site_id": from_site["site_id"],
            "to_site_id": to_site["site_id"],
            "quantity": r.randint(10, 100),
            "quantity_shipped": r.randint(0, 100),
            "reason": "Rebalance",
            "status": r.choices(["requested", "approved", "shipped"], [0.2, 0.4, 0.4])[0],
            "requested_by": f"EMP-{r.randint(1, 500):05d}",
            "requested_date": g.days_ago(r.randint(0, 30)),
            "shipped_date": g.days_ago(r.randint(0, 30)) if r.random() < 0.6 else None,
            "received_date": g.days_ago(r.randint(0, 30)) if r.random() < 0.3 else None,
        })

    # Generate release plans
    sp_id = 0
    for _ in range(10):
        sp_id += 1
        release_plans.append({
            "plan_id": f"SRP-{sp_id:06d}",
            "site_id": r.choice(stores)["site_id"],
            "category": r.choice(["Dresses", "Bedding", "Home"]),
            "planned_release_date": g.days_ago(-r.randint(0, 30)),
            "status": r.choices(["draft", "approved", "completed"], [0.2, 0.4, 0.4])[0],
            "description": "Clear seasonal overstock",
            "estimated_units": r.randint(50, 500),
            "actual_units_released": r.randint(0, 500),
            "created_by": f"EMP-{r.randint(1, 500):05d}",
            "created_at": g.days_ago(r.randint(5, 60)),
        })

    # Generate shrink analysis (by week and category)
    for store in stores[:50]:
        for week_offset in range(0, 12):
            week_start = g.days_ago(7 * week_offset)
            for category in ["Dresses", "Bedding", "Home"]:
                shrink.append({
                    "site_id": store["site_id"],
                    "category": category,
                    "analysis_week": week_start,
                    "shrink_units": r.randint(0, 20),
                    "shrink_value_gbp": r.uniform(0, 1000),
                    "shrink_rate_pct": r.uniform(0, 2),
                    "vs_peer_avg_pct": r.uniform(-0.5, 0.5),
                    "main_cause": r.choice(["receiving error", "picking error", "theft"]),
                })

    # Generate availability tracking (weekly by SKU and store)
    weeks = g.weeks(12)
    for tracking_date in weeks:
        for sku_row in r.sample(skus, min(50, len(skus))):
            for store in r.sample(stores, min(20, len(stores))):
                availability.append({
                    "sku": sku_row["sku"],
                    "site_id": store["site_id"],
                    "tracking_date": tracking_date,
                    "available": r.random() < 0.7,
                    "quantity_available": r.randint(0, 50),
                    "demand_units": r.randint(0, 20),
                    "lost_sales": r.randint(0, 5) if r.random() < 0.2 else 0,
                    "forecast_available": r.random() < 0.75,
                })

    # Generate lost products (damage, expiry, etc)
    loss_id = 0
    for _ in range(50):
        loss_id += 1
        losses.append({
            "loss_id": f"LOSS-{loss_id:06d}",
            "sku": r.choice(skus)["sku"],
            "site_id": r.choice(stores)["site_id"],
            "loss_type": r.choice(["damage", "expiry", "shrink", "unknown"]),
            "quantity": r.randint(1, 30),
            "value_gbp": r.uniform(10, 500),
            "identified_date": g.days_ago(r.randint(0, 90)),
            "batch_or_serial": None,
            "notes": "Inventory loss",
        })

    return {
        "inventory_positions": positions,
        "inventory_adjustments": adjustments,
        "cycle_count_tasks": cycle_counts,
        "cycle_count_results": cycle_results,
        "stock_reservations": reservations,
        "store_transfers": transfers,
        "stock_release_plans": release_plans,
        "shrink_analysis": shrink,
        "availability_tracking": availability,
        "lost_products": losses,
    }
