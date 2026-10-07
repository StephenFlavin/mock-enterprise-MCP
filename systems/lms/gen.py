"""Labour management data: shifts, productivity, costs for DC1-DC3."""
from datetime import datetime, timedelta
import itertools


def generate(g):
    r = g.rng
    sites = ['DC1', 'DC2', 'DC3']
    shifts = ['early', 'late', 'night']
    processes = ['receiving', 'putaway', 'picking', 'packing', 'shipping']
    labour_types = ['permanent', 'overtime', 'agency']
    pick_methods = ['wave', 'batch', 'discrete']
    zones = ['pick-a', 'pick-b', 'pick-c']
    agencies = ['SUP-0001', 'SUP-0002', 'SUP-0003']

    rosters, hours, productivity, quality, picks = [], [], [], [], []
    starters, requests, standards, patterns, rates = [], [], [], [], []

    # Generate 12 weeks of historical data (going back 84 days from as_of)
    weeks = g.weeks(12)

    # 1. Shift rosters: daily for each site and shift
    for week_monday in weeks:
        for day_offset in range(7):
            date = week_monday + timedelta(days=day_offset)
            for site in sites:
                for shift in shifts:
                    base_count = 80 if site == 'DC1' else (60 if site == 'DC2' else 45)
                    scheduled = r.randint(int(base_count * 0.85), int(base_count * 1.1))
                    permanent = int(scheduled * r.uniform(0.7, 0.85))
                    agency_c = scheduled - permanent
                    attended = r.randint(int(scheduled * 0.92), scheduled)
                    rosters.append({
                        'site_id': site, 'roster_date': date, 'shift_type': shift,
                        'scheduled_count': scheduled, 'permanent_count': permanent,
                        'agency_count': agency_c, 'attended_count': attended,
                        'updated_at': date - timedelta(days=1)
                    })

    # 2. Labour hours: weekly summary
    for week_monday in weeks:
        for site in sites:
            for ltype in labour_types:
                if ltype == 'permanent':
                    total_hours = r.uniform(1400, 1800)
                    productive_hours = total_hours * 0.92
                    cost_gbp = productive_hours * 15.5
                elif ltype == 'overtime':
                    total_hours = r.uniform(100, 400)
                    productive_hours = total_hours * 0.95
                    cost_gbp = productive_hours * 23.25  # 1.5x permanent
                else:  # agency
                    total_hours = r.uniform(50, 300)
                    productive_hours = total_hours * 0.90
                    cost_gbp = productive_hours * 18.75
                hours.append({
                    'site_id': site, 'week_start': week_monday, 'labour_type': ltype,
                    'total_hours': round(total_hours, 1), 'productive_hours': round(productive_hours, 1),
                    'cost_gbp': round(cost_gbp, 2), 'updated_at': week_monday - timedelta(days=1)
                })

    # 3. Labour productivity: units per hour by process and labour type
    for week_monday in weeks:
        for site in sites:
            for process in processes:
                for ltype in labour_types:
                    if process == 'receiving':
                        base_rate = 180
                    elif process == 'putaway':
                        base_rate = 220
                    elif process == 'picking':
                        base_rate = 240
                    elif process == 'packing':
                        base_rate = 300
                    else:  # shipping
                        base_rate = 200

                    if ltype == 'permanent':
                        rate_mult = 1.0
                        hours_used = r.uniform(200, 300)
                    elif ltype == 'overtime':
                        rate_mult = 0.85  # fatigue impact
                        hours_used = r.uniform(50, 150)
                    else:  # agency
                        rate_mult = 0.75  # less experienced
                        hours_used = r.uniform(40, 120)

                    units_per_hour = base_rate * rate_mult * r.uniform(0.9, 1.1)
                    units_handled = int(units_per_hour * hours_used)

                    productivity.append({
                        'site_id': site, 'week_start': week_monday, 'process_type': process,
                        'labour_type': ltype, 'units_handled': units_handled,
                        'labour_hours': round(hours_used, 1), 'units_per_hour': round(units_per_hour, 1),
                        'updated_at': week_monday - timedelta(days=1)
                    })

    # 4. Quality metrics: error rates by labour type
    for week_monday in weeks:
        for site in sites:
            for ltype in labour_types:
                picks_proc = r.randint(4000, 8000)
                if ltype == 'permanent':
                    error_rate = r.uniform(0.5, 1.2)
                elif ltype == 'overtime':
                    error_rate = r.uniform(1.0, 1.8)
                else:  # agency
                    error_rate = r.uniform(1.5, 2.5)
                errors = max(0, int(picks_proc * error_rate / 100.0))
                quality.append({
                    'site_id': site, 'week_start': week_monday, 'labour_type': ltype,
                    'picks_processed': picks_proc, 'picks_with_error': errors,
                    'error_rate_pct': round(100.0 * errors / picks_proc, 2),
                    'updated_at': week_monday - timedelta(days=1)
                })

    # 5. Pick operations by method and zone
    for week_monday in weeks:
        for site in sites:
            for method in pick_methods:
                for zone in zones:
                    picks_c = r.randint(800, 2000)
                    items = r.randint(3000, 8000)
                    if method == 'wave':
                        picks_per_hour = r.uniform(45, 65)
                    elif method == 'batch':
                        picks_per_hour = r.uniform(50, 72)
                    else:  # discrete
                        picks_per_hour = r.uniform(35, 50)
                    hours_used = picks_c / picks_per_hour if picks_per_hour > 0 else 20
                    picks.append({
                        'site_id': site, 'week_start': week_monday, 'pick_method': method,
                        'zone': zone, 'picks_completed': picks_c, 'items_picked': items,
                        'labour_hours': round(hours_used, 1), 'picks_per_hour': round(picks_per_hour, 1),
                        'updated_at': week_monday - timedelta(days=1)
                    })

    # 6. New starters throughout the period
    starter_count = 0
    for week_monday in weeks[::2]:  # Every other week
        for site in sites:
            num_starts = r.randint(2, 6)
            for _ in range(num_starts):
                starter_count += 1
                start_date = week_monday + timedelta(days=r.randint(0, 4))
                ltype = r.choice(['permanent', 'agency'])
                training_done = (r.random() < 0.6) if start_date < g.as_of else False
                training_d = start_date + timedelta(days=7) if training_done else None
                starters.append({
                    'starter_id': f'NST-{starter_count:06d}', 'site_id': site,
                    'start_date': start_date, 'labour_type': ltype,
                    'role': r.choice(['operative', 'team_lead', 'specialist']),
                    'training_complete': training_done, 'training_date': training_d,
                    'employee_id': None, 'updated_at': start_date + timedelta(days=1)
                })

    # 7. Agency labour requests
    req_count = 0
    for week_monday in weeks[::1]:
        for site in sites:
            num_reqs = r.randint(0, 2)
            for _ in range(num_reqs):
                req_count += 1
                shift = r.choice(shifts)
                days_out = r.randint(3, 28)
                from_date = week_monday + timedelta(days=days_out)
                to_date = from_date + timedelta(days=r.randint(7, 42))
                qty = r.randint(5, 25)
                if from_date < g.as_of:
                    rand_val = r.random()
                    if rand_val < 0.4:
                        status = 'confirmed'
                    elif rand_val < 0.7:
                        status = 'filled'
                    else:
                        status = 'cancelled'
                else:
                    rand_val = r.random()
                    if rand_val < 0.3:
                        status = 'draft'
                    elif rand_val < 0.6:
                        status = 'submitted'
                    else:
                        status = 'confirmed'
                supplier = r.choice(agencies) if status != 'draft' else None
                rate = round(r.uniform(14.5, 22.0), 2) if status != 'draft' else None
                requests.append({
                    'request_id': f'ALR-{req_count:06d}', 'site_id': site,
                    'shift_type': shift, 'date_from': from_date, 'date_to': to_date,
                    'quantity_required': qty, 'labour_type': 'operative',
                    'status': status, 'supplier_id': supplier, 'cost_per_hour_gbp': rate,
                    'created_at': week_monday, 'updated_at': week_monday
                })

    # 8. Productivity standards (fixed)
    for site in sites:
        for process in processes:
            for role in ['operative', 'team_lead']:
                if process == 'receiving':
                    std_rate = 180 if role == 'operative' else 200
                elif process == 'putaway':
                    std_rate = 220 if role == 'operative' else 250
                elif process == 'picking':
                    std_rate = 240 if role == 'operative' else 270
                elif process == 'packing':
                    std_rate = 300 if role == 'operative' else 330
                else:  # shipping
                    std_rate = 200 if role == 'operative' else 225
                standards.append({
                    'site_id': site, 'process_type': process, 'role': role,
                    'standard_units_per_hour': std_rate, 'updated_at': g.as_of
                })

    # 9. Shift patterns (fixed per site)
    patterns_data = [
        {'site_id': 'DC1', 'pattern_name': 'two-shift', 'early': 120, 'late': 120, 'night': 0, 'ot': 15},
        {'site_id': 'DC2', 'pattern_name': 'three-shift', 'early': 80, 'late': 80, 'night': 80, 'ot': 12},
        {'site_id': 'DC3', 'pattern_name': 'flexible', 'early': 60, 'late': 70, 'night': 40, 'ot': 18},
    ]
    for pd in patterns_data:
        patterns.append({
            'site_id': pd['site_id'], 'pattern_name': pd['pattern_name'],
            'early_shift_hours': pd['early'], 'late_shift_hours': pd['late'],
            'night_shift_hours': pd['night'], 'overtime_hours_avg': pd['ot'],
            'updated_at': g.as_of
        })

    # 10. Handling rates (fixed)
    for site in sites:
        for op in ['dc_receiving', 'dc_putaway', 'dc_picking', 'dc_packing', 'dc_shipping']:
            if op == 'dc_receiving':
                cost_unit = r.uniform(0.35, 0.55)
                rate = 180
            elif op == 'dc_putaway':
                cost_unit = r.uniform(0.40, 0.60)
                rate = 220
            elif op == 'dc_picking':
                cost_unit = r.uniform(0.30, 0.50)
                rate = 240
            elif op == 'dc_packing':
                cost_unit = r.uniform(0.25, 0.40)
                rate = 300
            else:  # shipping
                cost_unit = r.uniform(0.35, 0.55)
                rate = 200
            rates.append({
                'site_id': site, 'operation_type': op,
                'cost_per_unit_gbp': round(cost_unit, 2),
                'units_per_labour_hour': rate,
                'updated_at': g.as_of
            })
    # Cross-dock rates
    for rate_type in ['cross_dock']:
        for site in sites:
            rates.append({
                'site_id': site, 'operation_type': rate_type,
                'cost_per_unit_gbp': round(r.uniform(0.15, 0.30), 2),
                'units_per_labour_hour': r.randint(250, 400),
                'updated_at': g.as_of
            })

    return {
        'shift_rosters': rosters, 'labour_hours': hours, 'labour_productivity': productivity,
        'quality_metrics': quality, 'pick_operations': picks, 'new_starters': starters,
        'agency_labour_requests': requests, 'productivity_standards': standards,
        'shift_patterns': patterns, 'handling_rates': rates
    }
