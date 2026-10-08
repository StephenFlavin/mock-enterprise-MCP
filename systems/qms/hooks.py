"""Quality management system tools for measurement tolerance calculation."""


def calculate_recommended_tolerance(ctx, factory_id, material, measurement_type, construction=None):
    """Calculate recommended tolerance based on factory process capability and material shrinkage.

    Args:
        ctx: Tool context with access to database queries
        factory_id: Factory being evaluated
        material: Material type (cotton, polyester, silk, wool)
        measurement_type: Type of measurement (e.g., shrinkage, length, width, chest_width)
        construction: Optional fabric construction (knit, woven)

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

    # Adjust by factory capability: higher pass rate = tighter tolerance possible
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

    # Shrinkage / dimensional change: start from the industry standard for the material and construction
    topic = "shrinkage" if measurement_type.lower() in ("shrinkage", "length", "width", "dimensional_change") else None
    std = []
    if topic:
        std = ctx.q("""
            SELECT standard_id, reference, tolerance_pct, construction FROM tolerance_standards
            WHERE topic = $t AND source_type = 'industry' AND tolerance_pct IS NOT NULL
              AND lower(material) IN ($m, 'all') AND ($c IS NULL OR lower(construction) IN ($c, 'all'))
            ORDER BY CASE WHEN lower(material) = $m THEN 0 ELSE 1 END,
                     CASE WHEN $c IS NOT NULL AND lower(construction) = $c THEN 0 ELSE 1 END, tolerance_pct
            LIMIT 1
        """, t=topic, m=material.lower(), c=construction.lower() if construction else None)
    if std:
        industry = float(std[0]["tolerance_pct"])
        capability_pct = round(industry * capability_factor, 2)
        tighter = min(industry, capability_pct)
        return {
            "factory_id": factory_id,
            "material": material,
            "construction": std[0]["construction"],
            "measurement_type": measurement_type,
            "industry_standard_pct": industry,
            "industry_standard_ref": f'{std[0]["standard_id"]} {std[0]["reference"]}',
            "capability_adjusted_pct": capability_pct,
            "recommended_tolerance_pct": tighter,
            "factory_pass_rate_pct": round(pass_rate, 1),
            "weeks_of_data": weeks_tracked,
            "basis": f"Industry standard +/-{industry}% for {material} {std[0]['construction']}; factory capability ({round(pass_rate, 0)}% pass rate) "
                     f"implies +/-{capability_pct}% ({capability_factor}x); the tighter figure, +/-{tighter}%, is recommended",
        }

    # Other measurements: base tolerances by material (in mm), scaled by capability
    base_tolerance = {
        "cotton": 2.5,
        "polyester": 2.0,
        "silk": 1.5,
        "wool": 3.0
    }.get(material, 2.0)

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
