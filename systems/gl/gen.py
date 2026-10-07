"""
Generate GL system data: journal entries, inventory valuation, cost centre actuals,
intercompany transactions, FX movements, freight and handling costs.
"""

def generate(g):
    """
    Generate GL system data for Harbour & Vale.

    Key tables:
    - journal_entries: ~200 draft/posted entries per month
    - inventory_by_site: Stock at cost + provisions by DC/store
    - cost_centre_actuals: Actual costs by cost centre, period and account
    - intercompany_transactions: Intercompany postings with FX
    - accruals: Month-end accruals with auto-reversals
    - fx_gains_losses: FX revaluation by currency
    - freight_costs: Inbound/outbound freight
    - handling_costs: Handling and packing by channel
    - order_charges: Order-level financial data
    - erp_stock: Stock balance snapshot by SKU and location
    - reconciliations: Balance sheet reconciliation tracking
    """

    je_id = 0
    accrual_id = 0
    ic_txn_id = 0
    freight_id = 0
    handling_id = 0
    fx_id = 0
    recon_id = 0

    # Master data
    entities = ['LE-UK', 'LE-IE', 'LE-NL', 'LE-DE', 'LE-US', 'LE-HK']
    sites = ['DC1', 'DC2', 'DC3', 'DC4', 'DC5', 'ST001', 'ST002', 'ST003']
    cost_centres = ['CC-2101', 'CC-2102', 'CC-2103', 'CC-2104', 'CC-2105']
    employees = [f'EMP-{i:05d}' for i in range(100, 120)]

    # Get products and suppliers from master
    products = g.master('products')[:200]  # ~200 SKUs
    suppliers = g.master('suppliers')

    # ===== Journal Entries =====
    journal_entries = []
    journal_lines = []
    je_types = ['manual', 'accrual', 'inventory', 'intercompany', 'fx', 'reclassification']
    statuses = ['draft', 'submitted', 'approved', 'posted', 'reversed']

    # Generate ~150 journal entries across statuses
    for i in range(150):
        je_id += 1
        je_id_str = f'JE-{je_id:06d}'
        entity_id = g.pick(entities)
        posting_date = g.date_between(90, 0)
        status = g.pick(statuses)
        je_type = g.pick(je_types)

        total_debit = g.rng.randint(1000, 50000)
        total_credit = total_debit

        journal_entries.append({
            'je_id': je_id_str,
            'entity_id': entity_id,
            'posting_date': posting_date,
            'description': f'{je_type.upper()} entry {i+1}',
            'status': status,
            'je_type': je_type,
            'created_by': g.pick(employees),
            'submitted_by': g.pick(employees) if status in ['submitted', 'approved', 'posted'] else '',
            'approved_by': g.pick(employees) if status in ['approved', 'posted'] else '',
            'auto_reversal_date': g.days_ago(-30) if je_type == 'accrual' else '',
            'created_at': g.fake.date_time_this_month(),
            'updated_at': g.fake.date_time_this_month(),
            'total_debit_gbp': total_debit,
            'total_credit_gbp': total_credit,
        })

        # Add 2-4 lines per entry
        for line_no in range(1, g.rng.randint(2, 5)):
            if line_no == 1:
                amount = total_debit
                debit = amount
                credit = 0
            elif line_no == len(range(2, g.rng.randint(2, 5))):
                amount = total_credit
                debit = 0
                credit = amount
            else:
                amount = total_debit // 2
                debit = amount
                credit = 0

            journal_lines.append({
                'je_id': je_id_str,
                'line_no': line_no,
                'account_code': f'{1000 + g.rng.randint(0, 9999):05d}',
                'account_desc': f'Account {line_no}',
                'cost_centre_id': g.pick(cost_centres) if g.rng.random() > 0.3 else '',
                'debit_gbp': debit,
                'credit_gbp': credit,
                'currency': 'GBP',
                'amount_local': debit + credit,
                'reference': f'REF-{g.rng.randint(1000, 9999)}' if g.rng.random() > 0.5 else '',
            })

    # ===== Inventory by Site =====
    inventory_by_site = []
    for site_id in sites:
        for product in g.pick(products, k=50):
            sku = product['sku']
            units = g.rng.randint(0, 500)
            unit_cost = float(product.get('unit_cost_gbp', 25.0))
            total_value = units * unit_cost

            # Some items slow-moving or obsolete
            status = 'active'
            provision_pct = 0.0
            if units > 100 and g.rng.random() > 0.8:
                status = 'slow_moving'
                provision_pct = 0.10
            elif units < 10 and g.rng.random() > 0.7:
                status = 'obsolete'
                provision_pct = 0.50

            provision_gbp = total_value * provision_pct

            inventory_by_site.append({
                'sku': sku,
                'site_id': site_id,
                'as_of_date': g.as_of,
                'units_on_hand': units,
                'unit_cost_gbp': round(unit_cost, 2),
                'total_value_gbp': round(total_value, 2),
                'provision_pct': round(provision_pct, 2),
                'provision_gbp': round(provision_gbp, 2),
                'net_value_gbp': round(total_value - provision_gbp, 2),
                'status': status,
            })

    # ===== Cost Centre Actuals =====
    cost_centre_actuals = []
    periods = [f'FY27-{m:02d}' for m in range(7, 10)]  # Jul, Aug, Sep
    accounts = [f'{1000 + i:05d}' for i in range(100)]

    for cost_centre in cost_centres:
        for period in periods:
            # Use each account only once per cost centre per period
            used_accounts = set()
            for account in g.pick(accounts, k=5):
                if account not in used_accounts:
                    used_accounts.add(account)
                    amount = g.rng.randint(5000, 50000)
                    budget = amount * g.rng.uniform(0.9, 1.1)

                    cost_centre_actuals.append({
                        'cost_centre_id': cost_centre,
                        'account_code': account,
                        'period': period,
                        'amount_gbp': round(amount, 2),
                        'budget_gbp': round(budget, 2),
                        'variance_gbp': round(amount - budget, 2),
                    })

    # ===== Intercompany Transactions =====
    intercompany_transactions = []
    entity_pairs = [
        ('LE-UK', 'LE-IE'),
        ('LE-UK', 'LE-US'),
        ('LE-HK', 'LE-NL'),
    ]

    for from_entity, to_entity in entity_pairs:
        for _ in range(g.rng.randint(5, 15)):
            ic_txn_id += 1
            amount = g.rng.randint(10000, 200000)
            fx_rate = g.rng.uniform(0.85, 1.15)

            intercompany_transactions.append({
                'ic_txn_id': f'IC-{ic_txn_id:06d}',
                'from_entity_id': from_entity,
                'to_entity_id': to_entity,
                'je_id': f'JE-{g.rng.randint(1, 150):06d}',
                'posting_date': g.date_between(30, 0),
                'amount_gbp': round(amount, 2),
                'currency': 'GBP',
                'amount_local': round(amount * fx_rate, 2),
                'fx_rate': round(fx_rate, 4),
                'description': f'IC purchase {from_entity} to {to_entity}',
                'reference': f'PO-{g.rng.randint(100000, 999999)}',
                'matched_to': '',
                'status': g.pick(['unmatched', 'matched', 'matched', 'matched']),
            })

    # ===== Accruals =====
    accruals = []
    accrual_descriptions = [
        'Month-end rent accrual',
        'Utilities accrual',
        'Bonus accrual',
        'Maintenance accrual',
        'Insurance accrual',
    ]

    for i in range(15):
        accrual_id += 1
        amount = g.rng.randint(10000, 100000)

        accruals.append({
            'accrual_id': f'ACC-{accrual_id:06d}',
            'je_id': f'JE-{g.rng.randint(1, 150):06d}',
            'reversal_je_id': '',
            'period': f'FY27-{g.rng.randint(7, 9):02d}',
            'description': g.pick(accrual_descriptions),
            'amount_gbp': round(amount, 2),
            'accrual_date': g.date_between(30, 0),
            'reversal_date': g.days_ago(-30),
            'status': g.pick(['open', 'open', 'reversed']),
        })

    # ===== FX Gains/Losses =====
    fx_gains_losses = []
    currencies = ['USD', 'EUR', 'JPY', 'CAD']

    for _ in range(30):
        fx_id += 1
        currency = g.pick(currencies)
        gbp_amount = g.rng.randint(10000, 100000)

        opening_rate = g.rng.uniform(0.80, 1.20)
        closing_rate = opening_rate * g.rng.uniform(0.95, 1.05)

        fx_gains_losses.append({
            'fx_txn_id': f'FX-{fx_id:06d}',
            'je_id': f'JE-{g.rng.randint(1, 150):06d}',
            'posting_date': g.date_between(90, 0),
            'currency': currency,
            'gbp_amount': round(gbp_amount, 2),
            'local_amount': round(gbp_amount / opening_rate, 2),
            'opening_rate': round(opening_rate, 4),
            'closing_rate': round(closing_rate, 4),
            'gain_loss_gbp': round((closing_rate - opening_rate) * gbp_amount / opening_rate, 2),
            'fx_type': g.pick(['realised', 'unrealised']),
            'account_code': f'{8000 + g.rng.randint(0, 99):05d}',
        })

    # ===== Freight Costs =====
    freight_costs = []
    shipment_ids = ['SHP-0000001', 'SHP-0000002', 'SHP-0000003', 'SHP-0000004', 'SHP-0000005']
    for _ in range(40):
        freight_id += 1
        cost = g.rng.randint(500, 5000)

        freight_costs.append({
            'freight_id': f'FRT-{freight_id:06d}',
            'je_id': f'JE-{g.rng.randint(1, 150):06d}',
            'posting_date': g.date_between(30, 0),
            'account_code': f'{6000 + g.rng.randint(0, 99):05d}',
            'shipment_id': g.pick(shipment_ids) if g.rng.random() > 0.3 else '',
            'supplier_id': g.pick(suppliers)['supplier_id'] if suppliers else 'SUP-0001',
            'cost_gbp': round(cost, 2),
            'description': 'Inbound freight' if g.rng.random() > 0.5 else 'Outbound freight',
        })

    # ===== Handling Costs =====
    handling_costs = []
    channels = ['web', 'app', 'click_collect', 'marketplace', 'store', 'warehouse']

    for _ in range(50):
        handling_id += 1
        units = g.rng.randint(100, 1000)
        cost_per_unit = g.rng.uniform(0.5, 2.0)
        total_cost = units * cost_per_unit

        handling_costs.append({
            'handling_id': f'HDL-{handling_id:06d}',
            'je_id': f'JE-{g.rng.randint(1, 150):06d}',
            'posting_date': g.date_between(30, 0),
            'channel': g.pick(channels),
            'cost_gbp': round(total_cost, 2),
            'units_handled': units,
            'cost_per_unit_gbp': round(cost_per_unit, 4),
            'description': f'Handling {units} units',
        })

    # ===== Order Charges =====
    order_charges = []
    orders = g.master('orders')

    for order in g.pick(orders, k=100):
        order_value = float(order['value_gbp'])
        order_charges.append({
            'order_id': order['order_id'],
            'entity_id': g.pick(entities),
            'posting_date': order['order_date'],
            'revenue_gbp': round(order_value, 2),
            'freight_charge_gbp': round(g.rng.uniform(3.0, 15.0), 2),
            'handling_charge_gbp': round(g.rng.uniform(1.0, 5.0), 2),
            'discount_gbp': round(g.rng.uniform(0, order_value * 0.1), 2),
            'total_charges_gbp': round(order_value + g.rng.uniform(3.0, 15.0) + g.rng.uniform(1.0, 5.0), 2),
            'je_id': '',
        })

    # ===== ERP Stock =====
    erp_stock = []
    for product in g.pick(products, k=100):
        sku = product['sku']
        for site in g.pick(sites, k=3):
            units = g.rng.randint(0, 200)
            unit_cost = float(product.get('unit_cost_gbp', 25.0))

            erp_stock.append({
                'sku': sku,
                'site_id': site,
                'location_id': '',
                'as_of_date': g.as_of,
                'quantity': units,
                'unit_cost_gbp': round(unit_cost, 2),
                'total_value_gbp': round(units * unit_cost, 2),
            })

    # ===== Reconciliations =====
    reconciliations = []
    for i in range(20):
        recon_id += 1

        reconciliations.append({
            'recon_id': f'R-{recon_id:06d}',
            'account_code': f'{1000 + g.rng.randint(0, 9999):05d}',
            'period': f'FY27-{g.rng.randint(7, 9):02d}',
            'entity_id': g.pick(entities),
            'status': g.pick(['open', 'open', 'signed_off', 'disputed']),
            'assigned_to': g.pick(employees),
            'reviewer': g.pick(employees),
            'opened_date': g.date_between(60, 0),
            'signed_off_date': '',
            'notes': f'Reconciliation for account {i+1}',
        })

    return {
        'journal_entries': journal_entries,
        'journal_lines': journal_lines,
        'accruals': accruals,
        'intercompany_transactions': intercompany_transactions,
        'inventory_by_site': inventory_by_site,
        'cost_centre_actuals': cost_centre_actuals,
        'fx_gains_losses': fx_gains_losses,
        'freight_costs': freight_costs,
        'handling_costs': handling_costs,
        'order_charges': order_charges,
        'erp_stock': erp_stock,
        'reconciliations': reconciliations,
    }
