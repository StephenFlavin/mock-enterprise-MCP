"""Tax & Duty system: duty rates by HS code and origin, import entries, VAT returns, transfer pricing."""
from datetime import datetime, timedelta


def generate(g):
    r = g.rng

    # Duty rates for common HS codes and origins into UK/EU/US
    duty_rates = []
    hs_codes = ['6110', '6111', '6114', '62046827', '62095473', '85165829', '85163623', '63026131', '63029990']
    origins = ['VN', 'CN', 'BD', 'TR', 'PL', 'PT', 'IT', 'FR', 'DE', 'IN']
    destinations = ['UK', 'EU', 'US']

    rate_map = {
        ('6110', 'VN', 'UK'): (10, 20, 8, 'CPTPP'),
        ('6110', 'VN', 'EU'): (10, 21, 10, 'GSP+'),
        ('6110', 'VN', 'US'): (15, 0, 0, None),
        ('6110', 'CN', 'UK'): (15, 20, 0, None),
        ('6110', 'CN', 'EU'): (15, 21, 0, None),
        ('6110', 'CN', 'US'): (25, 0, 0, None),
        ('6110', 'BD', 'UK'): (12, 20, 10, 'EBA'),
        ('6111', 'VN', 'UK'): (12, 20, 9, 'CPTPP'),
        ('62046827', 'VN', 'UK'): (9, 20, 7, 'CPTPP'),
        ('62046827', 'CN', 'UK'): (12, 20, 0, None),
        ('85165829', 'MX', 'US'): (5, 0, 5, 'USMCA'),
        ('85165829', 'MX', 'UK'): (8, 20, 0, None),
        ('63029990', 'PT', 'UK'): (0, 20, 0, None),
        ('63029990', 'PT', 'EU'): (0, 21, 0, None),
        ('63026131', 'TR', 'UK'): (12, 20, 9, 'CU'),
        ('63026131', 'TR', 'EU'): (8, 21, 8, 'CU'),
    }

    for dest in destinations:
        for hs in hs_codes:
            for origin in origins:
                key = (hs, origin, dest)
                if key in rate_map:
                    duty, vat, pref, scheme = rate_map[key]
                else:
                    duty = r.choice([8, 10, 12, 15, 20, 25])
                    vat = 20 if dest == 'UK' else (21 if dest == 'EU' else 0)
                    pref = duty - r.randint(0, 3) if r.random() < 0.3 else 0
                    scheme = None

                duty_rates.append({
                    'hs_code': hs,
                    'origin_country': origin,
                    'destination_market': dest,
                    'duty_rate_pct': duty,
                    'vat_rate_pct': vat,
                    'preferential_rate_pct': pref if pref > 0 else None,
                    'preference_scheme': scheme,
                    'effective_date': g.as_of - timedelta(days=r.randint(30, 365)),
                    'end_date': None,
                    'last_updated': g.as_of
                })

    # Import entries: customs clearances by PO and origin
    import_entries = []
    po_list = g.master('purchase_orders')[:100]
    for i, po in enumerate(po_list):
        if po['status'] in ('cancelled', 'draft'):
            continue
        sku = g.pick(g.master('products'))['sku']
        origin = r.choice(origins)
        hs = r.choice(hs_codes)
        qty = r.randint(100, 5000)
        value_per_unit = r.uniform(20, 200)
        total_value = qty * value_per_unit

        # Find applicable duty rate
        duty_rate = 15  # default
        vat_rate = 20   # default UK
        for dr in duty_rates:
            if dr['hs_code'] == hs and dr['origin_country'] == origin and dr['destination_market'] == 'UK':
                duty_rate = dr['duty_rate_pct']
                vat_rate = dr['vat_rate_pct']
                break

        duty_gbp = total_value * duty_rate / 100.0
        vat_gbp = (total_value + duty_gbp) * vat_rate / 100.0

        entry_date = datetime.fromisoformat(po['due_date']).date()
        cleared = r.random() < 0.95

        import_entries.append({
            'entry_id': f'ENT-{len(import_entries) + 1:06d}',
            'po_id': po['po_id'],
            'sku': sku,
            'origin_country': origin,
            'declared_value_gbp': round(total_value, 2),
            'hs_code_used': hs,
            'quantity': qty,
            'duty_paid_gbp': round(duty_gbp, 2) if cleared else None,
            'vat_paid_gbp': round(vat_gbp, 2) if cleared else None,
            'insurance_gbp': round(total_value * 0.02, 2),
            'freight_gbp': round(total_value * 0.08, 2),
            'entry_date': entry_date,
            'cleared_date': entry_date + timedelta(days=r.randint(1, 5)) if cleared else None,
            'status': 'cleared' if cleared else 'held',
            'reassessment_exposure_gbp': round(duty_gbp * 0.2, 2) if r.random() < 0.1 else 0,
            'notes': '',
            'updated_at': g.as_of
        })

    # VAT transactions: monthly postings by entity and code
    vat_transactions = []
    entities = ['LE-UK', 'LE-PL', 'LE-HK']
    periods = ['2026-Q1', '2026-Q2', '2026-Q3']
    vat_codes = ['S', 'Z', 'E', 'M']

    for entity in entities:
        for period in periods:
            for _ in range(r.randint(50, 200)):
                vat_code = r.choice(vat_codes)
                amount = r.uniform(100, 50000)
                vat_amount = amount * (0.20 if vat_code == 'S' else 0)

                vat_transactions.append({
                    'vat_txn_id': f'VTX-{len(vat_transactions) + 1:06d}',
                    'entity_id': entity,
                    'period': period,
                    'transaction_date': g.as_of - timedelta(days=r.randint(0, 90)),
                    'invoice_number': f'INV-{r.randint(10000, 99999)}',
                    'vat_code': vat_code,
                    'amount_gbp': round(amount, 2),
                    'vat_gbp': round(vat_amount, 2),
                    'description': '',
                    'po_id': r.choice(po_list)['po_id'] if r.random() < 0.5 else None,
                    'status': 'posted',
                    'corrected_to_code': None,
                    'updated_at': g.as_of
                })

    # VAT returns: summary by entity and period
    vat_returns = []
    for entity in entities:
        for period in periods:
            box_1 = r.uniform(500000, 2000000)
            box_4 = box_1 * 0.20
            box_5 = r.uniform(300000, 800000)
            box_6 = box_4 - box_5

            vat_returns.append({
                'entity_id': entity,
                'period': period,
                'box_1_gbp': round(box_1, 2),
                'box_2_gbp': round(box_1 * 0.05, 2),
                'box_4_gbp': round(box_4, 2),
                'box_5_gbp': round(box_5, 2),
                'box_6_gbp': round(box_6, 2),
                'box_7_gbp': round(box_1 / 1.20, 2),
                'box_8_gbp': round(box_5 / 1.20, 2),
                'expected_box_6_gbp': round(box_6 + r.gauss(0, box_6 * 0.05), 2),
                'variance_gbp': round(r.gauss(0, box_6 * 0.05), 2),
                'submitted': True,
                'submitted_date': g.as_of - timedelta(days=r.randint(5, 30)),
                'updated_at': g.as_of
            })

    # Transfer pricing policies: for each entity
    tp_policies = []
    for entity in entities:
        tp_policies.append({
            'entity_id': entity,
            'policy_version': '2.0',
            'profit_mark_up_pct': r.choice([8, 10, 12, 15]),
            'functions_performed': 'sourcing, quality control, logistics',
            'assets_controlled': 'inventory, contracts, brand',
            'risks_assumed': 'market risk, operational risk',
            'comparables_used': True,
            'documentation_status': r.choice(['complete', 'incomplete', 'missing']),
            'last_audit_date': g.as_of - timedelta(days=r.randint(180, 730)),
            'exposure_gbp': round(r.uniform(50000, 500000), 2),
            'updated_at': g.as_of
        })

    # Transfer pricing documents
    tp_documents = []
    doc_types = ['functional analysis', 'comparables study', 'transfer pricing study']
    for entity in entities:
        for doc_type in doc_types:
            tp_documents.append({
                'doc_id': f'TPD-{len(tp_documents) + 1:06d}',
                'entity_id': entity,
                'doc_type': doc_type,
                'file_path': f'files/{entity}_{doc_type.replace(" ", "_")}.md',
                'held': r.random() < 0.7,
                'required_by': g.as_of + timedelta(days=r.randint(30, 365)),
                'summary': f'Transfer pricing {doc_type} for {entity}',
                'updated_at': g.as_of
            })

    # Tax compliance tasks
    tax_tasks = []
    task_types = ['documentation', 'declaration', 'audit response', 'policy']
    for i in range(20):
        tax_tasks.append({
            'task_id': f'TCT-{len(tax_tasks) + 1:06d}',
            'task_type': r.choice(task_types),
            'description': f'Tax compliance task {i+1}',
            'entity_id': r.choice(entities),
            'assigned_to': f'EMP-{r.randint(1, 100):04d}',
            'due_date': g.as_of + timedelta(days=r.randint(7, 90)),
            'status': r.choice(['open', 'in_progress', 'completed']),
            'priority': r.choice(['low', 'medium', 'high']),
            'raised_date': g.as_of - timedelta(days=r.randint(1, 30)),
            'completed_date': None,
            'notes': '',
            'updated_at': g.as_of
        })

    # Incentive records
    incentive_records = []
    for i in range(10):
        capex = r.uniform(100000, 1000000)
        incentive_records.append({
            'incentive_id': f'INC-{len(incentive_records) + 1:06d}',
            'incentive_type': r.choice(['automation relief', 'renewable energy', 'RD credit']),
            'entity_id': r.choice(entities),
            'site_id': r.choice(['DC1', 'DC2', 'DC3']),
            'capex_gbp': round(capex, 2),
            'eligible_amount_gbp': round(capex * r.uniform(0.7, 1.0), 2),
            'relief_rate_pct': r.choice([10, 15, 20, 25]),
            'estimated_relief_gbp': round(capex * r.choice([10, 15, 20, 25]) / 100.0, 2),
            'conditions': 'Equipment must be new and used for eligible activity',
            'application_deadline': g.as_of + timedelta(days=r.randint(30, 180)),
            'applied': r.random() < 0.5,
            'applied_date': None,
            'updated_at': g.as_of
        })

    # Tariff scenarios
    tariff_scenarios = []
    scenario_names = [
        '15% Turkey tariff on textiles',
        'US tariff increase on electronics',
        'Brexit tariff changes on PT imports',
        'New safeguard on VN footwear'
    ]
    for i, name in enumerate(scenario_names):
        tariff_scenarios.append({
            'scenario_id': f'TSC-{i + 1:06d}',
            'scenario_name': name,
            'base_period': '2027',
            'origin_country': r.choice(['TR', 'CN', 'VN', 'PT']),
            'hs_code_range': f'{r.choice(hs_codes)}-{r.choice(hs_codes)}',
            'duty_rate_change_pct': r.choice([5, 10, 15, 25]),
            'estimated_volume_gbp': round(r.uniform(1000000, 10000000), 2),
            'estimated_duty_impact_gbp': round(r.uniform(100000, 1500000), 2),
            'probability_pct': r.randint(20, 80),
            'mitigation_options': 'origin diversification, price adjustment, sourcing changes',
            'created_date': g.as_of - timedelta(days=r.randint(30, 180)),
            'updated_at': g.as_of
        })

    return {
        'duty_rates': duty_rates,
        'import_entries': import_entries,
        'vat_transactions': vat_transactions,
        'vat_returns': vat_returns,
        'transfer_pricing_policies': tp_policies,
        'transfer_pricing_documents': tp_documents,
        'tax_compliance_tasks': tax_tasks,
        'incentive_records': incentive_records,
        'tariff_scenarios': tariff_scenarios
    }
