"""ESG data: emissions by scope, factors, targets, initiatives, data gaps, supplier submissions."""
from datetime import datetime, timedelta, date


def generate(g):
    r = g.rng
    suppliers = g.master("suppliers")[:50]
    products = g.master("products")[:100]
    sites = g.master("sites")

    emissions = []
    emission_factors = []
    reduction_targets = []
    reduction_initiatives = []
    esg_data_gaps = []
    supplier_submissions = []
    claims_register = []
    data_requests = []
    scope2_history = []
    transport_factors = []
    regulations = []

    # Emission factors library
    ef_materials = ["cotton", "polyester", "recycled_polyester", "nylon", "wool"]
    ef_transport_modes = ["air", "sea", "truck", "rail"]
    ef_quality = ["A", "B", "C", "D"]
    ef_sources = ["DEFRA", "ICAO", "IPCC", "supplier_data"]

    for i in range(20):
        for material in ef_materials:
            factor_id = f"EF-2026-{i * 100 + len(emission_factors) + 1:04d}"
            emission_factors.append({
                "factor_id": factor_id,
                "factor_name": f"{material.replace('_', ' ').title()} production 2026",
                "material": material,
                "transport_mode": None,
                "kg_co2e_per_unit": round(r.gauss(2.0, 0.5), 2),
                "unit": "kg",
                "source": r.choice(ef_sources),
                "version": r.randint(1, 3),
                "data_quality_rating": r.choice(ef_quality),
                "valid_from": g.as_of - timedelta(days=90),
                "valid_to": g.as_of + timedelta(days=270),
                "region": r.choice(["UK", "EU", "Asia"])
            })

    # Transport emission factors
    routes = [
        ("UK", "Europe", "truck"),
        ("UK", "China", "sea"),
        ("UK", "China", "air"),
        ("Europe", "Asia", "sea"),
        ("Europe", "Asia", "air")
    ]

    for origin, dest, mode in routes:
        for v in range(1, 4):
            factor = {
                "lane_id": f"{origin}-{dest}-{mode}",
                "period_start": g.as_of - timedelta(days=(4-v)*90),
                "transport_mode": mode,
                "origin": origin,
                "destination": dest,
                "factor_kg_per_tonne_km": round(
                    {"air": 0.12, "sea": 0.008, "truck": 0.08, "rail": 0.025}[mode] * r.gauss(1, 0.1), 5
                ),
                "factor_source": r.choice(["ICAO", "DEFRA", "carbon_trust"]),
                "version": v,
                "status": "active" if v == 3 else "superseded"
            }
            transport_factors.append(factor)

    # Emissions data - scope 1, 2, 3
    emission_id_counter = 1

    # Scope 1 (Direct)
    for site in sites[:3]:
        for month in range(-12, 1):
            month_date = g.as_of + timedelta(days=month*30)
            emissions.append({
                "emission_id": f"EMS-{emission_id_counter:06d}",
                "scope": "1",
                "category": "fleet",
                "sku": None,
                "supplier_id": None,
                "tonnes_co2e": round(r.gauss(50, 10), 2),
                "is_measured": True,
                "measurement_date": month_date,
                "emission_factor_id": None,
                "notes": "Fleet fuel consumption",
                "updated_at": g.as_of
            })
            emission_id_counter += 1

    # Scope 2 (Electricity)
    for site in sites[:5]:
        for month in range(-12, 1):
            month_date = g.as_of + timedelta(days=month*30)
            ef = emission_factors[r.randint(0, len(emission_factors)-1)]
            emissions.append({
                "emission_id": f"EMS-{emission_id_counter:06d}",
                "scope": "2",
                "category": "purchased_electricity",
                "sku": None,
                "supplier_id": None,
                "tonnes_co2e": round(r.gauss(200, 50), 2),
                "is_measured": True,
                "measurement_date": month_date,
                "emission_factor_id": ef["factor_id"],
                "notes": f"Electricity at {site['site_id']}",
                "updated_at": g.as_of
            })
            emission_id_counter += 1

    # Scope 3 by supplier
    for supplier in suppliers:
        for sku in r.sample([p["sku"] for p in products], min(5, len(products))):
            for month in range(-12, 1):
                month_date = g.as_of + timedelta(days=month*30)
                is_measured = r.random() > 0.6
                ef = emission_factors[r.randint(0, len(emission_factors)-1)]
                emissions.append({
                    "emission_id": f"EMS-{emission_id_counter:06d}",
                    "scope": "3",
                    "category": r.choice(["materials", "transport", "processing"]),
                    "sku": sku,
                    "supplier_id": supplier["supplier_id"],
                    "tonnes_co2e": round(r.gauss(100, 30), 2),
                    "is_measured": is_measured,
                    "measurement_date": month_date,
                    "emission_factor_id": ef["factor_id"],
                    "notes": "Scope 3 from supplier" if is_measured else "Estimated based on spend",
                    "updated_at": g.as_of
                })
                emission_id_counter += 1

    # Reduction targets
    for scope_num in [1, 2, 3]:
        targets_count = r.randint(2, 4)
        for t in range(targets_count):
            target_id = f"TRG-{len(reduction_targets) + 1:06d}"
            reduction_targets.append({
                "target_id": target_id,
                "scope": str(scope_num),
                "baseline_year": 2020,
                "baseline_tonnes_co2e": round(r.gauss(5000, 1000), 2),
                "target_year": 2025 + scope_num,
                "target_tonnes_co2e": round(r.gauss(3000, 800), 2),
                "reduction_pct": round(r.gauss(40, 10), 1),
                "pathway": r.choice(["SBTi 1.5C", "Paris Aligned", "Net Zero 2040"]),
                "status": r.choice(["active", "achieved", "paused"])
            })

    # Reduction initiatives
    initiative_categories = ["renewable_energy", "recycled_materials", "logistics", "supplier_engagement", "energy_efficiency"]
    for i in range(15):
        initiative_id = f"INI-2026-{i + 1:04d}"
        scope = str(r.choice([1, 2, 3]))
        reduction_initiatives.append({
            "initiative_id": initiative_id,
            "name": f"Initiative {i+1}: {r.choice(initiative_categories)}",
            "description": f"Reduction initiative focused on {r.choice(initiative_categories).replace('_', ' ')}",
            "scope": scope,
            "category": r.choice(initiative_categories),
            "expected_savings_tonnes": round(r.gauss(500, 200), 2),
            "cost_gbp": round(r.gauss(100000, 50000), 2),
            "start_date": g.as_of + timedelta(days=r.randint(0, 180)),
            "completion_date": g.as_of + timedelta(days=r.randint(180, 365)),
            "status": r.choice(["planned", "in_progress", "completed"]),
            "feasibility_rating": r.choice(["high", "medium", "low"]),
            "actual_savings_tonnes": None,
            "created_at": g.as_of,
            "updated_at": g.as_of
        })

    # ESG data gaps
    metrics = ["Scope1_completeness", "Scope2_supplier_data", "Scope3_supplier_emissions", "Product_footprints", "Energy_efficiency_data"]
    for m in metrics:
        gap_id = f"GAP-{len(esg_data_gaps) + 1:06d}"
        esg_data_gaps.append({
            "gap_id": gap_id,
            "metric": m,
            "description": f"Missing or incomplete {m.lower()} data",
            "materiality_score": round(r.gauss(70, 20), 1),
            "regulatory_impact": r.choice(["high", "medium", "low"]),
            "coverage_pct": round(r.gauss(60, 25), 1),
            "effort_to_close": r.choice(["easy", "medium", "hard"]),
            "priority": r.choice(["critical", "high", "medium", "low"]),
            "identified_date": g.as_of - timedelta(days=r.randint(30, 180)),
            "target_close_date": g.as_of + timedelta(days=r.randint(30, 180)),
            "status": r.choice(["open", "in_progress"])
        })

    # Supplier submissions
    for supplier in suppliers[:20]:
        submission_id = f"SUB-{len(supplier_submissions) + 1:06d}"
        deadline = g.as_of + timedelta(days=r.randint(7, 60))
        submitted = r.random() > 0.3
        supplier_submissions.append({
            "submission_id": submission_id,
            "supplier_id": supplier["supplier_id"],
            "submission_date": deadline - timedelta(days=r.randint(0, 15)) if submitted else None,
            "deadline_date": deadline,
            "data_quality_score": r.randint(40, 95) if submitted else 0,
            "completeness_pct": round(r.gauss(70, 25), 1) if submitted else 0,
            "has_scope1": r.random() > 0.4,
            "has_scope2": r.random() > 0.2,
            "has_scope3": r.random() > 0.6,
            "status": r.choice(["received", "under_review", "approved"]) if submitted else "pending",
            "notes": "Quality issues" if not submitted else "Data received",
            "updated_at": g.as_of
        })

    # Sustainability claims
    claims_text = [
        "Made from 100% recycled materials",
        "Carbon neutral shipping",
        "Organic cotton sourced",
        "Sustainable production certified",
        "Fair trade partner",
        "Plastic-free packaging",
        "Zero waste manufacturing"
    ]

    for i, claim in enumerate(claims_text):
        claim_id = f"CLM-2026-{i + 1:04d}"
        claims_register.append({
            "claim_id": claim_id,
            "claim_text": claim,
            "product_category": r.choice(["apparel", "footwear", "accessories"]),
            "risk_level": r.choice(["high", "medium", "low"]),
            "substantiation_available": r.random() > 0.4,
            "evidence_path": f"files/claim_{i+1}_evidence.pdf" if r.random() > 0.5 else None,
            "review_status": r.choice(["pending", "approved", "amend"]),
            "reviewed_by": None,
            "reviewed_date": None,
            "notes": "Under review" if r.random() > 0.5 else "",
            "created_at": g.as_of - timedelta(days=r.randint(30, 180))
        })

    # Data requests to suppliers
    for supplier in suppliers[:15]:
        request_id = f"REQ-{len(data_requests) + 1:06d}"
        deadline = g.as_of + timedelta(days=r.randint(14, 60))
        data_requests.append({
            "request_id": request_id,
            "supplier_id": supplier["supplier_id"],
            "request_date": g.as_of - timedelta(days=r.randint(0, 30)),
            "deadline_date": deadline,
            "scopes_requested": ",".join([str(s) for s in r.sample([1, 2, 3], r.randint(1, 3))]),
            "status": r.choice(["sent", "received", "overdue", "cancelled"]),
            "notes": "Quarterly ESG data request",
            "sent_at": g.as_of - timedelta(days=r.randint(0, 30))
        })

    # Scope 2 history (year-over-year)
    for site in sites[:3]:
        for year in range(2020, 2027):
            s2_id = (year, site["site_id"])
            scope2_history.append({
                "year": year,
                "site_id": site["site_id"],
                "kwh_consumed": round(r.gauss(500000, 100000), 0),
                "emissions_tonnes_co2e": round(r.gauss(150, 30), 2),
                "factor_kg_per_kwh": round(r.gauss(0.20, 0.05), 3),
                "factor_source": "UK Grid DEFRA",
                "method": r.choice(["location_based", "market_based"]),
                "boundary": "fully_owned",
                "updated_at": g.as_of
            })

    # Regulations
    regulations_list = [
        ("REG-UK-TCFD", "TCFD Disclosure", "UK", "carbon_disclosure", "Mandatory from 2025 for large companies"),
        ("REG-EU-CSRD", "Corporate Sustainability Reporting", "EU", "carbon_disclosure", "Applies to large EU companies"),
        ("REG-UK-FCA", "FCA Climate Disclosures", "UK", "climate_risk", "Financial Conduct Authority rules"),
        ("REG-GLOBAL-SBTi", "Science Based Targets", "global", "emissions_reduction", "Voluntary science-based commitment")
    ]

    for reg_id, name, jurisdiction, req_type, desc in regulations_list:
        regulations.append({
            "regulation_id": reg_id,
            "name": name,
            "jurisdiction": jurisdiction,
            "requirement_type": req_type,
            "description": desc,
            "applies_to_us": r.random() > 0.3,
            "effective_date": g.as_of + timedelta(days=r.randint(90, 730)),
            "scopes_covered": "1,2,3",
            "data_required": "Emissions by scope, reduction targets, governance",
            "url": "https://example.com/regulation"
        })

    return {
        "emissions": emissions,
        "emission_factors": emission_factors,
        "reduction_targets": reduction_targets,
        "reduction_initiatives": reduction_initiatives,
        "esg_data_gaps": esg_data_gaps,
        "supplier_submissions": supplier_submissions,
        "claims_register": claims_register,
        "data_requests": data_requests,
        "scope2_history": scope2_history,
        "transport_factors": transport_factors,
        "regulations": regulations
    }
