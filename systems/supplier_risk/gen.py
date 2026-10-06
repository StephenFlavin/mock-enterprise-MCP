"""Supplier risk data: profiles, alerts, certifications, compliance, credit, insurance, onboarding."""
from datetime import datetime, timedelta


def generate(g):
    r = g.rng
    suppliers = g.master("suppliers")
    factories = g.master("factories")
    products = g.master("products")

    # Tables
    profiles, alerts, certs, insurance, bank_details, compliance, credit, cyber, filings, security, factories_p = [], [], [], [], [], [], [], [], [], [], []
    onboarding_cases, controls, items, alt_suppliers, alt_factories = [], [], [], [], []

    # Generate supplier profiles
    for sup in suppliers:
        if sup["status"] != "active":
            continue
        profiles.append({
            "supplier_id": sup["supplier_id"],
            "criticality_rating": r.choices(["low", "medium", "high", "critical"], [40, 35, 20, 5])[0],
            "financial_health_score": max(0, min(100, r.gauss(65, 20))),
            "security_risk_rating": r.choices(["low", "medium", "high", "critical"], [50, 30, 15, 5])[0],
            "last_assessed_at": g.days_ago(r.randint(0, 90)),
            "watch_status": "none",
        })

    # Generate supplier risk alerts for some suppliers
    alert_id = 0
    for sup in suppliers:
        if r.random() > 0.3 or sup["status"] != "active":
            continue
        for _ in range(r.randint(0, 2)):
            alert_id += 1
            alerts.append({
                "alert_id": f"SRA-{alert_id:06d}",
                "supplier_id": sup["supplier_id"],
                "factory_id": None,
                "alert_type": r.choice(["financial", "compliance", "quality", "delivery", "security", "regulatory"]),
                "severity": r.choices(["low", "medium", "high", "critical"], [30, 40, 20, 10])[0],
                "description": g.fake.sentence(),
                "raised_at": g.days_ago(r.randint(0, 60)),
                "status": r.choices(["active", "resolved"], [70, 30])[0],
            })

    # Generate certifications for suppliers
    cert_types = ["ISO-9001", "ISO-14001", "OEKO-TEX", "BSCI", "SA8000", "FSC", "Sedex"]
    for sup in suppliers[:len(suppliers)//2]:
        for cert in r.sample(cert_types, k=r.randint(1, 3)):
            issue_date = g.days_ago(r.randint(180, 730))
            certs.append({
                "supplier_id": sup["supplier_id"],
                "cert_type": cert,
                "issuer": g.fake.company(),
                "issue_date": issue_date,
                "expiry_date": issue_date + timedelta(days=730),
                "scope": "All products" if r.random() > 0.5 else "Selected certifications",
                "status": "current",
            })

    # Generate insurance records
    policy_types = ["General Liability", "Product Liability", "Professional Indemnity", "Cyber", "Directors & Officers"]
    for sup in suppliers:
        for pol in r.sample(policy_types, k=r.randint(1, 2)):
            issue_date = g.days_ago(r.randint(30, 365))
            insurance.append({
                "supplier_id": sup["supplier_id"],
                "policy_type": pol,
                "provider": g.fake.company(),
                "policy_number": g.fake.bothify("POL-######"),
                "coverage_gbp": r.choice([1_000_000, 5_000_000, 10_000_000]),
                "issue_date": issue_date,
                "expiry_date": issue_date + timedelta(days=365),
                "status": "current",
            })

    # Generate bank details
    for sup in suppliers:
        bank_details.append({
            "supplier_id": sup["supplier_id"],
            "bank_name": g.fake.bank(),
            "account_holder": sup["name"],
            "account_number": g.fake.bothify("##-##-######"),
            "sort_code": g.fake.bothify("##-##-##"),
            "country": sup["country"],
            "currency": sup["currency"],
            "verified": r.random() > 0.2,
            "last_verified_at": g.days_ago(r.randint(0, 180)) if r.random() > 0.1 else None,
        })

    # Generate compliance records
    compliance_areas = ["labour", "environmental", "safety", "data_protection", "tax_compliance"]
    for sup in suppliers:
        for _ in range(r.randint(2, 5)):
            compliance.append({
                "supplier_id": sup["supplier_id"],
                "record_date": g.days_ago(r.randint(0, 365)),
                "compliance_area": r.choice(compliance_areas),
                "finding": "No issues found" if r.random() > 0.2 else g.fake.sentence(),
                "status": r.choices(["compliant", "non_compliant", "exception"], [80, 10, 10])[0],
            })

    # Generate credit data (latest only for now)
    for sup in suppliers:
        credit.append({
            "supplier_id": sup["supplier_id"],
            "rating_date": g.days_ago(r.randint(0, 30)),
            "credit_rating": r.choices(["A_excellent", "B_good", "C_fair", "D_poor", "E_very_poor"], [30, 40, 20, 7, 3])[0],
            "credit_score": r.randint(400, 900),
            "days_payable_outstanding": r.randint(30, 120),
            "payment_default_count": r.choices([0, 1, 2, 3], [85, 10, 3, 2])[0],
        })

    # Generate cyber security ratings
    for sup in suppliers[::2]:
        cyber.append({
            "supplier_id": sup["supplier_id"],
            "assessment_date": g.days_ago(r.randint(0, 180)),
            "rating": r.choices(["excellent", "good", "fair", "poor"], [20, 40, 30, 10])[0],
            "assessment_source": r.choice(["Recorded Future", "SecurityScorecard", "Rapid7", "BitSight"]),
            "findings": g.fake.sentence(),
        })

    # Generate financial filings
    for sup in suppliers:
        spend = float(sup["annual_spend_gbp"]) if sup["annual_spend_gbp"] else 0
        if spend and spend > 100000:
            for years_ago in range(1, 3):
                filing_date = g.days_ago(365 * years_ago)
                filings.append({
                    "supplier_id": sup["supplier_id"],
                    "filing_date": filing_date,
                    "filing_type": "annual accounts",
                    "revenue_gbp": spend * r.uniform(0.8, 1.2),
                    "profit_gbp": spend * r.uniform(0.05, 0.15),
                    "cash_gbp": spend * r.uniform(0.1, 0.4),
                    "debt_gbp": spend * r.uniform(0.2, 0.6),
                    "roe_pct": r.uniform(5, 30),
                    "debt_to_equity": r.uniform(0.5, 2.0),
                    "current_ratio": r.uniform(1.0, 3.0),
                })

    # Generate security risk records
    for sup in suppliers[::3]:
        security.append({
            "supplier_id": sup["supplier_id"],
            "assessment_date": g.days_ago(r.randint(0, 180)),
            "rating": r.choices(["low", "medium", "high", "critical"], [50, 30, 15, 5])[0],
            "system_access": r.random() > 0.7,
            "access_level": r.choice(["read_only", "order_placement", "inventory", "financial"]) if r.random() > 0.7 else None,
        })

    # Generate factory profiles
    for fac in factories:
        factories_p.append({
            "factory_id": fac["factory_id"],
            "risk_rating": r.choices(["low", "medium", "high", "critical"], [50, 30, 15, 5])[0],
            "last_assessed_at": g.days_ago(r.randint(0, 180)),
        })

    # Generate onboarding cases for some suppliers
    case_id = 0
    for sup in suppliers[len(suppliers)//2:]:
        if r.random() > 0.4:
            case_id += 1
            onboarding_cases.append({
                "case_id": f"SOC-{case_id:06d}",
                "supplier_id": sup["supplier_id"],
                "status": r.choices(["draft", "in_progress", "approved", "conditional", "rejected", "completed"], [10, 30, 30, 15, 10, 5])[0],
                "risk_rating": r.choices(["low", "medium", "high", "critical"], [40, 40, 15, 5])[0],
                "conditions": "Audit required; OEKO-TEX certification needed" if r.random() > 0.7 else None,
                "created_at": g.days_ago(r.randint(0, 180)),
                "updated_at": g.days_ago(r.randint(0, 90)),
                "completed_at": g.days_ago(r.randint(0, 60)) if r.random() > 0.5 else None,
            })

    # Generate onboarding controls
    for i, desc in enumerate(["Verify company registration", "Check sanctions list", "Run credit check",
                               "Review financial statements", "Confirm certifications", "Assess compliance"], 1):
        controls.append({
            "control_id": f"SOC-CTL-{i:03d}",
            "description": desc,
            "control_type": r.choice(["document review", "sanctions screening", "financial check", "certification check"]),
            "sequence": i,
        })

    # Generate onboarding items for cases
    item_id = 0
    for case in onboarding_cases:
        for control in controls[:r.randint(2, 5)]:
            item_id += 1
            items.append({
                "case_id": case["case_id"],
                "item_id": str(item_id),
                "control_id": control["control_id"],
                "description": control["description"],
                "status": r.choices(["required", "submitted", "approved", "rejected"], [20, 30, 40, 10])[0],
                "due_date": g.days_ago(-r.randint(1, 60)),
                "submitted_at": g.days_ago(r.randint(0, 30)) if r.random() > 0.3 else None,
            })

    # Generate alternative suppliers
    categories = ["Cookware", "Fabrics", "Packaging", "Electronics", "Leather"]
    for cat in categories:
        for sup in r.sample(suppliers, k=min(3, len(suppliers))):
            alt_suppliers.append({
                "category": cat,
                "supplier_id": sup["supplier_id"],
                "tier": r.choices(["primary", "secondary", "tertiary"], [40, 35, 25])[0],
                "capability": r.choice(["seam-sealing", "OEKO-TEX", "large_batch", "fast_turnaround", "custom_design"]),
            })

    # Generate alternative factories
    for prod in products[:len(products)//3]:
        for fac in r.sample(factories, k=r.randint(1, 2)):
            alt_factories.append({
                "sku": prod["sku"],
                "factory_id": fac["factory_id"],
                "approved": r.random() > 0.3,
                "qualification_status": r.choices(["approved", "in_progress", "pending", "failed"], [60, 20, 15, 5])[0],
            })

    return {
        "supplier_profiles": profiles,
        "supplier_risk_alerts": alerts,
        "supplier_certifications": certs,
        "supplier_insurance": insurance,
        "supplier_bank_details": bank_details,
        "supplier_compliance_records": compliance,
        "supplier_credit_data": credit,
        "supplier_cyber_security": cyber,
        "supplier_financial_filings": filings,
        "supplier_security_risk": security,
        "factory_profiles": factories_p,
        "onboarding_cases": onboarding_cases,
        "onboarding_controls": controls,
        "onboarding_items": items,
        "alternative_suppliers": alt_suppliers,
        "alternative_factories": alt_factories,
    }
