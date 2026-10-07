"""Labour management data: shifts, productivity, costs for DC1-DC3.

Everything is derived from one headcount model (heads per site/shift/week) so rosters, labour hours,
productivity and agency requests agree with each other.  k = whole weeks before as_of (k=1 is the last
complete week).  Stories (see scenarios.yaml):
  DC1  late-shift agency/new-starter ramp from k=9 (Aug), overtime and agency up in the last 4 weeks (k<=4),
       early-shift shipping (loading) productivity drops from k=3 (store wave template change on 14 Sep).
  DC2  heavy agency share and low productivity on every process; batch picking trial in zones A/B since k=8.
  DC3  best productivity; returns centre (returns standard 45 units/hour); hosts the northern cross-dock.
"""
from datetime import timedelta

SITE_SHIFTS = {'DC1': ['early', 'late'], 'DC2': ['early', 'late', 'night'], 'DC3': ['early', 'late', 'night']}
# permanent heads, agency heads per shift per day (baseline)
HEADS = {
    ('DC1', 'early'): (62, 11), ('DC1', 'late'): (58, 12),
    ('DC2', 'early'): (36, 18), ('DC2', 'late'): (34, 20), ('DC2', 'night'): (26, 16),
    ('DC3', 'early'): (40, 6), ('DC3', 'late'): (36, 6), ('DC3', 'night'): (22, 4),
}
DC1_LATE_AGENCY = {9: 14, 8: 17, 7: 20, 6: 24, 5: 27, 4: 29, 3: 29, 2: 28, 1: 27}
OT_BASE = {('DC1', 'early'): 240, ('DC1', 'late'): 280, ('DC2', 'early'): 150, ('DC2', 'late'): 170,
           ('DC2', 'night'): 180, ('DC3', 'early'): 120, ('DC3', 'late'): 130, ('DC3', 'night'): 90}
HOURS_PER_HEAD_WEEK = 37.5           # 5 days x 7.5 h
RATE = {'permanent': 15.50, 'overtime': 23.25, 'agency': 18.75}
PRODUCTIVE = {'permanent': 0.92, 'overtime': 0.94, 'agency': 0.88}
PROCESSES = ['receiving', 'putaway', 'picking', 'packing', 'shipping']
PROC_WEIGHT = {'receiving': 0.14, 'putaway': 0.16, 'picking': 0.34, 'packing': 0.17, 'shipping': 0.19}
STD_RATE = {'receiving': 180, 'putaway': 220, 'picking': 240, 'packing': 300, 'shipping': 200}
TL_RATE = {'receiving': 200, 'putaway': 250, 'picking': 270, 'packing': 330, 'shipping': 225}
SITE_MULT = {
    'DC1': {'receiving': 0.97, 'putaway': 0.96, 'picking': 0.93, 'packing': 0.98, 'shipping': 0.97},
    'DC2': {'receiving': 0.86, 'putaway': 0.86, 'picking': 0.84, 'packing': 0.87, 'shipping': 0.86},
    'DC3': {'receiving': 1.0, 'putaway': 1.0, 'picking': 1.0, 'packing': 1.0, 'shipping': 1.0},
}
LT_MULT = {'permanent': 1.0, 'overtime': 0.90, 'agency': 0.78}
SHIFT_MULT = {'early': 1.0, 'late': 0.985, 'night': 0.97}


def generate(g):
    r = g.rng
    as_of = g.as_of
    sites = list(SITE_SHIFTS)
    weeks52 = g.weeks(52)

    def kof(week):
        return (as_of - week).days // 7

    def heads(site, shift, k):
        perm, ag = HEADS[(site, shift)]
        if site == 'DC1' and shift == 'late':
            ag = DC1_LATE_AGENCY.get(k, 12)
        return perm, ag

    def ot_hours(site, shift, k):
        base = OT_BASE[(site, shift)]
        if site == 'DC1':
            if k <= 4:
                base = 340 if shift == 'early' else 520
            elif k == 5:
                base = 250 if shift == 'early' else 300
        return base * r.uniform(0.96, 1.04)

    # ---- labour_hours (weekly by site, shift, labour type) -------------------------------------------
    hours, hours_idx = [], {}
    for wk in weeks52:
        k = kof(wk)
        for site in sites:
            for shift in SITE_SHIFTS[site]:
                perm, ag = heads(site, shift, k)
                for ltype in ('permanent', 'overtime', 'agency'):
                    if ltype == 'permanent':
                        total = perm * HOURS_PER_HEAD_WEEK * r.uniform(0.97, 1.0)
                    elif ltype == 'agency':
                        total = ag * HOURS_PER_HEAD_WEEK * r.uniform(0.97, 1.0)
                    else:
                        total = ot_hours(site, shift, k)
                    total = round(total, 1)
                    row = {'site_id': site, 'week_start': wk, 'shift_type': shift, 'labour_type': ltype,
                           'total_hours': total, 'productive_hours': round(total * PRODUCTIVE[ltype], 1),
                           'cost_gbp': round(total * RATE[ltype], 2), 'updated_at': wk - timedelta(days=1)}
                    hours.append(row)
                    hours_idx[(site, wk, shift, ltype)] = total

    # ---- labour_productivity: the same hours split across processes ----------------------------------
    productivity = []
    for wk in weeks52:
        k = kof(wk)
        for site in sites:
            for shift in SITE_SHIFTS[site]:
                for ltype in ('permanent', 'overtime', 'agency'):
                    total = hours_idx[(site, wk, shift, ltype)]
                    for proc in PROCESSES:
                        used = round(total * PROC_WEIGHT[proc], 1)
                        mult = SITE_MULT[site][proc] * LT_MULT[ltype] * SHIFT_MULT[shift]
                        if site == 'DC1' and shift == 'early' and proc == 'shipping' and k <= 3:
                            mult *= 0.76          # loading windows squeezed by the 14 Sep wave template change
                        if site == 'DC1' and shift == 'late' and k <= 7:
                            mult *= 0.97          # new starters on late shift
                        rate = STD_RATE[proc] * mult * r.uniform(0.985, 1.015)
                        units = int(rate * used)
                        productivity.append({
                            'site_id': site, 'week_start': wk, 'shift_type': shift, 'process_type': proc,
                            'labour_type': ltype, 'units_handled': units, 'labour_hours': used,
                            'units_per_hour': round(units / used, 1), 'updated_at': wk - timedelta(days=1)})

    # ---- shift rosters (Mon-Fri, last 15 weeks) -------------------------------------------------------
    rosters = []
    for wk in g.weeks(15):
        k = kof(wk)
        for d in range(5):
            day = wk + timedelta(days=d)
            factor = 1.0
            for site in sites:
                for shift in SITE_SHIFTS[site]:
                    perm, ag = heads(site, shift, k)
                    p = max(1, round(perm * factor * r.uniform(0.97, 1.03)))
                    a = max(1, round(ag * factor * r.uniform(0.96, 1.04)))
                    sched = p + a
                    rosters.append({
                        'site_id': site, 'roster_date': day, 'shift_type': shift, 'scheduled_count': sched,
                        'permanent_count': p, 'agency_count': a,
                        'attended_count': round(sched * r.uniform(0.93, 0.985)),
                        'updated_at': day - timedelta(days=1)})

    # ---- quality metrics (job 2 owns the story; seeds overlay the last weeks) ---------------------------
    quality = []
    for wk in g.weeks(12):
        for site in sites:
            for ltype in ('permanent', 'overtime', 'agency'):
                picks_proc = r.randint(4000, 8000)
                lo, hi = {'permanent': (0.5, 1.2), 'overtime': (1.0, 1.8), 'agency': (1.5, 2.5)}[ltype]
                errors = max(0, int(picks_proc * r.uniform(lo, hi) / 100.0))
                quality.append({
                    'site_id': site, 'week_start': wk, 'labour_type': ltype, 'picks_processed': picks_proc,
                    'picks_with_error': errors, 'error_rate_pct': round(100.0 * errors / picks_proc, 2),
                    'updated_at': wk - timedelta(days=1)})

    # ---- pick operations (last 15 weeks) ----------------------------------------------------------------
    picks = []
    base_volume = {'DC1': {'pick-a': 11000, 'pick-b': 10000, 'pick-c': 7000},
                   'DC2': {'pick-a': 14000, 'pick-b': 13000, 'pick-c': 9000},
                   'DC3': {'pick-a': 6500, 'pick-b': 6000, 'pick-c': 4000}}
    wave_rate = {'DC1': 48.0, 'DC2': 52.0, 'DC3': 46.0}
    for wk in g.weeks(15):
        k = kof(wk)
        for site in sites:
            for zone, vol in base_volume[site].items():
                batch_on = site == 'DC2' and zone in ('pick-a', 'pick-b') and k <= 8
                combos = [('wave', vol * (0.45 if batch_on else 1.0), wave_rate[site]),
                          ('discrete', vol * 0.08, 36.0)]
                if batch_on:
                    combos.append(('batch', vol * 0.55, wave_rate[site] * 1.28))
                for method, n, pph in combos:
                    n = int(n * r.uniform(0.97, 1.03))
                    pph = pph * r.uniform(0.98, 1.02)
                    ipp = 3.1 if method == 'batch' else 3.3
                    picks.append({
                        'site_id': site, 'week_start': wk, 'pick_method': method, 'zone': zone,
                        'picks_completed': n, 'items_picked': int(n * ipp * r.uniform(0.97, 1.03)),
                        'labour_hours': round(n / pph, 1), 'picks_per_hour': round(pph, 1),
                        'updated_at': wk - timedelta(days=1)})

    # ---- new starters: DC1 story is in seed/new_starters.csv; DC2/DC3 are background ---------------------
    starters = []
    n = 0
    for wk in g.weeks(15)[::2]:
        for site in ('DC2', 'DC3'):
            for _ in range(r.randint(1, 3)):
                n += 1
                start = wk + timedelta(days=r.randint(0, 4))
                done = (as_of - start).days > 14 and r.random() < 0.9
                starters.append({
                    'starter_id': f'NST-{n:06d}', 'site_id': site, 'start_date': start,
                    'shift_type': r.choice(SITE_SHIFTS[site]), 'labour_type': r.choice(['permanent', 'agency']),
                    'role': 'operative', 'training_complete': done,
                    'training_date': start + timedelta(days=7) if done else None,
                    'employee_id': None, 'updated_at': start + timedelta(days=1)})

    # ---- agency labour requests: only finished historic ones; current ones are seeded -------------------
    requests = []
    n = 0
    for wk in weeks52[:-8:2]:
        for site in sites:
            if r.random() < 0.6:
                n += 1
                shift = r.choice(SITE_SHIFTS[site])
                f = wk + timedelta(days=r.randint(0, 6))
                t = f + timedelta(days=r.randint(14, 35))
                done = r.random() < 0.8
                requests.append({
                    'request_id': f'ALR-{n:06d}', 'site_id': site, 'shift_type': shift, 'date_from': f,
                    'date_to': t, 'quantity_required': r.randint(5, 20), 'labour_type': 'operative',
                    'status': 'filled' if done else 'cancelled',
                    'supplier_id': r.choice(['SUP-0001', 'SUP-0002', 'SUP-0003']) if done else None,
                    'cost_per_hour_gbp': round(r.uniform(17.5, 19.5), 2) if done else None,
                    'created_at': f - timedelta(days=5), 'updated_at': f})

    # ---- productivity standards ---------------------------------------------------------------------------
    standards = []
    for site in sites:
        for proc in PROCESSES:
            for role, std in (('operative', STD_RATE[proc]), ('team_lead', TL_RATE[proc])):
                standards.append({'site_id': site, 'process_type': proc, 'role': role,
                                  'standard_units_per_hour': std, 'updated_at': as_of})
    # returns processing (inspect, grade, restock) runs at the returns DC (Leeds)
    standards.append({'site_id': 'DC3', 'process_type': 'returns', 'role': 'operative',
                      'standard_units_per_hour': 45, 'updated_at': as_of})
    standards.append({'site_id': 'DC3', 'process_type': 'returns', 'role': 'team_lead',
                      'standard_units_per_hour': 50, 'updated_at': as_of})

    # ---- shift patterns (fixed per site) --------------------------------------------------------------------
    patterns = []
    for site, name, e, l, nt, ot in [('DC1', 'two-shift', 120, 120, 0, 15), ('DC2', 'three-shift', 80, 80, 80, 22),
                                     ('DC3', 'flexible', 60, 70, 40, 18)]:
        patterns.append({'site_id': site, 'pattern_name': name, 'early_shift_hours': e, 'late_shift_hours': l,
                         'night_shift_hours': nt, 'overtime_hours_avg': ot, 'updated_at': as_of})

    # ---- handling rates ------------------------------------------------------------------------------------
    # (variable cost per unit, peak cost per unit, fixed cost per week, units per labour hour)
    dc_ops = {
        'DC1': {'dc_receiving': (0.42, 0.50, 3200, 180), 'dc_putaway': (0.48, 0.57, 2800, 220),
                'dc_picking': (0.65, 0.78, 6500, 240), 'dc_packing': (0.31, 0.37, 2400, 300),
                'dc_shipping': (0.38, 0.45, 3100, 200)},
        'DC2': {'dc_receiving': (0.44, 0.53, 2600, 180), 'dc_putaway': (0.50, 0.60, 2300, 220),
                'dc_picking': (0.70, 0.84, 5400, 240), 'dc_packing': (0.33, 0.40, 2100, 300),
                'dc_shipping': (0.40, 0.48, 2500, 200)},
        'DC3': {'dc_receiving': (0.40, 0.48, 1900, 180), 'dc_putaway': (0.46, 0.55, 1700, 220),
                'dc_picking': (0.60, 0.72, 3600, 240), 'dc_packing': (0.30, 0.36, 1400, 300),
                'dc_shipping': (0.36, 0.43, 1800, 200)},
    }
    rates = []
    for site, ops in dc_ops.items():
        for op, (c, pk, fx, uph) in ops.items():
            rates.append({
                'site_id': site, 'operation_type': op, 'cost_per_unit_gbp': c, 'peak_cost_per_unit_gbp': pk,
                'fixed_cost_per_week_gbp': fx, 'units_per_labour_hour': uph,
                'assumptions': 'Blended labour at 15.50 permanent / 18.75 agency / 23.25 overtime per hour, '
                               'equipment and overhead allocated; peak assumes 35% of hours on overtime or agency',
                'updated_at': as_of})
    rates.append({
        'site_id': 'DC3', 'operation_type': 'cross_dock', 'cost_per_unit_gbp': 0.36,
        'peak_cost_per_unit_gbp': 0.41, 'fixed_cost_per_week_gbp': 6500, 'units_per_labour_hour': 320,
        'assumptions': 'Northern cross-dock run from Leeds: receive, sort to store and load only (no putaway or '
                       'pick); fixed weekly cost covers dock lease and sortation equipment',
        'updated_at': as_of})

    return {
        'shift_rosters': rosters, 'labour_hours': hours, 'labour_productivity': productivity,
        'quality_metrics': quality, 'pick_operations': picks, 'new_starters': starters,
        'agency_labour_requests': requests, 'productivity_standards': standards,
        'shift_patterns': patterns, 'handling_rates': rates,
    }
