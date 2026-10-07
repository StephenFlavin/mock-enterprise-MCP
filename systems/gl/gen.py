"""
Generate GL system data for Harbour & Vale: journals, accruals, reconciliations, intercompany,
DC cost centre actuals and activity, labour rate card, ERP stock, in-transit documents,
freight and recovery postings, FX and inventory valuation.

Story rows (September close, UK/Polish intercompany, DC1 cost per unit, freight ledger, ...)
live in seed/*.csv and in the small story blocks below. Everything else is background noise
kept small and realistic so the stories are the first thing a tool returns.
"""
import calendar
import random
from datetime import date, timedelta

FINANCE = ['EMP-00085', 'EMP-00086', 'EMP-00087', 'EMP-00088', 'EMP-00089']
ANALYSTS = ['EMP-00077', 'EMP-00078', 'EMP-00079', 'EMP-00081', 'EMP-00084']
ENTITIES = ['LE-UK', 'LE-IE', 'LE-NL', 'LE-DE', 'LE-US', 'LE-HK', 'LE-PL']
ENTITY_WEIGHTS = [55, 6, 8, 6, 9, 8, 8]

ACCOUNTS = [
    ('1100', 'Bank - current accounts', 'asset'),
    ('1200', 'Trade receivables', 'asset'),
    ('1210', 'Provision for doubtful debts', 'asset'),
    ('1300', 'Inventory - finished goods', 'asset'),
    ('1310', 'Inventory provision - slow-moving and obsolete', 'asset'),
    ('1500', 'Prepayments', 'asset'),
    ('1600', 'Intercompany receivable', 'asset'),
    ('1800', 'Fixed assets - cost', 'asset'),
    ('2100', 'Trade payables', 'liability'),
    ('2200', 'Accruals', 'liability'),
    ('2210', 'Goods received not invoiced', 'liability'),
    ('2300', 'Intercompany payable', 'liability'),
    ('2400', 'VAT control', 'liability'),
    ('2500', 'Payroll control', 'liability'),
    ('4000', 'Sales revenue', 'income'),
    ('5000', 'Cost of goods sold', 'expense'),
    ('5110', 'Freight and carriage', 'expense'),
    ('5102', 'Carrier charges (legacy code)', 'expense'),
    ('6100', 'Warehouse operating costs', 'expense'),
    ('6110', 'Warehouse labour', 'expense'),
    ('6120', 'Warehouse overtime', 'expense'),
    ('6130', 'Agency labour', 'expense'),
    ('6140', 'Damages and write-offs', 'expense'),
    ('6150', 'Rework and re-pick', 'expense'),
    ('6200', 'Energy and utilities', 'expense'),
    ('6210', 'Rent and rates', 'expense'),
    ('6800', 'Bad debt expense', 'expense'),
    ('6900', 'Intercompany recharges', 'expense'),
    ('7000', 'Marketing', 'expense'),
    ('7100', 'IT and software licences', 'expense'),
    ('7200', 'Restructuring costs', 'expense'),
    ('8100', 'FX gains and losses', 'expense'),
    ('8110', 'Realised FX gains and losses', 'expense'),
    ('8120', 'Unrealised FX revaluation gains and losses', 'expense'),
]
CATEGORY_ACCOUNT = {'labour': '6110', 'overtime': '6120', 'agency': '6130', 'damages': '6140',
                    'rework': '6150', 'energy': '6200', 'rent': '6210'}
RATE = {'labour': 14.40, 'overtime': 20.16, 'agency': 17.86}   # GBP per paid hour (DC1)

# GBP per local currency unit is 1/rate; rates are local units per GBP
LOCAL_RATE = {'GBP': 1.0, 'EUR': 1.17, 'USD': 1.27, 'HKD': 9.9, 'PLN': 5.06}
ENTITY_CCY = {'LE-UK': 'GBP', 'LE-IE': 'EUR', 'LE-NL': 'EUR', 'LE-DE': 'EUR', 'LE-US': 'USD', 'LE-HK': 'HKD', 'LE-PL': 'PLN'}


def fy_label(y, m):
    fy = y + 1 if m >= 2 else y
    per = m - 1 if m >= 2 else 12
    return f'FY{fy % 100:02d}-{per:02d}'


def month_end(y, m):
    return date(y, m, calendar.monthrange(y, m)[1])


def months_back(as_of, n):
    """Last n complete calendar months before as_of, oldest first, as (year, month)."""
    y, m = as_of.year, as_of.month
    out = []
    for _ in range(n):
        m -= 1
        if m == 0:
            y, m = y - 1, 12
        out.append((y, m))
    return out[::-1]


def generate(g):
    rng = g.rng
    as_of = g.as_of
    products = {p['sku']: p for p in g.master('products')}
    sites = {s['site_id']: s for s in g.master('sites')}

    # ---------------------------------------------------------------- accounts
    accounts = [{'account_code': c, 'name': n, 'account_type': t} for c, n, t in ACCOUNTS]

    # ---------------------------------------------------------------- journal entries (background)
    journal_entries, journal_lines = [], []
    jtypes = (['manual'] * 28 + ['accrual'] * 20 + ['inventory'] * 15 + ['intercompany'] * 12 + ['fx'] * 10 +
              ['reclassification'] * 15)
    recurring_manual = ['Monthly depreciation allocation', 'Prepayment release - insurance', 'Payroll cost allocation to cost centres',
                        'Monthly management charge', 'Rebate accrual true-up (standard template)']
    adhoc_manual = ['Correction of duplicate supplier invoice', 'Credit note posted to wrong period', 'Bank charges reclass',
                    'Petty cash replenishment', 'Customer refund correction', 'Rounding difference write-off']
    reclass_desc = ['Reclass between cost centres', 'Reclass of marketing spend to correct entity', 'Reclass of DC consumables to opex',
                    'Reclass of utilities between sites']
    accrual_desc = ['Month-end accrual - utilities', 'Month-end accrual - agency labour', 'Month-end accrual - rent',
                    'Month-end accrual - maintenance', 'Month-end accrual - insurance']
    inv_desc = ['Inventory valuation adjustment', 'Stock count adjustment', 'Standard cost revaluation']
    fx_desc = ['FX revaluation - USD balances', 'FX revaluation - EUR balances', 'FX revaluation - HKD balances']
    for i in range(1, 221):
        je = f'JE-{i:06d}'
        age = rng.randint(1, 120)
        entity = rng.choices(ENTITIES, weights=ENTITY_WEIGHTS)[0]
        jt = rng.choice(jtypes)
        recurring = False
        amt = round(min(60000, max(800, rng.lognormvariate(8.8, 0.9))), 2)
        impact = 0.0
        if jt == 'manual':
            if rng.random() < 0.6:
                desc, recurring = rng.choice(recurring_manual), True
            else:
                desc = rng.choice(adhoc_manual)
                amt = round(min(amt, 18000), 2)
                impact = round(rng.choice([-1, 1]) * amt * rng.uniform(0.2, 1.0), 2)
            dr, cr = rng.choice([('6100', '2200'), ('6900', '2300'), ('1500', '6100'), ('2100', '5000')])
        elif jt == 'reclassification':
            desc = rng.choice(reclass_desc)
            amt = round(min(amt, 25000), 2)
            dr, cr = rng.choice([('6100', '7000'), ('6110', '6100'), ('6200', '6100')])
        elif jt == 'accrual':
            desc, recurring = rng.choice(accrual_desc), True
            dr, cr = rng.choice([('6200', '2200'), ('6130', '2200'), ('6210', '2200'), ('6100', '2200')])
        elif jt == 'inventory':
            desc = f'{rng.choice(inv_desc)} - {rng.choice(["DC1", "DC2", "DC3", "DC4", "DC5"])}'
            dr, cr = rng.choice([('1300', '5000'), ('5000', '1300'), ('1310', '5000')])
        elif jt == 'intercompany':
            other = rng.choice([e for e in ENTITIES if e != entity])
            desc = f'Intercompany recharge {entity} to {other}'
            recurring = True
            dr, cr = '1600', '6900'
        else:
            desc = rng.choice(fx_desc)
            recurring = True
            dr, cr = rng.choice([('8100', '2100'), ('1100', '8100')])
        if age <= 10:
            status = rng.choices(['draft', 'submitted', 'approved', 'posted'], weights=[20, 20, 15, 45])[0]
        else:
            status = rng.choices(['posted', 'reversed', 'approved'], weights=[90, 6, 4])[0]
        creator = rng.choice(FINANCE + ANALYSTS)
        posting = g.days_ago(age)
        created = f'{g.days_ago(age + 1).isoformat()} {rng.randint(8, 17):02d}:{rng.randint(0, 59):02d}:00'
        journal_entries.append({
            'je_id': je, 'entity_id': entity, 'posting_date': posting, 'description': desc, 'status': status,
            'je_type': jt, 'created_by': creator,
            'submitted_by': rng.choice(FINANCE) if status in ('submitted', 'approved', 'posted', 'reversed') else '',
            'approved_by': 'EMP-00002' if status in ('approved', 'posted', 'reversed') and amt > 25000 else
                           (rng.choice(FINANCE) if status in ('approved', 'posted', 'reversed') else ''),
            'auto_reversal_date': posting + timedelta(days=30) if jt == 'accrual' else '',
            'created_at': created, 'updated_at': created, 'total_debit_gbp': amt, 'total_credit_gbp': amt,
            'debit_account': dr, 'credit_account': cr, 'reference': '', 'recurring': recurring,
            'pl_impact_gbp': impact, 'counterparty_entity_id': '',
        })
        for n, (acct, d, c) in enumerate(((dr, amt, 0.0), (cr, 0.0, amt)), start=1):
            journal_lines.append({
                'je_id': je, 'line_no': n, 'account_code': acct,
                'account_desc': next(a[1] for a in ACCOUNTS if a[0] == acct),
                'cost_centre_id': rng.choice(['CC-2101', 'CC-2102', 'CC-2103', 'CC-2119']) if acct.startswith('6') else '',
                'debit_gbp': d, 'credit_gbp': c, 'currency': 'GBP', 'amount_local': amt, 'reference': ''})

    # ---------------------------------------------------------------- accruals (background: recent, small)
    accruals = []
    acc_desc = [('Utilities accrual - DC electricity', '6200'), ('Rent accrual - store portfolio', '6210'),
                ('Agency labour accrual - peak preparation', '6130'), ('Maintenance accrual - MHE contracts', '6100'),
                ('Insurance accrual - property', '6100'), ('Bonus accrual - monthly', '2500')]
    for i in range(1, 9):
        age = rng.randint(2, 24)
        d, acct = rng.choice(acc_desc)
        accruals.append({
            'accrual_id': f'ACC-{i:06d}', 'je_id': '', 'reversal_je_id': '', 'period': 'FY27-08',
            'description': d, 'amount_gbp': round(rng.uniform(8000, 48000), 2),
            'accrual_date': g.days_ago(age), 'reversal_date': g.days_ago(age) + timedelta(days=rng.randint(21, 45)),
            'status': 'open', 'entity_id': rng.choices(ENTITIES, weights=ENTITY_WEIGHTS)[0], 'item_type': 'accrual',
            'account_code': acct, 'owner_id': rng.choice(FINANCE)})
    for i in range(9, 20):   # older, already reversed
        age = rng.randint(30, 150)
        d, acct = rng.choice(acc_desc)
        accruals.append({
            'accrual_id': f'ACC-{i:06d}', 'je_id': '', 'reversal_je_id': '', 'period': fy_label(*months_back(as_of, 6)[rng.randint(0, 4)]),
            'description': d, 'amount_gbp': round(rng.uniform(8000, 60000), 2),
            'accrual_date': g.days_ago(age), 'reversal_date': g.days_ago(age) + timedelta(days=rng.randint(25, 32)),
            'status': 'reversed', 'entity_id': rng.choices(ENTITIES, weights=ENTITY_WEIGHTS)[0], 'item_type': 'accrual',
            'account_code': acct, 'owner_id': rng.choice(FINANCE)})

    # ---------------------------------------------------------------- reconciliations (background)
    reconciliations = []
    recon_accts = [('1100', 'Bank - current accounts'), ('1200', 'Trade receivables'), ('1300', 'Inventory - finished goods'),
                   ('1500', 'Prepayments'), ('2100', 'Trade payables'), ('2200', 'Accruals'), ('2210', 'Goods received not invoiced'),
                   ('2400', 'VAT control'), ('2500', 'Payroll control'), ('1800', 'Fixed assets - cost')]
    n = 0
    for (y, m) in months_back(as_of, 2):    # prior periods, all signed off
        for acct, name in recon_accts:
            for ent in rng.sample(ENTITIES, 2):
                n += 1
                closed = month_end(y, m) + timedelta(days=rng.randint(4, 9))
                reconciliations.append({
                    'recon_id': f'R-{n:06d}', 'account_code': acct, 'account_desc': name, 'period': fy_label(y, m),
                    'entity_id': ent, 'status': 'signed_off', 'assigned_to': rng.choice(FINANCE), 'reviewer': 'EMP-00087',
                    'opened_date': month_end(y, m) + timedelta(days=1), 'signed_off_date': closed,
                    'notes': 'Reconciled to sub-ledger, no reconciling items.', 'balance_gbp': 0.0})
    for acct, name in recon_accts:           # current period: mostly signed off already, a few open and recent
        for ent in rng.sample(ENTITIES, 2):
            n += 1
            is_open = rng.random() < 0.3
            opened = g.days_ago(rng.randint(3, 12))
            reconciliations.append({
                'recon_id': f'R-{n:06d}', 'account_code': acct, 'account_desc': name, 'period': 'FY27-08',
                'entity_id': ent, 'status': 'open' if is_open else 'signed_off', 'assigned_to': rng.choice(FINANCE),
                'reviewer': 'EMP-00087', 'opened_date': opened,
                'signed_off_date': '' if is_open else opened + timedelta(days=rng.randint(1, 3)),
                'notes': 'Awaiting sub-ledger cut-off confirmation.' if is_open else 'Reconciled.',
                'balance_gbp': round(rng.uniform(2000, 38000), 2) if is_open else 0.0})

    # ---------------------------------------------------------------- inventory by site (old noise, only kept to preserve the random stream;
    # the real table is rebuilt from erp_stock in build_inventory() below)
    plist = g.master('products')[:200]
    inventory_by_site = []
    for site_id in ['DC1', 'DC2', 'DC3', 'DC4', 'DC5', 'ST001', 'ST002', 'ST003']:
        for product in g.pick(plist, k=50):
            units = rng.randint(0, 500)
            unit_cost = float(product.get('unit_cost_gbp') or 25.0)
            total_value = units * unit_cost
            status, provision_pct = 'active', 0.0
            if units > 100 and rng.random() > 0.8:
                status, provision_pct = 'slow_moving', 0.10
            elif units < 10 and rng.random() > 0.7:
                status, provision_pct = 'obsolete', 0.50
            provision_gbp = total_value * provision_pct
            inventory_by_site.append({
                'sku': product['sku'], 'site_id': site_id, 'as_of_date': as_of, 'units_on_hand': units,
                'unit_cost_gbp': round(unit_cost, 2), 'total_value_gbp': round(total_value, 2),
                'provision_pct': round(provision_pct, 2), 'provision_gbp': round(provision_gbp, 2),
                'net_value_gbp': round(total_value - provision_gbp, 2), 'status': status})

    # ---------------------------------------------------------------- DC cost centre actuals and activity
    cost_centre_actuals, dc_activity = [], []
    seasonal = {1: .92, 2: .90, 3: .95, 4: .97, 5: .96, 6: .94, 7: .96, 8: 1.0, 9: .98, 10: 1.05, 11: 1.28, 12: 1.35}
    dcs = {  # cost centre: (site, base units per month, labour cpu, orders per unit, rent per sqft per year)
        'CC-2101': ('DC1', 3_520_000, 0.378, 0.403, 6.0),
        'CC-2102': ('DC2', 3_050_000, 0.452, 0.52, 6.0),
        'CC-2103': ('DC3', 1_900_000, 0.43, 0.38, 5.4),
        'CC-2104': ('DC4', 2_300_000, 0.36, 0.34, 5.2),
        'CC-2105': ('DC5', 2_100_000, 0.31, 0.30, 4.6),
    }
    story = {   # DC1 (CC-2101) story months: units, orders, paid hours (perm, ot, agency), other costs
        (2026, 8): dict(units=3_520_000, orders=1_420_000, h=(92_400, 6_200, 8_400), dmg=41_200, rew=33_100, en=168_400, rent=425_000),
        (2026, 9): dict(units=3_440_000, orders=1_445_000, h=(92_000, 10_300, 11_200), dmg=46_900, rew=47_300, en=169_900, rent=425_000),
        (2025, 9): dict(units=3_310_000, orders=1_380_000, h=(90_500, 5_600, 7_900), dmg=36_800, rew=29_900, en=151_200, rent=405_000),
    }
    story_rates = {(2025, 9): (13.60, 19.04, 16.90)}
    for cc, (site, base_units, lab_cpu, ord_per_unit, rent_sqft) in dcs.items():
        sqft = float(sites[site]['sqft'])
        for (y, m) in months_back(as_of, 13):
            pend = month_end(y, m)
            label = fy_label(y, m)
            if cc == 'CC-2101' and (y, m) in story:
                s = story[(y, m)]
                rates = story_rates.get((y, m), (RATE['labour'], RATE['overtime'], RATE['agency']))
                units, orders, (ph, oh, ah) = s['units'], s['orders'], s['h']
                costs = {'labour': ph * rates[0], 'overtime': oh * rates[1], 'agency': ah * rates[2],
                         'damages': s['dmg'], 'rework': s['rew'], 'energy': s['en'], 'rent': s['rent']}
                hours = ph + oh + ah
            else:
                units = int(base_units * seasonal[m] * rng.uniform(0.97, 1.03))
                if cc == 'CC-2101':
                    drift = 1 + 0.006 * ((y - 2025) * 12 + m - 9)        # slow cost drift across the year
                    ph = int(units * 0.0262 * rng.uniform(0.98, 1.02))
                    oh = int(ph * 0.062 * rng.uniform(0.85, 1.15) * (1.2 if m in (11, 12) else 1))
                    ah = int(ph * 0.078 * rng.uniform(0.85, 1.15) * (1.4 if m in (11, 12) else 1))
                    rates = (RATE['labour'] * (0.97 + 0.003 * ((y - 2025) * 12 + m - 9)), RATE['overtime'] * 0.97, RATE['agency'] * 0.97)
                else:
                    drift = 1.0
                    ph = int(units * lab_cpu / 14.4 * rng.uniform(0.98, 1.02))
                    oh = int(ph * 0.06 * rng.uniform(0.85, 1.15))
                    ah = int(ph * 0.07 * rng.uniform(0.85, 1.15))
                    rates = (RATE['labour'], RATE['overtime'], RATE['agency'])
                costs = {'labour': ph * rates[0], 'overtime': oh * rates[1], 'agency': ah * rates[2],
                         'damages': units * 0.0117 * rng.uniform(0.9, 1.1), 'rework': units * 0.0094 * rng.uniform(0.9, 1.1),
                         'energy': sqft * 0.198 * rng.uniform(0.94, 1.08) * (1.12 if m in (12, 1, 2) else 1),
                         'rent': sqft * rent_sqft / 12}
                orders = int(units * ord_per_unit * rng.uniform(0.98, 1.02))
                hours = ph + oh + ah
            dc_activity.append({'cost_centre_id': cc, 'period': label, 'period_end': pend, 'units_shipped': units,
                                'orders_shipped': orders, 'paid_hours': hours,
                                'overtime_hours': (oh if not (cc == 'CC-2101' and (y, m) in story) else story[(y, m)]['h'][1]),
                                'agency_hours': (ah if not (cc == 'CC-2101' and (y, m) in story) else story[(y, m)]['h'][2])})
            for cat, amount in costs.items():
                amount = round(amount, 2)
                if cc == 'CC-2101' and (y, m) in story:
                    budget = round(amount * (1.0 if cat in ('rent',) else rng.uniform(0.97, 1.0)), 2)
                    if (y, m) == (2026, 9) and cat in ('overtime', 'agency', 'rework'):
                        budget = round(costs[cat] * 0.66, 2)
                else:
                    budget = round(amount / rng.uniform(0.97, 1.04), 2)
                cost_centre_actuals.append({
                    'cost_centre_id': cc, 'account_code': CATEGORY_ACCOUNT[cat], 'period': label, 'period_end': pend,
                    'category': cat, 'amount_gbp': amount, 'budget_gbp': budget, 'variance_gbp': round(amount - budget, 2)})

    # ---------------------------------------------------------------- labour rate card
    labour_rate_card = []
    for site, (base, otm, night, allow, onc, apay, amar, auplift, onb, share) in {
            'DC1': (12.80, 1.5, 25.0, 9.50, 14.0, 13.20, 3.90, 12.0, 1200.0, 70.0),
            'DC2': (12.60, 1.5, 25.0, 9.50, 14.0, 13.00, 3.90, 12.0, 1150.0, 65.0),
            'DC3': (12.40, 1.5, 25.0, 9.00, 14.0, 12.80, 3.80, 12.0, 1100.0, 60.0)}.items():
        labour_rate_card.append({
            'site_id': site, 'base_hourly_gbp': base, 'overtime_multiplier': otm, 'night_premium_pct': night,
            'night_allowance_per_shift_gbp': allow, 'employer_oncost_pct': onc, 'overtime_meal_allowance_per_shift_gbp': 4.0,
            'agency_pay_hourly_gbp': apay, 'agency_margin_hourly_gbp': amar, 'agency_night_uplift_pct': auplift,
            'onboarding_cost_per_hire_gbp': onb, 'late_shift_agency_share_pct': share, 'hours_per_fte_week': 40.0,
            'shifts_per_fte_week': 5.0, 'rate_card_ref': 'Agency rate card and September labour data'})

    # ---------------------------------------------------------------- intercompany (background pairs, matched)
    intercompany_transactions = []
    ic_n = 100
    pairs = [('LE-UK', 'LE-IE', 'EUR', 12), ('LE-UK', 'LE-US', 'USD', 10), ('LE-HK', 'LE-NL', 'EUR', 12), ('LE-HK', 'LE-UK', 'HKD', 12),
             ('LE-UK', 'LE-PL', 'GBP', 12), ('LE-PL', 'LE-UK', 'PLN', 6)]
    for frm, to, ccy, count in pairs:
        for k in range(count):
            ic_n += 1
            gbp = round(rng.uniform(14000, 64000), 2)
            rate = LOCAL_RATE[ccy] if ccy != 'GBP' else 1.0
            pdate = g.days_ago(rng.randint(12, 80)) if (frm, to) in (('LE-UK', 'LE-PL'), ('LE-PL', 'LE-UK')) else g.days_ago(rng.randint(3, 80))
            desc = {'LE-HK': 'Sourcing commission', 'LE-PL': 'Poland services recharge'}.get(frm, 'IC purchase and recharge')
            unmatched = (frm, to) not in (('LE-UK', 'LE-PL'), ('LE-PL', 'LE-UK')) and rng.random() < 0.12
            intercompany_transactions.append({
                'ic_txn_id': f'IC-{ic_n:06d}', 'from_entity_id': frm, 'to_entity_id': to, 'je_id': '', 'posting_date': pdate,
                'amount_gbp': gbp, 'currency': ccy, 'amount_local': round(gbp * rate, 2), 'fx_rate': rate,
                'description': f'{desc} {frm[3:]} to {to[3:]}', 'reference': f'INV-{frm[3:]}-{rng.randint(10000, 99999)}',
                'matched_to': '' if unmatched else f'IC-{ic_n + 5000:06d}', 'status': 'unmatched' if unmatched else 'matched',
                'counterparty_amount_gbp': '' if unmatched else gbp,
                'counterparty_posting_date': '' if unmatched else pdate + timedelta(days=rng.randint(0, 2)),
                'counterparty_fx_rate': '' if unmatched else rate})

    # ---------------------------------------------------------------- FX gains and losses (unchanged background)
    fx_gains_losses = []
    for i in range(1, 31):
        ccy = rng.choice(['USD', 'EUR', 'JPY', 'CAD'])
        gbp_amount = rng.randint(10000, 100000)
        o = rng.uniform(0.80, 1.20)
        c = o * rng.uniform(0.95, 1.05)
        fx_gains_losses.append({
            'fx_txn_id': f'FX-{i:06d}', 'je_id': f'JE-{rng.randint(1, 150):06d}', 'posting_date': g.date_between(90, 0),
            'currency': ccy, 'gbp_amount': round(gbp_amount, 2), 'local_amount': round(gbp_amount / o, 2),
            'opening_rate': round(o, 4), 'closing_rate': round(c, 4), 'gain_loss_gbp': round((c - o) * gbp_amount / o, 2),
            'fx_type': (fxt := rng.choice(['realised', 'unrealised'])), 'account_code': '8110' if fxt == 'realised' else '8120'})

    # ---------------------------------------------------------------- freight postings (ledger side of the TMS reconciliation)
    freight_costs = []
    fr_n = 0
    ledger_posted = {   # carrier: GBP posted to 5110 in the last four weeks (agrees with the logistics reconciliation)
        'CAR-001': 53230, 'CAR-002': 51421, 'CAR-003': 107811, 'CAR-004': 63829, 'CAR-005': 34834, 'CAR-006': 43046,
        'CAR-007': 32118, 'CAR-008': 41783, 'CAR-009': 48144, 'CAR-010': 29170, 'CAR-011': 972, 'CAR-012': 1516,
        'CAR-013': 928, 'CAR-014': 839, 'CAR-015': 329}
    carriers = {c['carrier_id']: c['name'] for c in g.master('carriers')}
    for car, total in ledger_posted.items():
        first = round(total * 0.55)
        for age, amt in ((12, first), (5, total - first)):
            fr_n += 1
            freight_costs.append({
                'freight_id': f'FRT-{fr_n:06d}', 'je_id': '', 'posting_date': g.days_ago(age), 'account_code': '5110',
                'shipment_id': '', 'supplier_id': '', 'cost_gbp': float(amt), 'carrier_id': car,
                'invoice_ref': f'FRT-{rng.randint(100000, 999999)}', 'cost_centre_id': 'CC-2124',
                'description': f'Weekly freight invoices - {carriers[car]}'})
        for month_age in (38, 66, 94, 122):          # earlier months, same pattern with noise
            fr_n += 1
            freight_costs.append({
                'freight_id': f'FRT-{fr_n:06d}', 'je_id': '', 'posting_date': g.days_ago(month_age + rng.randint(0, 6)),
                'account_code': '5110', 'shipment_id': '', 'supplier_id': '',
                'cost_gbp': round(total * rng.uniform(0.85, 1.12), 2), 'carrier_id': car,
                'invoice_ref': f'FRT-{rng.randint(100000, 999999)}', 'cost_centre_id': 'CC-2124',
                'description': f'Weekly freight invoices - {carriers[car]}'})

    # ---------------------------------------------------------------- recovery channels (circular economy)
    handling_costs = []
    hid = 0
    # (channel, units this year, handling cost per unit, recovered value this year, units last year factor, cost/unit last yr factor)
    channels = [('take_back', 270, 2.60, 758.0, 0.60, 1.10), ('resale', 456, 0.95, 592.0, 0.72, 1.12),
                ('repair', 238, 1.85, 500.0, 0.55, 1.08), ('recycling', 330, 0.80, 290.0, 0.82, 1.05)]
    seas = [0.7, 0.8, 0.9, 1.0, 1.1, 1.3, 1.2, 1.0, 0.9, 0.9, 1.0, 1.2]
    for ch, units, cpu, rec, uf, cf in channels:
        for yr in (0, 1):
            tot_units = units if yr == 0 else round(units * uf)
            tot_rec = rec if yr == 0 else round(rec * uf * 0.9, 2)
            cost_per = cpu if yr == 0 else round(cpu * cf, 2)
            w = [s * rng.uniform(0.9, 1.1) for s in seas]
            ws = sum(w)
            left_u, left_r = tot_units, tot_rec
            for k in range(12):
                mon_age = 5 + int(30.4 * k) + 365 * yr
                if k == 11:
                    u, r = left_u, left_r
                else:
                    u, r = round(tot_units * w[k] / ws), round(tot_rec * w[k] / ws, 2)
                    left_u -= u
                    left_r = round(left_r - r, 2)
                hid += 1
                handling_costs.append({
                    'handling_id': f'HDL-{hid:06d}', 'je_id': '', 'posting_date': g.days_ago(mon_age), 'channel': ch,
                    'cost_gbp': round(u * cost_per, 2), 'units_handled': u, 'cost_per_unit_gbp': cost_per,
                    'recovered_value_gbp': r, 'description': f'{ch.replace("_", " ").title()} monthly handling and recovery posting'})

    # ---------------------------------------------------------------- order charges (old noise, kept to preserve the random stream;
    # rebuilt from master orders in build_order_charges() below)
    order_charges = []
    for order in g.pick(g.master('orders'), k=100):
        v = float(order['value_gbp'])
        order_charges.append({
            'order_id': order['order_id'], 'entity_id': rng.choice(ENTITIES[:6]), 'posting_date': order['order_date'],
            'revenue_gbp': round(v, 2), 'freight_charge_gbp': round(rng.uniform(3.0, 15.0), 2),
            'handling_charge_gbp': round(rng.uniform(1.0, 5.0), 2), 'discount_gbp': round(rng.uniform(0, v * 0.1), 2),
            'total_charges_gbp': round(v + rng.uniform(3.0, 15.0) + rng.uniform(1.0, 5.0), 2), 'je_id': ''})

    # ---------------------------------------------------------------- ERP stock: one balance per DC SKU, last night's close
    erp_stock = []
    snap = g.days_ago(1)
    for row in g.master('dc_stock'):
        p = products.get(row['sku'])
        if not p:
            continue
        qty = int(row['on_hand'])
        cost = float(p['unit_cost_gbp'])
        erp_stock.append({'sku': row['sku'], 'site_id': row['site_id'], 'location_id': '', 'as_of_date': snap,
                          'quantity': qty, 'unit_cost_gbp': round(cost, 2), 'total_value_gbp': round(qty * cost, 2)})

    # ---------------------------------------------------------------- goods movements pending in one system
    goods_movements = []
    n = 0
    # WMS shipped inter-site transfers, ERP goods receipt not yet posted (transfer ids as in the WMS)
    transfers = [('STR-000040', 'DC3', 'DC4', 'SKU-105236', 754, 0), ('STR-000112', 'DC1', 'DC4', 'SKU-100406', 887, 1),
                 ('STR-000123', 'DC1', 'DC4', 'SKU-100273', 1089, 7), ('STR-000045', 'DC5', 'DC4', 'SKU-102338', 717, 8),
                 ('STR-000129', 'DC1', 'DC4', 'SKU-105768', 983, 15), ('STR-000036', 'DC4', 'DC1', 'SKU-101659', 582, 16),
                 ('STR-000009', 'DC4', 'DC3', 'SKU-103514', 351, 16)]
    for ref, a, b, sku, qty, age in transfers:
        n += 1
        goods_movements.append({
            'doc_id': f'MD-{n + 4900000:07d}', 'doc_type': 'stock_transfer', 'reference': ref, 'from_site_id': a, 'to_site_id': b,
            'sku': sku, 'quantity': qty, 'value_gbp': round(qty * float(products[sku]['unit_cost_gbp']), 2),
            'posted_date': g.days_ago(age + 1), 'posted_in': 'WMS', 'pending_in': 'ERP',
            'note': 'Shipped in WMS, ERP goods receipt not yet posted at destination'})
    # ERP goods receipts posted from the ASN, WMS put-away confirmation still pending
    receipts = [('SHP-0001244', 'PO-2026-005425', 'DC1', 5), ('SHP-0000772', 'PO-2026-004898', 'DC3', 6),
                ('SHP-0000889', 'PO-2026-005022', 'DC4', 6), ('SHP-0000107', 'PO-2026-004127', 'DC2', 5)]
    pol = g.master('po_lines')
    pos = {p['po_id']: p for p in g.master('purchase_orders')}
    fxr = {'GBP': 1.0, 'USD': 0.79, 'EUR': 0.855}
    for shp, po, site, age in receipts:
        lines = [l for l in pol if l['po_id'] == po]
        if not lines:
            continue
        l = max(lines, key=lambda x: float(x['qty_ordered']) * float(x['unit_cost']))
        qty = int(float(l['qty_ordered']))
        val = round(qty * float(l['unit_cost']) * fxr[pos[po]['currency']], 2)
        n += 1
        goods_movements.append({
            'doc_id': f'MD-{n + 4900000:07d}', 'doc_type': 'goods_receipt', 'reference': shp, 'from_site_id': '', 'to_site_id': site,
            'sku': l['sku'], 'quantity': qty, 'value_gbp': val, 'posted_date': g.days_ago(age), 'posted_in': 'ERP',
            'pending_in': 'WMS', 'note': f'ERP goods receipt for {po} posted from the ASN, WMS put-away not confirmed'})

    # ---------------------------------------------------------------- job 2 stories (own random stream)
    lr = random.Random(260707)
    apply_erp_story(g, lr, products, erp_stock, goods_movements)
    inventory_by_site = build_inventory(g, lr, products, erp_stock)
    inventory_monthly = build_inventory_monthly(g, lr, products, inventory_by_site)
    ledger_balances = build_ledger_balances(inventory_monthly)
    sourcing_margins = build_sourcing_margins()
    supplier_payments = build_supplier_payments(g, lr)
    order_charges = build_order_charges(g, lr)

    return {
        'accounts': accounts,
        'journal_entries': journal_entries,
        'journal_lines': journal_lines,
        'accruals': accruals,
        'reconciliations': reconciliations,
        'intercompany_transactions': intercompany_transactions,
        'inventory_by_site': inventory_by_site,
        'cost_centre_actuals': cost_centre_actuals,
        'dc_activity': dc_activity,
        'labour_rate_card': labour_rate_card,
        'fx_gains_losses': fx_gains_losses,
        'freight_costs': freight_costs,
        'handling_costs': handling_costs,
        'order_charges': order_charges,
        'erp_stock': erp_stock,
        'goods_movements': goods_movements,
        'inventory_monthly': inventory_monthly,
        'ledger_balances': ledger_balances,
        'sourcing_margins': sourcing_margins,
        'supplier_payments': supplier_payments,
    }
