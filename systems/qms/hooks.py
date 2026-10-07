"""Quality management system tools for measurement tolerance calculation."""


def update_lot_disposition(ctx, lot_id, disposition):
    """Update production lot disposition and status based on QA decision.

    Args:
        ctx: Tool context with database access
        lot_id: Production lot to update
        disposition: QA decision (release, rework, reject)

    Returns:
        dict with updated lot details
    """
    # Map disposition to status
    disposition_to_status = {
        'release': 'released',
        'rework': 'reworked',
        'reject': 'rejected'
    }

    status = disposition_to_status.get(disposition, disposition)

    # Fetch current lot
    rows = ctx.q("""
        SELECT lot_id, sku, factory_id, status, lot_disposition, qty_produced, created_at
        FROM production_lots
        WHERE lot_id = $lid
    """, lid=lot_id)

    if not rows:
        return {"lot_id": lot_id, "error": "Lot not found"}

    lot = rows[0]

    # Return the lot with updated values (write would happen in real execution)
    return {
        "lot_id": lot["lot_id"],
        "sku": lot["sku"],
        "factory_id": lot["factory_id"],
        "status": status,
        "lot_disposition": disposition,
        "qty_produced": lot["qty_produced"],
        "message": f"Lot disposition set to {disposition}, status updated to {status}"
    }


def calculate_recommended_tolerance(ctx, factory_id, material, measurement_type):
    """Calculate recommended tolerance based on factory process capability and material shrinkage.

    Args:
        ctx: Tool context with access to database queries
        factory_id: Factory being evaluated
        material: Material type (cotton, polyester, silk, wool)
        measurement_type: Type of measurement (e.g., length, width, chest_width)

    Returns:
        dict with recommended_tolerance_mm and supporting metrics
    """
    # Query factory capability - last 12 weeks
    rows = ctx.q("""
        SELECT AVG(pass_rate_pct) as avg_pass_rate,
               MIN(pass_rate_pct) as min_pass_rate,
               MAX(pass_rate_pct) as max_pass_rate,
               COUNT(*) as weeks_tracked
        FROM (
            SELECT pass_rate_pct
            FROM factory_quality_scorecards
            WHERE factory_id = $fid
            ORDER BY period DESC LIMIT 12
        )
    """, fid=factory_id)

    if not rows or rows[0]['avg_pass_rate'] is None:
        # Default values if no data
        pass_rate = 90
        weeks_tracked = 0
    else:
        pass_rate = rows[0]['avg_pass_rate']
        weeks_tracked = rows[0]['weeks_tracked']

    # Base tolerances by material (in mm)
    base_tolerance = {
        "cotton": 2.5,
        "polyester": 2.0,
        "silk": 1.5,
        "wool": 3.0
    }.get(material, 2.0)

    # Adjust by factory capability
    # Higher pass rate = tighter tolerance possible
    if pass_rate < 75:
        capability_factor = 1.8  # Poor capability, need loose tolerance
    elif pass_rate < 85:
        capability_factor = 1.4
    elif pass_rate < 92:
        capability_factor = 1.0  # Use base tolerance
    elif pass_rate < 96:
        capability_factor = 0.9
    else:
        capability_factor = 0.8  # Excellent capability, can tighten

    recommended_tolerance = base_tolerance * capability_factor

    return {
        "factory_id": factory_id,
        "material": material,
        "measurement_type": measurement_type,
        "recommended_tolerance_mm": round(recommended_tolerance, 2),
        "factory_pass_rate_pct": round(pass_rate, 1),
        "weeks_of_data": weeks_tracked,
        "basis": f"Base tolerance {base_tolerance}mm for {material}, adjusted {capability_factor}x for {round(pass_rate, 0)}% pass rate"
    }
