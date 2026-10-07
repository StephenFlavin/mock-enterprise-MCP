"""EPR and packaging compliance background data.

All story countries (GB, DE, FR, NL, ES, IT) and every SKU/target/assessment row come from seed/*.csv so that tools
return clean answers for those scopes. The generator only adds a little background for Belgium, which no question uses.
"""
from datetime import timedelta


def generate(g):
    r = g.rng
    out = {t: [] for t in ["packaging_targets", "epr_registrations", "epr_reporting_obligations", "epr_fee_schedules",
                           "packaging_regulations", "recyclability_assessments", "recycled_content_data",
                           "recycling_label_rules", "epr_preparation_tasks", "packaging_cost_factors",
                           "packaging_catch_up_options"]}

    out["epr_registrations"].append({
        "registration_id": "REG-000001", "country": "BE", "scheme_name": "Fost Plus (Belgium)",
        "registration_number": "BE-FP-2023-017", "status": "active",
        "registration_date": g.date_between(730, 365), "category": "packaging"})

    for i, category in enumerate(["packaging", "textiles"]):
        out["epr_reporting_obligations"].append({
            "obligation_id": f"OBL-{i + 1:06d}", "country": "BE", "category": category,
            "data_required": "Volume by material; Disposal route data",
            "deadline": g.as_of + timedelta(days=r.randint(120, 330)), "frequency": "annual",
            "penalty_gbp": r.choice([15000, 30000])})

    for i, (material, fee) in enumerate([("plastic", 430), ("corrugated", 105), ("moulded_pulp", 160)]):
        out["epr_fee_schedules"].append({
            "schedule_id": f"SCH-{i + 1:06d}", "country": "BE", "scheme_name": "Fost Plus (Belgium)",
            "category": "packaging", "material": material, "fee_per_tonne_gbp": fee,
            "effective_from": g.as_of - timedelta(days=r.randint(90, 300)), "effective_to": None})

    out["packaging_regulations"].append({
        "regulation_id": "REG-000001", "country": "BE", "regulation_name": "Belgian Packaging EPR Agreement",
        "requirement": "Packaging EPR through Fost Plus", "recycled_content_mandate_pct": None,
        "plastic_tax_pct": 0, "effective_from": g.as_of - timedelta(days=900), "effective_to": None,
        "penalty_gbp": 40000})

    for i, category in enumerate(["cosmetics", "home"]):
        out["recycling_label_rules"].append({
            "rule_id": f"LBL-{i + 1:06d}", "country": "BE", "product_category": category,
            "requirement": "Recycling marks and sorting instructions in Dutch or French",
            "legal_marks": "Sorting icons per component",
            "warnings": None, "material_markings_required": True, "disposal_instructions_required": True,
            "language_requirements": "Dutch and French mandatory", "often_missed": None, "penalty_gbp": 12000,
            "effective_from": g.as_of - timedelta(days=500)})

    out["packaging_cost_factors"].append({
        "factor_id": "FCT-000001", "material": "plastic", "country": "BE", "packaging_tax_rate_pct": 0,
        "epr_contribution_pct": 2.6, "regulatory_cost_per_unit_gbp": 0.48,
        "effective_from": g.as_of - timedelta(days=400)})
    return out
