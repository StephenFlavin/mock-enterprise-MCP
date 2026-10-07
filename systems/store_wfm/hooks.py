"""Python tools for store workforce management calculations."""


def calc_labour_requirement(ctx, site_id, week_start, forecast_footfall, receiving_deliveries=2, promotional_events=0):
    """Calculate hourly labour requirement based on tasks and standards."""

    # Get labour standards
    standards = ctx.q(
        "SELECT task_category, standard_hours, unit_of_measure FROM labour_standards WHERE status = 'active'"
    )
    std_map = {s["task_category"]: s for s in standards}

    # Get current rota for this store and week
    rota = ctx.q(
        "SELECT rota_id, total_hours FROM staff_rotas WHERE site_id = $s AND week_start = CAST($w AS DATE) ORDER BY rota_id DESC LIMIT 1",
        s=site_id,
        w=week_start
    )

    current_hours = rota[0]["total_hours"] if rota else 0

    # Calculate requirements by task
    requirements = []
    total_required = 0

    # Receiving
    if "receiving" in std_map:
        receiving_hours = receiving_deliveries * std_map["receiving"]["standard_hours"]
        requirements.append(f"Receiving: {receiving_deliveries} deliveries × {std_map['receiving']['standard_hours']} hours = {receiving_hours} hours")
        total_required += receiving_hours

    # Shelf stocking based on footfall
    if "shelf" in std_map:
        # Assume 1000 units per 100 customers roughly
        shelf_hours = (forecast_footfall / 100) * std_map["shelf"]["standard_hours"]
        requirements.append(f"Shelf stocking: {forecast_footfall} footfall ÷ 100 × {std_map['shelf']['standard_hours']} = {shelf_hours:.1f} hours")
        total_required += shelf_hours

    # Promotional tasks
    if promotional_events > 0 and "relabel" in std_map:
        promo_hours = promotional_events * std_map["relabel"]["standard_hours"] * 2  # Double for promotion setup
        requirements.append(f"Promotional events: {promotional_events} events × {std_map['relabel']['standard_hours'] * 2} hours = {promo_hours} hours")
        total_required += promo_hours

    # Base checkout and customer service
    if "checkout" in std_map:
        checkout_hours = 8 * std_map["checkout"]["standard_hours"]  # 8 hours a day
        requirements.append(f"Checkout: 8 hours/day × {std_map['checkout']['standard_hours']} = {checkout_hours} hours")
        total_required += checkout_hours

    # Cleaning (2 hours per day)
    if "cleaning" in std_map:
        cleaning_hours = 7 * std_map["cleaning"]["standard_hours"] / 7  # Daily cleaning
        requirements.append(f"Cleaning: 7 days × {std_map['cleaning']['standard_hours'] / 7:.1f} hours/day = {cleaning_hours:.1f} hours")
        total_required += cleaning_hours

    gap = current_hours - total_required

    return {
        "site_id": site_id,
        "week_start": week_start,
        "forecast_footfall": forecast_footfall,
        "current_roasted_hours": round(current_hours, 1),
        "total_hours_required": round(total_required, 1),
        "gap_hours": round(gap, 1),
        "gap_status": "over-staffed" if gap > 2 else "under-staffed" if gap < -2 else "balanced",
        "requirements_breakdown": "; ".join(requirements),
        "formula": "total = receiving + shelf + checkout + cleaning + promotional"
    }
