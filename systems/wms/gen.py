"""Warehouse data: stock by location, goods receipts, cycle counts, order lines, exceptions, patches.

Everything is derived from master data (dc_stock, locations, orders, purchase_orders, po_lines, shipments) so ids and
quantities line up with the other systems. Story rows (bay C-14, count priority, receipts from SUP-0072, allocation
failures, store-wave exceptions, WMS 9.2 duplicates, space growth) are built in code; the rest is background.

Windows are chosen so that numbers do not change when 'today' moves by up to a week: story rows sit well inside
rolling windows and quarter blocks (91 days) keep at least a 2 day margin from their edges.
"""
import math
import random
from datetime import datetime, timedelta

DCS = ['DC1', 'DC2', 'DC3', 'DC4', 'DC5']
PALLET_TYPES = ('reserve', 'bulk_floor')
AFFECTED_SUPPLIER = 'SUP-0013'          # SKUs hit by the pack-spec change (allocation failures)
STORY_RECEIPT_POS = {('PO-2026-005321', 'SKU-104991'), ('PO-2026-005133', 'SKU-104998')}

# units per pallet by category (pallet maths and space story)
UPP = {'Small Appliances': 160, 'Smart Home': 300, 'Audio': 320, 'Personal Care': 700, 'Lighting': 220, 'Storage': 180,
       'Cookware': 200, 'Drinkware': 400, 'Bedding': 120, 'Towels': 300, 'Footwear': 360, 'Bags': 300, 'Jewellery': 2000,
       'Scarves': 1500, 'Fragrance': 900, 'Haircare': 900, 'Bodycare': 900, 'Skincare': 1100}
UPP_DEFAULT = 1100
# weekly growth in occupied pallet positions by category at DC1 (autumn build-up for Christmas). About 27 a week in total, so the building
# (1158 positions, 114 free) is full in about four weeks: the same story as supply_planning, which projects DC1 over capacity from the
# week of 2 November, driven by Smart Home, Cookware and Small Appliances.
GROWTH_DC1 = {'Smart Home': 7.0, 'Small Appliances': 6.5, 'Cookware': 3.0, 'Audio': 2.0, 'Outerwear': 1.8, 'Bedding': 1.5,
              'Lighting': 1.3, 'Personal Care': 1.2, 'Drinkware': 0.9, 'Towels': 0.9, 'Fragrance': 0.8}

# accuracy-issue rate by DC1 zone for 13-week blocks, most recent first
ISSUE_RATE_DC1 = {'pick': [4.8, 4.4, 4.8, 4.5], 'reserve': [4.6, 4.9, 4.4, 4.8], 'bulk': [3.0, 3.4, 3.9, 4.3],
                  'hazmat': [5.0, 5.2, 4.8, 5.1], 'mezzanine': [14.5, 10.5, 7.5, 6.0]}

BAY_C14 = 'DC1-C-14'
# stock held in quarantine at DC1 and DC3 (status-mapping part of the ERP-WMS gap, about GBP 1.05m): (site, sku, units)
QUALITY_HOLDS = [('DC1', 'SKU-103507', 867), ('DC3', 'SKU-100819', 2939), ('DC1', 'SKU-101687', 1027), ('DC3', 'SKU-104690', 2757),
                 ('DC1', 'SKU-104270', 663), ('DC3', 'SKU-104053', 2842), ('DC1', 'SKU-102723', 876), ('DC3', 'SKU-103661', 1752),
                 ('DC1', 'SKU-101715', 1058), ('DC3', 'SKU-101750', 2879), ('DC1', 'SKU-103080', 671), ('DC3', 'SKU-104284', 2650),
                 ('DC1', 'SKU-101869', 696), ('DC3', 'SKU-106069', 2496), ('DC1', 'SKU-102338', 165)]
PACK_STORY_SKU = 'SKU-100532'     # Denim Small Appliance: corrugated vs moulded pulp vs recycled plastic pack comparison
MATERIAL_OF = {'carton': 'corrugated', 'polybag': 'plastic_film', 'hanging': 'hanger', 'tray': 'moulded_pulp', 'pouch': 'recycled_plastic'}


def generate(g):
    r = g.rng
    as_of = g.as_of
    D = lambda days_ago: as_of - timedelta(days=days_ago)

    def T(day, h=0, m=0, s=0):
        return datetime(day.year, day.month, day.day, h, m, s)

    def parse(s):
        return datetime.fromisoformat(s)

    products = g.master('products')
    prod = {p['sku']: p for p in products}
    cost = {s: float(p['unit_cost_gbp']) for s, p in prod.items()}
    locations = g.master('locations')
    loc = {l['location_id']: l for l in locations}
    dc_stock = g.master('dc_stock')
    employees = g.master('employees')
    master_orders = g.master('orders')
    pos = {p['po_id']: p for p in g.master('purchase_orders')}
    po_lines = g.master('po_lines')
    ships = {}
    for s in g.master('shipments'):
        ships.setdefault(s['po_id'], s)
    stores = [s for s in g.master('sites') if s['type'] == 'store']

    def emps(site, role, shift=None):
        return [e['employee_id'] for e in employees if e['site_id'] == site and e['role'] == role
                and (shift is None or e['shift'] == shift)]

    controllers = {s: emps(s, 'Inventory Controller') for s in DCS}
    clerks = {s: emps(s, 'Goods-in Clerk') for s in DCS}
    shift_of = {e['employee_id']: e['shift'] for e in employees}

    # ------------------------------------------------------------------ cause codes (same vocabulary as IMS)
    cause_codes = [
        ('shrink', 'Unexplained stock loss found at a count', 'loss', 'Use when stock is missing and no other cause is known after a recount.', False),
        ('damage', 'Goods damaged in the warehouse', 'damage', 'Damaged during handling, racking or picking. Attach the damage report.', False),
        ('expiry', 'Product past its expiry or best-before date', 'expiry', 'Write-off of expired lots only.', False),
        ('loss', 'Confirmed loss of stock', 'loss', 'Confirmed loss after investigation, for example lost pallet.', False),
        ('receiving_variance', 'Quantity received differs from the ASN or PO', 'receiving', 'Goods-in count differs from ASN. Raise the supplier claim separately.', False),
        ('cycle_count_variance', 'Variance found by a cycle count', 'count', 'Default code for a count correction once the recount is confirmed.', False),
        ('write_off', 'Stock written off', 'write_off', 'Approved write-off of unsaleable stock.', False),
        ('reclass', 'Stock moved between statuses or SKUs', 'reclass', 'Quality or status reclassification with no quantity change overall.', False),
        ('receiving_error', 'Error made at goods-in', 'receiving', 'Wrong SKU, wrong quantity keyed or put-away scan missed by our own receiving.', False),
        ('picking_error', 'Error made at picking', 'picking', 'Wrong bin scanned or short pick that the system did not record.', False),
        ('markdown', 'Stock relabelled for markdown', 'commercial', 'Relabelling for clearance; no stock loss.', False),
        ('sample', 'Units removed as samples', 'commercial', 'Photography, marketing or supplier samples.', False),
        ('theft', 'Suspected theft', 'loss', 'Only with a loss-prevention incident reference.', False),
        ('other', 'Catch-all when no other code fits', 'catch_all', 'Catch-all for adjustments that fit no other code. Should be rare and always carry a reason note; '
                                                                  'a high volume of other means the real cause is not being recorded.', True),
    ]
    cause_codes = [dict(cause_code=a, description=b, category=c, intended_use=d, catch_all=e) for a, b, c, d, e in cause_codes]

    # ------------------------------------------------------------------ pack specifications
    def upp_of(sku):
        return UPP.get(prod[sku]['category'], UPP_DEFAULT)

    affected = [p['sku'] for p in products if p['supplier_id'] == AFFECTED_SUPPLIER]
    pack_specs = []
    for i, p in enumerate(products):
        upp = upp_of(p['sku'])
        pr_ = g.rng_for('packspec', p['sku'])     # per-SKU stream: new master products never shift other rows
        units_per_pack = pr_.choice([1, 2, 4, 6, 10])
        row = {
            'pack_spec_id': f'PKS-{i + 1:06d}', 'sku': p['sku'], 'pack_type': p['pack_type'] or 'carton',
            'units_per_pack': units_per_pack, 'packs_per_pallet': max(1, upp // units_per_pack),
            'units_per_pallet': max(1, upp // units_per_pack) * units_per_pack,
            'pallet_height_cm': pr_.randint(120, 200), 'pallet_weight_kg': round(upp * float(p['weight_kg'] or 1) + 25, 1),
            'bonded_suitable': p['hazmat'] == 'none', 'created_at': T(D(pr_.randint(120, 400)), 10), 'updated_at': T(D(pr_.randint(60, 118)), 10),
        }
        if p['sku'] in affected:   # pack-spec sync the evening before the allocation failures
            row |= {'pack_type': 'polybag' if p['sku'] == 'PF-220' else 'carton', 'units_per_pack': 4, 'packs_per_pallet': 100 if p['sku'] in ('PF-220', 'K-1700') else max(1, upp // 4),
                    'units_per_pallet': 400 if p['sku'] in ('PF-220', 'K-1700') else max(1, upp // 4) * 4, 'updated_at': T(D(1), 21, 30)}
            if p['sku'] == 'PF-220':
                row |= {'pallet_height_cm': 160, 'pallet_weight_kg': 800}
        row['material'] = MATERIAL_OF.get(row['pack_type'], 'other')
        pack_specs.append(row)
    # packaging comparison story (small appliances, SKU-100532): same product in three pack materials, pallet fill as in packaging design
    base = next(x for x in pack_specs if x['sku'] == PACK_STORY_SKU)
    unit_kg = float(prod[PACK_STORY_SKU]['weight_kg'] or 1)
    alt = [  # (pack_spec_id, pack_type, material, units_per_pack, packs_per_pallet, height_cm, pack_kg)
        (base['pack_spec_id'], 'carton', 'corrugated', 5, 50, 150, 0.12),
        ('PKS-900101', 'tray', 'moulded_pulp', 4, 50, 165, 0.15),
        ('PKS-900102', 'pouch', 'recycled_plastic', 10, 40, 120, 0.05)]
    for spec_id, ptype, mat, upk, ppp, h, pk in alt:
        row = dict(base)
        row |= {'pack_spec_id': spec_id, 'pack_type': ptype, 'material': mat, 'units_per_pack': upk, 'packs_per_pallet': ppp,
                'units_per_pallet': upk * ppp, 'pallet_height_cm': h,
                'pallet_weight_kg': round(upk * ppp * (unit_kg + pk / upk) + 25, 1), 'updated_at': T(D(30), 10)}
        if spec_id == base['pack_spec_id']:
            base.update(row)
        else:
            pack_specs.append(row)

    # ------------------------------------------------------------------ location inventory (from master dc_stock)
    story_inv = [  # (location, sku, fraction of the SKU's on-hand held in that bin, or explicit qty)
        ('DC1-F-13-04', 'SKU-104739', 0.55), ('DC1-B-21-02', 'SKU-102380', 0.55), ('DC1-A-28-02', 'SKU-103556', 0.6),
        ('DC1-E-23-01', 'SKU-100805', 0.55), ('DC1-D-25-01', 'SKU-102968', 0.5), ('DC1-D-18-02', 'SKU-103129', 0.55),
        ('DC1-A-06-04', 'SKU-105887', 0.5), ('DC1-C-06-01', 'SKU-103682', 0.45), ('DC1-G-09-02', 'SKU-101379', 0.012),
        ('DC1-C-14-01', 'SKU-100028', 60), ('DC1-C-14-02', 'SKU-100084', 124),
        ('DC1-C-14-03', 'SKU-101113', 180), ('DC1-C-14-04', 'SKU-100007', 95),
        ('DC1-C-14-01', 'SKU-100007', 40),
    ]
    stock_by = {(d['sku'], d['site_id']): int(d['on_hand']) for d in dc_stock}
    inventory = []   # dicts without stock_id
    fixed = {}       # (sku, site) -> qty already placed by story rows
    story_locs = set()
    for lid, sku, q in story_inv:
        site = loc[lid]['site_id']
        qty = int(round(stock_by[(sku, site)] * q)) if isinstance(q, float) else q
        if lid == 'DC1-G-09-02':
            qty = max(qty, 60)
        inventory.append({'location_id': lid, 'site_id': site, 'sku': sku, 'qty': qty, 'status': 'on-hand'})
        fixed[(sku, site)] = fixed.get((sku, site), 0) + qty
        story_locs.add(lid)
    # status story: stock on hold at DC1 that WMS excludes from available but ERP still counts
    for sku, site, qty, status, lid in [('SKU-100007', 'DC1', 150, 'quarantine', 'DC1-L-02-03')]:
        inventory.append({'location_id': lid, 'site_id': site, 'sku': sku, 'qty': qty, 'status': status})
        fixed[(sku, site)] = fixed.get((sku, site), 0) + qty
        story_locs.add(lid)

    DEPT_ZONES = {'Womenswear': ['pick', 'pick', 'mezzanine', 'reserve'], 'Menswear': ['pick', 'pick', 'mezzanine', 'reserve'],
                  'Kids': ['pick', 'reserve', 'mezzanine'], 'Accessories': ['mezzanine', 'pick', 'reserve'],
                  'Beauty': ['pick', 'reserve', 'mezzanine'], 'Home': ['bulk', 'bulk', 'reserve'],
                  'Electricals': ['reserve', 'reserve', 'mezzanine', 'pick']}
    for site in DCS:
        active = [l for l in locations if l['site_id'] == site and l['status'] == 'active' and l['location_id'] not in story_locs]
        pallet = [l for l in active if l['location_type'] in PALLET_TYPES]
        pickf = [l for l in active if l['location_type'] == 'pick_face']
        zones = {}
        for l in pallet:
            zones.setdefault(l['zone'], []).append(l['location_id'])
        frac = {'bulk': 0.95, 'reserve': 0.94, 'pick': 0.92, 'mezzanine': 0.88, 'hazmat': 0.90} if site == 'DC1' else {}
        for zname, z in zones.items():
            r.shuffle(z)
            del z[int(len(z) * frac.get(zname, 0.78)):]
        zone_size = {zn: max(1, len(q)) for zn, q in zones.items()}
        used = []
        pick_pool = [l['location_id'] for l in pickf]
        r.shuffle(pick_pool)
        rows = [(d['sku'], int(d['on_hand']) - fixed.get((d['sku'], site), 0)) for d in dc_stock if d['site_id'] == site]
        rows = [(s, q) for s, q in rows if q > 0]
        target = sum(len(z) for z in zones.values())

        def n_for(s, q, scale):
            cap = math.ceil(q * 0.94 * cost[s] / 48000) if site == 'DC1' else 1
            return max(1, math.ceil(q * 0.94 / (upp_of(s) * scale)), cap)

        def needed(scale):
            return sum(n_for(s, q, scale) for s, q in rows)
        lo, hi = 0.2, 60.0
        for _ in range(60):
            mid = (lo + hi) / 2
            if needed(mid) > target:
                lo = mid
            else:
                hi = mid
        scale = hi
        for sku, qty in sorted(rows, key=lambda x: -x[1] * cost[x[0]]):
            p = prod[sku]
            pick_share = 0.06 if p['abc_class'] in ('A', 'B') and pick_pool else 0
            pq = int(qty * pick_share)
            k = 1 if pq < 80 else 2
            if pq >= 6 and len(pick_pool) >= k:
                for part in _split(r, pq, k):
                    inventory.append({'location_id': pick_pool.pop(), 'site_id': site, 'sku': sku, 'qty': part, 'status': 'on-hand'})
                qty -= pq
            n = n_for(sku, qty, scale)
            if p['hazmat'] != 'none' and zones.get('hazmat'):
                prefs = ['hazmat']
            else:
                prefs = [z for z in DEPT_ZONES.get(p['department'], ['reserve']) if z in zones] or [z for z in zones if z != 'hazmat']
            for part in _even_split(r, qty, n):
                z = None
                for cand in [r.choice(prefs)] + prefs:
                    if zones.get(cand):
                        z = cand
                        break
                if z is None and not any(zones.values()):
                    z = None
                elif z is None:       # spill into the zone with the most room left
                    room = [(len(q) / zone_size[zn], zn) for zn, q in zones.items() if q and (zn != 'hazmat' or p['hazmat'] != 'none')]
                    z = max(room)[1] if room else None
                if z is None:
                    lid = pick_pool.pop() if pick_pool else r.choice(used)
                else:
                    lid = zones[z].pop()
                    used.append(lid)
                inventory.append({'location_id': lid, 'site_id': site, 'sku': sku, 'qty': part, 'status': 'on-hand'})
    # a little stock in damaged / expired status taken out of normal rows
    for row in r.sample([x for x in inventory if x['location_id'] not in story_locs and x['qty'] > 40], 60):
        move = max(1, int(row['qty'] * r.uniform(0.02, 0.08)))
        row['qty'] -= move
        inventory.append({'location_id': row['location_id'], 'site_id': row['site_id'], 'sku': row['sku'], 'qty': move,
                          'status': r.choice(['damaged', 'damaged', 'expired'])})
    location_inventory = []
    for i, row in enumerate(inventory):
        location_inventory.append({'stock_id': f'LI-{i + 1:06d}', 'location_id': row['location_id'], 'site_id': row['site_id'], 'sku': row['sku'],
                                   'lot_number': f'LOT-{r.randint(1000, 9999)}' if r.random() < 0.4 else '', 'status': row['status'],
                                   'qty': row['qty'], 'updated_at': T(D(r.randint(0, 20)), r.randint(6, 20), r.randint(0, 59))})
    # network story (03:31:Q4): Leeds (DC3) is underused. Consolidate three in ten of its occupied bins into neighbouring bins in the
    # same zone (no random draws, same stock), so occupancy falls well below the other DCs.
    for zname in sorted({loc[x['location_id']]['zone'] for x in location_inventory if x['site_id'] == 'DC3'}):
        zlocs = sorted({x['location_id'] for x in location_inventory if x['site_id'] == 'DC3' and loc[x['location_id']]['zone'] == zname})
        keep = [l for i, l in enumerate(zlocs) if i % 10 > 2]
        move = {l: keep[i % len(keep)] for i, l in enumerate([l for i, l in enumerate(zlocs) if i % 10 <= 2])} if keep else {}
        for x in location_inventory:
            if x['site_id'] == 'DC3' and x['location_id'] in move:
                x['location_id'] = move[x['location_id']]
    # status story (01:8:Q4): a quality hold put about £1.05m of DC1 and DC3 stock into quarantine; WMS leaves it out of
    # available stock but ERP still counts it. Uses its own random stream so nothing else in the data moves.
    qr = random.Random(8044)
    # The 15 holds are fixed lines (qms quotes 16 active holds, 24,488 units, GBP 1,054,351 with the DC1 SKU-100007 hold above), so the
    # story does not move when the random bin layout does. Each hold comes out of the SKU's largest bin at that DC.
    for site, sku, move in QUALITY_HOLDS:
        cands = sorted([x for x in location_inventory if x['status'] == 'on-hand' and x['site_id'] == site and x['sku'] == sku
                        and x['location_id'] not in story_locs], key=lambda x: (-x['qty'], x['stock_id']))
        left = move
        for x in cands:
            take = min(x['qty'], left)
            if take <= 0:
                continue
            left -= take
            x['qty'] -= take
            location_inventory.append({'stock_id': f'LI-{len(location_inventory) + 1:06d}', 'location_id': x['location_id'], 'site_id': x['site_id'],
                                       'sku': x['sku'], 'lot_number': f'LOT-QH-{qr.randint(100, 999)}', 'status': 'quarantine', 'qty': take,
                                       'updated_at': T(D(qr.randint(2, 4)), qr.randint(8, 17), qr.randint(0, 59))})
            if left <= 0:
                break
        assert left <= 0, (site, sku, left)
    inv_by_loc = {}
    for row in location_inventory:
        inv_by_loc.setdefault(row['location_id'], []).append(row)

    # pallet position history (weekly): current counts from the inventory, earlier weeks scaled back by category growth
    cur = {}
    for row in location_inventory:
        l = loc[row['location_id']]
        if l['location_type'] in PALLET_TYPES:
            cur.setdefault((row['site_id'], l['zone'], prod[row['sku']]['category']), set()).add(row['location_id'])
    last_monday = as_of - timedelta(days=as_of.weekday())
    history = []
    cat_total = {}
    for (site, zone, cat), locs in cur.items():
        cat_total[(site, cat)] = cat_total.get((site, cat), 0) + len(locs)
    for (site, zone, cat), locs in sorted(cur.items()):
        c = len(locs)
        g_cat = GROWTH_DC1.get(cat, 0.0) if site == 'DC1' else 0.15 * c / max(1, cat_total[(site, cat)])
        g_zone = g_cat * c / cat_total[(site, cat)]
        for w in range(0, 13):
            history.append({'week_start': last_monday - timedelta(weeks=w), 'site_id': site, 'zone': zone, 'category': cat,
                            'positions_occupied': max(0, int(round(c - g_zone * w)))})

    # ------------------------------------------------------------------ goods receipts
    receipts = []
    clerk_cycle = {s: 0 for s in DCS}
    for po_id, po in pos.items():
        if po['status'] not in ('received', 'closed') or po['dest_site_id'] not in DCS:
            continue
        sh = ships.get(po_id)
        day = (sh['ata'] if sh and sh['ata'] else po['due_date'])
        day = datetime.fromisoformat(day).date()
        if not (D(100) <= day <= D(1)):
            continue
        for ln in [x for x in po_lines if x['po_id'] == po_id]:
            ordered, got = int(ln['qty_ordered']), int(ln['qty_received'])
            if (po_id, ln['sku']) in STORY_RECEIPT_POS or got <= 0:
                continue
            if abs(got / ordered - 1) > 0.03:     # large master variances are not part of this DC's receipts
                continue
            site = po['dest_site_id']
            clerk = clerks[site][clerk_cycle[site] % len(clerks[site])] if clerks[site] else 'EMP-00001'
            clerk_cycle[site] += 1
            dmg = r.randint(1, max(1, got // 200)) if r.random() < 0.07 else 0
            when = T(day, r.randint(6, 19), r.randint(0, 59))
            receipts.append({
                'receipt_id': f'GR-{len(receipts) + 1:06d}', 'po_id': po_id, 'site_id': site, 'sku': ln['sku'],
                'qty_ordered': ordered, 'qty_received': got, 'qty_accepted': got - dmg, 'received_at': when, 'received_by': clerk,
                'dock': f'D{r.randint(1, 12):02d}', 'carrier_id': sh['carrier_id'] if sh else 'CAR-001',
                'batch_number': f'BTH-{day.year}-{r.randint(1000, 9999)}' if r.random() < 0.4 else '',
                'expiry_date': None, 'damage_qty': dmg, 'short_qty': max(0, ordered - got), 'updated_at': when, 'notes': ''})
    pick_loc_of = {}
    for row in location_inventory:
        if loc[row['location_id']]['location_type'] == 'pick_face' and row['status'] == 'on-hand':
            pick_loc_of.setdefault((row['site_id'], row['sku']), row['location_id'])
    # WMS 9.2 duplicate-task story: pairs of DC1 receipts landing within 5 seconds
    dc1 = sorted([x for x in receipts if x['site_id'] == 'DC1' and D(66) <= x['received_at'].date() <= D(9)], key=lambda x: x['received_at'])
    dup_pairs = []
    used = set()
    for k in range(12):
        cand = [x for x in dc1 if x['receipt_id'] not in used]
        cand_a = [x for x in cand if ('DC1', x['sku']) in pick_loc_of]
        if len(cand_a) < 1:
            break
        a = cand_a[(k * 7) % len(cand_a)]
        pool = [x for x in cand if x['receipt_id'] != a['receipt_id'] and x['sku'] != a['sku']]
        b = pool[(k * 5 + 3) % len(pool)]
        b['received_at'] = a['received_at'] + timedelta(seconds=r.randint(2, 4))
        b['updated_at'] = b['received_at']
        used |= {a['receipt_id'], b['receipt_id']}
        dup_pairs.append((a, b))

    # ------------------------------------------------------------------ replenishment tasks
    repl = []
    for x in receipts:
        if x['received_at'].date() < D(66):
            continue
        to_loc = pick_loc_of.get((x['site_id'], x['sku']))
        if not to_loc:
            continue
        repl.append({'task_id': f'RPL-{len(repl) + 1:06d}', 'site_id': x['site_id'], 'sku': x['sku'], 'to_location_id': to_loc,
                     'qty': max(10, min(x['qty_received'] // 20, 400)), 'status': 'completed',
                     'created_at': x['received_at'] + timedelta(seconds=r.randint(30, 90)), 'trigger_receipt_id': x['receipt_id'],
                     'created_by': 'WMS-AUTO'})
    by_receipt = {t['trigger_receipt_id']: t for t in repl}
    for a, b in dup_pairs:
        t1 = by_receipt.get(a['receipt_id'])
        if not t1:
            continue
        repl.append({'task_id': f'RPL-{len(repl) + 1:06d}', 'site_id': 'DC1', 'sku': t1['sku'], 'to_location_id': t1['to_location_id'],
                     'qty': t1['qty'], 'status': 'completed', 'created_at': b['received_at'] + timedelta(seconds=r.randint(30, 90)),
                     'trigger_receipt_id': b['receipt_id'], 'created_by': 'WMS-AUTO'})
        # duplicate created within 5 seconds of the first task
        repl[-1]['created_at'] = t1['created_at'] + timedelta(seconds=r.randint(2, 4))

    # ------------------------------------------------------------------ order lines (from master orders)
    stocked = {s: [d['sku'] for d in dc_stock if d['site_id'] == s and d['sku'] not in affected] for s in DCS}
    affected_at = {s: [d['sku'] for d in dc_stock if d['site_id'] == s and d['sku'] in affected] for s in DCS}
    zone_of = {}
    for row in location_inventory:
        if row['status'] == 'on-hand':
            zone_of.setdefault((row['site_id'], row['sku']), []).append(loc[row['location_id']]['zone'])
    PICK_W = [0, 0, 0, 0, 0, 0, 1, 2, 3, 4, 5, 5, 5, 6, 7, 8, 8, 7, 5, 3, 2, 1, 0, 0]
    ch_w = {'web': [1, 1, 1, 1, 1, 1, 2, 3, 4, 6, 7, 7, 7, 6, 5, 4, 4, 5, 7, 7, 6, 5, 3, 2],
            'app': [1, 1, 1, 1, 1, 1, 2, 3, 4, 5, 6, 6, 6, 5, 5, 4, 4, 5, 7, 7, 6, 5, 3, 2]}
    start = D(77)
    elig = [o for o in master_orders if o['status'] != 'cancelled' and datetime.fromisoformat(o['order_date']).date() >= start
            and o['fulfil_site_id'] in DCS]
    elig.sort(key=lambda o: o['order_id'])
    placed = [o for o in elig if o['status'] == 'placed' and o['order_date'] >= str(D(5))]
    fail_ids = {}
    dc2_p = [o for o in placed if o['fulfil_site_id'] == 'DC2']
    dc1_p = [o for o in placed if o['fulfil_site_id'] == 'DC1']
    r.shuffle(dc2_p)
    r.shuffle(dc1_p)
    chosen = dc2_p[:125] + dc1_p[:15]
    for i, o in enumerate(chosen):
        fail_ids[o['order_id']] = 'LOCATION_BLOCKED' if i % 17 == 16 else 'PACK_UOM_MISMATCH'
    order_lines = []
    pack_spec_id = {ps['sku']: ps['pack_spec_id'] for ps in pack_specs}
    story_pairs = _pairs(r, products, dc_stock)
    dc1_multi = []
    historic_aff = 0
    for o in elig:
        site, day = o['fulfil_site_id'], datetime.fromisoformat(o['order_date']).date()
        units = int(o['units'])
        n_lines = 1 if units == 1 else min(units, r.choices([1, 2, 3], [0.45, 0.4, 0.15])[0])
        qtys = _split(r, units, n_lines)
        failing = fail_ids.get(o['order_id'])
        skus = r.sample(stocked[site], n_lines)
        if failing == 'PACK_UOM_MISMATCH' and affected_at[site]:
            w = [3 if s in ('PF-220', 'K-1700') else 1 for s in affected_at[site]]
            skus[0] = r.choices(affected_at[site], w)[0]
            if qtys[0] % 4 == 0:
                qtys[0] += 1
        elif o['status'] in ('delivered', 'returned', 'part_returned', 'shipped') and day < D(8) and affected_at[site] and r.random() < 0.012:
            skus[0] = r.choice(affected_at[site])      # these SKUs allocated fine before the change
        if site == 'DC1' and n_lines >= 2 and o['status'] != 'placed' and day <= D(8) and story_pairs:
            dc1_multi.append(len(order_lines))
        status_o = {'delivered': 'shipped', 'returned': 'shipped', 'part_returned': 'shipped', 'shipped': 'shipped',
                    'picking': 'picking', 'placed': 'allocated'}[o['status']]
        pick_h = r.choices(range(24), PICK_W)[0]
        if status_o == 'shipped' or status_o == 'picking':
            picked = T(day, pick_h, r.randint(0, 59))
            released = picked - timedelta(minutes=r.randint(40, 150))
            shipped = (picked + timedelta(hours=r.randint(2, 5))) if status_o == 'shipped' else None
            if status_o == 'picking':
                picked = None
        else:
            picked, shipped, released = None, None, None
        for i in range(n_lines):
            sku = skus[i]
            line = {'order_id': o['order_id'], 'line_no': i + 1, 'site_id': site, 'sku': sku, 'qty': qtys[i], 'status': status_o,
                    'status_at': shipped or picked or released or T(day, 12), 'failure_code': '', 'failure_detail': '',
                    'pick_zone': r.choice(zone_of.get((site, sku), ['pick'])), 'released_at': released, 'picked_at': picked,
                    'shipped_at': shipped, 'updated_at': shipped or picked or released or T(day, 12)}
            if failing and i == 0:
                line['status'] = 'allocation_failed'
                line['status_at'] = line['updated_at'] = T(D(0), 6, r.randint(0, 3), r.randint(0, 59))
                line['released_at'] = line['status_at']
                if failing == 'PACK_UOM_MISMATCH':
                    line['failure_code'] = 'PACK_UOM_MISMATCH'
                    line['failure_detail'] = (f"Line qty {qtys[0]} is not a whole inner pack of 4 (pack spec {pack_spec_id[sku]} "
                                              f"changed yesterday 21:30); each-level allocation refused")
                else:
                    blocked = r.choice([l['location_id'] for l in locations if l['site_id'] == site and l['status'] == 'blocked'])
                    line['failure_code'] = 'LOCATION_BLOCKED'
                    line['failure_detail'] = f'Only pick face {blocked} is blocked; no alternative location with stock'
            order_lines.append(line)
    # co-pick story: planted SKU pairs in DC1 multi-line orders (already shipped)
    if story_pairs:
        slots = [i for i in dc1_multi if order_lines[i]['line_no'] == 1 and order_lines[i + 1]['order_id'] == order_lines[i]['order_id']]
        r.shuffle(slots)
        k = 0
        for (a, b), count in story_pairs:
            for _ in range(count):
                if k >= len(slots):
                    break
                i = slots[k]
                k += 1
                order_lines[i]['sku'], order_lines[i + 1]['sku'] = a, b
                order_lines[i]['pick_zone'] = order_lines[i + 1]['pick_zone'] = 'pick'

    # DC1 pick hours: schedule orders so every hour gets the same mix of one-, two- and three-line orders
    first_of = {}
    for i, ln in enumerate(order_lines):
        first_of.setdefault(ln['order_id'], []).append(i)
    dc1_orders = sorted({ln['order_id'] for ln in order_lines if ln['site_id'] == 'DC1' and ln['picked_at'] is not None},
                        key=lambda oid: (order_lines[first_of[oid][0]]['picked_at'].date(), oid))
    wsum = sum(PICK_W)
    assigned, totals = {}, {}
    for oid in dc1_orders:
        k = len(first_of[oid])
        totals[k] = totals.get(k, 0) + 1
        best = max((h for h in range(24) if PICK_W[h]),
                   key=lambda h: totals[k] * PICK_W[h] / wsum - assigned.get((k, h), 0) + r.random() * 0.01)
        assigned[(k, best)] = assigned.get((k, best), 0) + 1
        base = T(order_lines[first_of[oid][0]]['picked_at'].date(), best, r.randint(0, 59))
        for j in first_of[oid]:
            ln = order_lines[j]
            delta_ship = ln['shipped_at'] - ln['picked_at'] if ln['shipped_at'] else None
            delta_rel = ln['picked_at'] - ln['released_at']
            ln['picked_at'] = base
            ln['released_at'] = base - delta_rel
            ln['shipped_at'] = base + delta_ship if delta_ship is not None else None
            ln['status_at'] = ln['shipped_at'] or base
            ln['updated_at'] = ln['status_at']

    # lines behind the bay C-14 ledger: DC1 single-line shipped orders re-pointed at the bay's SKUs
    single = [i for i, ln in enumerate(order_lines)
              if ln['site_id'] == 'DC1' and ln['status'] == 'shipped' and ln['line_no'] == 1 and ln['qty'] >= 2 and ln['sku'] not in affected
              and (i + 1 >= len(order_lines) or order_lines[i + 1]['order_id'] != ln['order_id']) and D(84) <= ln['picked_at'].date() <= D(4)]
    r.shuffle(single)
    planted = {}
    for sku, lid, n in [('SKU-100084', 'DC1-C-14-02', 26), ('SKU-100028', 'DC1-C-14-01', 5), ('SKU-100007', 'DC1-C-14-01', 3),
                        ('SKU-101113', 'DC1-C-14-03', 6), ('SKU-100007', 'DC1-C-14-04', 4)]:
        idxs = [single.pop() for _ in range(n)]
        for i in idxs:
            order_lines[i]['sku'] = sku
            order_lines[i]['pick_zone'] = 'pick'
        planted[(sku, lid)] = idxs

    # ------------------------------------------------------------------ stock transfers (rebalancing between DCs)
    transfers = []
    for i in range(r.randint(100, 160)):
        frm = r.choice(DCS)
        to = r.choice([d for d in DCS if d != frm])
        created = D(r.randint(1, 90))
        sc = r.random()
        status = 'draft' if sc < 0.2 else 'confirmed' if sc < 0.4 else 'allocated' if sc < 0.6 else 'shipped' if sc < 0.8 else 'received'
        qty = r.randint(50, 1000)
        transfers.append({
            'transfer_id': f'STR-{len(transfers) + 1:06d}', 'from_site_id': frm, 'to_site_id': to, 'sku': r.choice(stocked[frm]),
            'qty_requested': qty, 'qty_allocated': qty if status != 'draft' else 0,
            'qty_shipped': qty if status in ('shipped', 'received') else 0, 'qty_received': qty if status == 'received' else 0,
            'created_at': T(created, 10), 'shipped_at': T(created + timedelta(days=2), 14) if status in ('shipped', 'received') else None,
            'received_at': T(created + timedelta(days=5), 9) if status == 'received' else None, 'status': status,
            'reason': r.choice(['rebalance', 'stockout', 'clearance', 'outlet']), 'created_by': r.choice(controllers[frm] or ['EMP-00112']),
            'updated_at': T(created, 10)})

    # ------------------------------------------------------------------ stock movements (ledger)
    movements = []

    def mov(location, site, sku, typ, qty, ref, when, by, batch='', notes='', status='completed'):
        movements.append({'movement_id': f'MOV-{len(movements) + 1:06d}', 'location_id': location, 'site_id': site, 'sku': sku,
                          'movement_type': typ, 'qty': qty, 'reference_id': ref, 'moved_at': when, 'moved_by': by,
                          'batch_number': batch, 'status': status, 'updated_at': when, 'notes': notes})

    stock_loc = {}
    for row in location_inventory:
        if row['status'] == 'on-hand' and row['location_id'] not in story_locs:
            stock_loc.setdefault((row['site_id'], row['sku']), []).append(row['location_id'])
    pickers = {s: emps(s, 'Picker/Packer') or ['EMP-00103'] for s in DCS}
    for x in receipts:
        locs = stock_loc.get((x['site_id'], x['sku']))
        if not locs or x['received_at'].date() < D(66):
            continue
        mov(r.choice(locs), x['site_id'], x['sku'], 'receipt', x['qty_received'], x['receipt_id'], x['received_at'], x['received_by'], x['batch_number'])
    for ln in order_lines:                      # every shipped line is a pick from a bin that holds the SKU
        if ln['status'] != 'shipped' or ln['picked_at'].date() < D(60):
            continue
        locs = stock_loc.get((ln['site_id'], ln['sku']))
        if locs:
            mov(r.choice(locs), ln['site_id'], ln['sku'], 'pick', -ln['qty'], ln['order_id'], ln['picked_at'], r.choice(pickers[ln['site_id']]))
    for t in transfers:
        if t['status'] in ('shipped', 'received'):
            locs = stock_loc.get((t['from_site_id'], t['sku']))
            if locs:
                mov(r.choice(locs), t['from_site_id'], t['sku'], 'transfer', -t['qty_shipped'], t['transfer_id'], t['shipped_at'], t['created_by'])
    # story bay C-14: the 90-day history behind the Tuesday count (SKU-100084 in DC1-C-14-02 nets to 124 system units)
    emp_a, emp_b = 'EMP-00112', 'EMP-00116'
    c142 = 'DC1-C-14-02'
    for (sku, lid), idxs in planted.items():
        for i in idxs:
            ln = order_lines[i]
            mov(lid, 'DC1', sku, 'pick', -ln['qty'], ln['order_id'], ln['picked_at'], r.choice(pickers['DC1']))
    picked_c142 = sum(order_lines[i]['qty'] for i in planted[('SKU-100084', c142)])
    story = [
        (D(88), 7, 30, 'receipt', 150, 'GR-901001', emp_a, ''),
        (D(87), 9, 10, 'adjustment', 36, 'INV-ADJ-900001', emp_a, 'Received 36 over ASN, put away to C-14-02'),
        (D(70), 14, 30, 'adjustment', -12, 'INV-ADJ-900002', emp_a, 'Pick short, wrong bin scanned'),
        (D(55), 15, 5, 'adjustment', -18, 'INV-ADJ-900003', emp_a, 'Pick short from C-14-02, wrong bin scanned'),
        (D(40), 7, 40, 'adjustment', 30, 'INV-ADJ-900004', emp_a, 'Put-away to C-14-02 not scanned'),
        (D(26), 16, 20, 'adjustment', -15, 'INV-ADJ-900005', emp_a, 'Picked from C-14-02 against C-14-01 label'),
    ]
    net = sum(q for _, _, _, _, q, _, _, _ in story) - picked_c142
    story.append((D(82), 8, 0, 'receipt', 124 - net, 'GR-901002', emp_a, ''))
    assert 124 - net > 0, (net, picked_c142)
    for d_, h, m, typ, q, ref, by, note in story:
        mov(c142, 'DC1', 'SKU-100084', typ, q, ref, T(d_, h, m), by, '', note)
    # other bins in the bay: ordinary receipts and picks that net to the bin quantity
    for (sku, lid), idxs in planted.items():
        if lid == c142:
            continue
        target = {('SKU-100028', 'DC1-C-14-01'): 60, ('SKU-100007', 'DC1-C-14-01'): 40, ('SKU-101113', 'DC1-C-14-03'): 180,
                  ('SKU-100007', 'DC1-C-14-04'): 95}[(sku, lid)]
        mov(lid, 'DC1', sku, 'receipt', target + sum(order_lines[i]['qty'] for i in idxs), f'GR-{r.randint(902000, 902999)}',
            T(D(88), 8, 15), emp_a)

    # ------------------------------------------------------------------ cycle counts
    tasks, results = [], []

    def add_visit(lid, site, when, counter, rows, issue_pct, status='completed', reason='Cycle count'):
        tid = f'CCT-{len(tasks) + 1:06d}'
        tasks.append({'task_id': tid, 'location_id': lid, 'site_id': site, 'status': status, 'assigned_to': counter,
                      'created_at': when - timedelta(days=r.randint(1, 4), hours=2), 'released_at': when - timedelta(hours=r.randint(1, 18)),
                      'completed_at': when, 'cancelled_at': None, 'cancel_reason': '', 'reason': reason, 'priority': r.randint(20, 70), 'updated_at': when})
        for row in rows:
            sys_q = max(5, int(row['qty'] * r.uniform(0.85, 1.15)))
            issue = r.random() * 100 < issue_pct
            pct = (r.uniform(2.5, 9.0) * r.choice([-1, -1, 1])) if issue else r.choice([0, 0, 0, 0.4, -0.4, 0.8, -0.8, 1.2, -1.2])
            var = int(round(sys_q * pct / 100))
            if issue and var == 0:
                var = -1 if pct < 0 else 1
            counted = sys_q + var
            rev = False
            rev_at = None
            val = abs(var) * cost[row['sku']]
            if var != 0 and val < 400 and r.random() < 0.05:
                rev, rev_at = True, when + timedelta(hours=r.randint(3, 40))
            results.append({'result_id': f'CCR-{len(results) + 1:06d}', 'task_id': tid, 'location_id': lid, 'sku': row['sku'],
                            'system_qty': sys_q, 'counted_qty': counted, 'variance': var,
                            'variance_pct': round(var / sys_q * 100, 2), 'counted_at': when, 'counted_by': counter,
                            'accuracy_issue': abs(var / sys_q * 100) >= 2.0, 'reversed_within_48h': rev, 'reversed_at': rev_at,
                            'cause_code': 'cycle_count_variance' if var != 0 else '', 'lot_number': row['lot_number'],
                            'condition': r.choice(['good'] * 8 + ['damaged', 'expired']), 'updated_at': when})
        return tid

    def hour_for(counter):
        sh = shift_of.get(counter, 'early')
        return {'early': r.randint(7, 12), 'late': r.randint(14, 20), 'night': r.choice([22, 23, 0, 1, 2, 3])}[sh]

    protected = story_locs | {'DC1-A-03-01', 'DC1-A-03-02', 'DC1-B-02-01'}
    for site in DCS:
        blocks = 4 if site == 'DC1' else 2
        prob = 0.34 if site == 'DC1' else 0.17
        for lid, rows in inv_by_loc.items():
            if loc[lid]['site_id'] != site or lid in protected or loc[lid]['status'] != 'active':
                continue
            rows = [x for x in rows if x['status'] == 'on-hand'][:3] or []
            if not rows:
                continue
            zone = loc[lid]['zone']
            for k in range(blocks):
                if r.random() > (0.62 if site == 'DC1' and zone == 'pick' else prob):
                    continue
                if k == 0:
                    age = r.choice(list(range(3, 23)) + list(range(38, 81)))
                else:
                    age = 91 * k + r.randint(2, 80)
                counter = r.choice(controllers[site] or ['EMP-00112'])
                when = T(D(age), hour_for(counter), r.randint(0, 59))
                rate = ISSUE_RATE_DC1[zone][k] if site == 'DC1' and zone in ISSUE_RATE_DC1 else 4.0 + r.uniform(-0.8, 0.8)
                add_visit(lid, site, when, counter, rows, rate)

    # ---- story: bay C-14 Tuesday count (6 days before as_of at 11:00) and two earlier counts of the bay
    def story_result(task, lid, sku, sys_q, counted, when, counter, cause='cycle_count_variance', lot=''):
        var = counted - sys_q
        results.append({'result_id': f'CCR-9{len([x for x in results if x["result_id"].startswith("CCR-9")]) + 1:05d}', 'task_id': task,
                        'location_id': lid, 'sku': sku, 'system_qty': sys_q, 'counted_qty': counted, 'variance': var,
                        'variance_pct': round(var / sys_q * 100, 2), 'counted_at': when, 'counted_by': counter,
                        'accuracy_issue': abs(var / sys_q * 100) >= 2.0, 'reversed_within_48h': False, 'reversed_at': None,
                        'cause_code': cause if var else '', 'lot_number': lot, 'condition': 'good', 'updated_at': when})

    def story_task(tid, lid, when, counter, status='completed', reason='Cycle count', priority=50, created=None, released='auto'):
        tasks.append({'task_id': tid, 'location_id': lid, 'site_id': 'DC1', 'status': status, 'assigned_to': counter,
                      'created_at': created or when - timedelta(days=3), 'released_at': when - timedelta(hours=20) if released == 'auto' else released,
                      'completed_at': when if status == 'completed' else None, 'cancelled_at': None, 'cancel_reason': '', 'reason': reason,
                      'priority': priority, 'updated_at': when})

    tue = T(D(6), 11, 0)
    story_task('CCT-900001', 'DC1-C-14-02', tue, emp_a, reason='Regular bay count', priority=60)
    story_task('CCT-900002', 'DC1-C-14-01', tue + timedelta(minutes=10), emp_a, reason='Regular bay count', priority=60)
    story_task('CCT-900003', 'DC1-C-14-03', tue + timedelta(minutes=20), emp_a, reason='Regular bay count', priority=60)
    story_task('CCT-900004', 'DC1-C-14-04', tue + timedelta(minutes=30), emp_a, reason='Regular bay count', priority=60)
    story_result('CCT-900001', 'DC1-C-14-02', 'SKU-100084', 124, 100, tue, emp_a, lot='LOT-4471')
    story_result('CCT-900002', 'DC1-C-14-01', 'SKU-100028', 60, 57, tue + timedelta(minutes=10), emp_a)
    story_result('CCT-900002', 'DC1-C-14-01', 'SKU-100007', 40, 40, tue + timedelta(minutes=10), emp_a)
    story_result('CCT-900003', 'DC1-C-14-03', 'SKU-101113', 180, 180, tue + timedelta(minutes=20), emp_a)
    story_result('CCT-900004', 'DC1-C-14-04', 'SKU-100007', 95, 95, tue + timedelta(minutes=30), emp_a)
    for tid, age, sysq, cnt in (('CCT-900005', 60, 188, 186), ('CCT-900006', 33, 171, 163)):
        story_task(tid, 'DC1-C-14-02', T(D(age), 10, 30), emp_b, reason='Weekly cycle count')
        story_result(tid, 'DC1-C-14-02', 'SKU-100084', sysq, cnt, T(D(age), 10, 30), emp_b)

    # ---- story: count priority at DC1 (value high, accuracy poor, not counted for 50+ days) plus decoys
    prio = [  # (location, planned task, assigned, [(age_days, issue?)])
        ('DC1-F-13-04', 'CCT-900101', 'EMP-00116', [(52, True), (66, True), (80, False)]),
        ('DC1-B-21-02', 'CCT-900102', 'EMP-00116', [(55, True), (70, True), (78, False)]),
        ('DC1-A-28-02', 'CCT-900103', 'EMP-00112', [(58, True), (74, False), (80, True)]),
        ('DC1-E-23-01', 'CCT-900104', 'EMP-00112', [(61, True), (77, True)]),
        ('DC1-D-25-01', 'CCT-900105', 'EMP-00116', [(64, True), (79, False), (72, True)]),
        ('DC1-D-18-02', 'CCT-900106', 'EMP-00116', [(67, True), (80, True)]),
        ('DC1-A-06-04', None, None, [(11, True), (45, True), (62, True)]),      # high value, poor history, but counted recently
        ('DC1-C-06-01', None, None, [(48, False), (63, False), (79, False)]),   # high value, clean history
        ('DC1-G-09-02', None, None, [(53, True), (65, True), (76, True)]),      # poor history, small value
    ]
    seq = [0]
    for lid, planned, who, hist in prio:
        row = [x for x in inv_by_loc[lid] if x['status'] == 'on-hand'][0]
        for j, (age, issue) in enumerate(hist):
            tid = f'CCT-9002{seq[0]:03d}'
            seq[0] += 1
            counter = r.choice(controllers['DC1'][:6])
            when = T(D(age), hour_for(counter) % 24, r.randint(0, 59))
            story_task(tid, lid, when, counter, reason='Cycle count')
            sysq = max(60, int(row['qty'] * r.uniform(0.9, 1.1)))
            var = int(round(sysq * (r.choice([-1, 1]) * r.uniform(3.0, 8.0) / 100))) if issue else r.choice([0, 1, -1])
            story_result(tid, lid, row['sku'], sysq, sysq + var, when, counter)
        if planned:
            story_task(planned, lid, T(D(0), 7), who, status='planned', reason='Priority count: high value, poor accuracy history',
                       priority=60, created=T(D(1), 15), released=None)
    # a couple of other planned/released tasks at DC1 as background
    for i, lid in enumerate(['DC1-H-05-02', 'DC1-K-10-03', 'DC1-L-12-01']):
        story_task(f'CCT-9003{i:02d}', lid, T(D(1), 9), 'EMP-00136', status='planned' if i < 2 else 'released', reason='Scheduled cycle count',
                   priority=30, created=T(D(2), 10), released=None if i < 2 else T(D(1), 7))
    # a released one that the question can cancel
    # ---- story: Q3 adjustments mirrored from IMS (cycle count corrections over 500 pounds)
    mirror = [  # (age_days, hour, loc, sku, variance, counter, reversed_hours)
        (D(80), 9, 'DC1-A-03-01', 'SKU-102338', -20, 'EMP-00112', 30),
        (D(58), 9, 'DC1-A-03-02', 'SKU-101834', -48, 'EMP-00112', 30),
        (D(36), 9, 'DC1-B-02-01', 'SKU-105341', -14, 'EMP-00112', 30),
    ]
    for i, (day, h, lid, sku, var, counter, rev_h) in enumerate(mirror):
        tid = f'CCT-9004{i:02d}'
        when = T(day, h, 0)
        story_task(tid, lid, when, counter, reason='Weekly cycle count')
        sysq = 400
        results.append({'result_id': f'CCR-9100{i:02d}', 'task_id': tid, 'location_id': lid, 'sku': sku, 'system_qty': sysq,
                        'counted_qty': sysq + var, 'variance': var, 'variance_pct': round(var / sysq * 100, 2), 'counted_at': when,
                        'counted_by': counter, 'accuracy_issue': True, 'reversed_within_48h': True, 'reversed_at': when + timedelta(hours=rev_h + 0),
                        'cause_code': 'cycle_count_variance', 'lot_number': '', 'condition': 'good', 'updated_at': when})
    catch_all = [  # night-shift corrections on the mezzanine/bulk aisles coded 'other' with no reason (matches IMS adjustments)
        (D(96), 22, 40, 'DC1-J-01-02', 'SKU-102338', -18), (D(92), 23, 15, 'DC1-J-01-03', 'SKU-101834', -60),
        (D(74), 22, 5, 'DC1-J-01-01', 'SKU-105159', -45), (D(63), 23, 50, 'DC1-J-02-01', 'SKU-102338', -22),
        (D(52), 22, 30, 'DC1-J-01-02', 'SKU-105341', -16), (D(41), 23, 20, 'DC1-L-01-01', 'SKU-101834', -55),
        (D(33), 22, 10, 'DC1-J-02-02', 'SKU-105159', -40), (D(20), 23, 45, 'DC1-J-01-03', 'SKU-102338', -20),
        (D(12), 22, 55, 'DC1-L-01-02', 'SKU-105341', -14),
    ]
    for i, (day, h, m, lid, sku, var) in enumerate(catch_all):
        tid = f'CCT-9005{i:02d}'
        when = T(day, h, m)
        story_task(tid, lid, when, 'EMP-00134', reason='Night count')
        sysq = 300
        results.append({'result_id': f'CCR-9200{i:02d}', 'task_id': tid, 'location_id': lid, 'sku': sku, 'system_qty': sysq,
                        'counted_qty': sysq + var, 'variance': var, 'variance_pct': round(var / sysq * 100, 2), 'counted_at': when,
                        'counted_by': 'EMP-00134', 'accuracy_issue': True, 'reversed_within_48h': False, 'reversed_at': None,
                        'cause_code': 'other', 'lot_number': '', 'condition': 'good', 'updated_at': when})
    results = [x for x in results if True]

    # make DC1 zone accuracy hit the planned rate in every 13-week block (story rows included in the count)
    zone_of_loc = {l['location_id']: l['zone'] for l in locations}
    groups = {}
    for row in results:
        if row['location_id'] not in loc or loc[row['location_id']]['site_id'] != 'DC1':
            continue
        blk = (as_of - row['counted_at'].date()).days // 91
        z = zone_of_loc[row['location_id']]
        if blk < 4 and z in ISSUE_RATE_DC1:
            groups.setdefault((z, blk), []).append(row)

    def set_issue(row, issue):
        sys_q = row['system_qty']
        if issue:
            pct = r.uniform(2.5, 9.0) * r.choice([-1, -1, 1])
            var = int(round(sys_q * pct / 100))
            var = var or (-1 if pct < 0 else 1)
            if abs(var / sys_q * 100) < 2.0:
                var = (-1 if var < 0 else 1) * math.ceil(sys_q * 0.025)
        else:
            var = r.choice([0, 0, 1, -1]) if sys_q >= 100 else 0
        row.update({'variance': var, 'counted_qty': sys_q + var, 'variance_pct': round(var / sys_q * 100, 2),
                    'accuracy_issue': abs(var / sys_q * 100) >= 2.0, 'reversed_within_48h': False, 'reversed_at': None,
                    'cause_code': 'cycle_count_variance' if var else ''})

    for (z, blk), rows in sorted(groups.items()):
        want = int(round(ISSUE_RATE_DC1[z][blk] / 100 * len(rows)))
        noise = [x for x in rows if not x['result_id'].startswith('CCR-9')]
        have = sum(1 for x in rows if x['accuracy_issue'])
        r.shuffle(noise)
        if have > want:
            for x in [x for x in noise if x['accuracy_issue']][:have - want]:
                set_issue(x, False)
        elif have < want:
            for x in [x for x in noise if not x['accuracy_issue']][:want - have]:
                set_issue(x, True)

    # ------------------------------------------------------------------ exceptions (store waves, picking, loading)
    exceptions = []
    north = ['ST150', 'ST159', 'ST183', 'ST148', 'ST151']      # ST150 Leeds Shopping Centre ('the Leeds store') takes the biggest hit
    north_w = [30, 25, 20, 8, 7]
    others = [s['site_id'] for s in stores if s['site_id'] not in north]
    CHANGE_MON = last_monday - timedelta(weeks=3)       # the Monday three weeks before this week
    for wk in range(0, 11):
        monday = last_monday - timedelta(weeks=wk)
        after = monday >= CHANGE_MON
        counts = {'short_pick': r.randint(30, 36) if after else r.randint(28, 34),
                  'late_wave': r.randint(11, 15) if after else r.randint(1, 3),
                  'loading_exception': r.randint(24, 30) if after else r.randint(3, 6)}
        for typ, n in counts.items():
            for _ in range(n):
                day = monday + timedelta(days=r.randint(0, 6))
                if day > as_of:
                    day = monday
                if typ == 'short_pick':
                    stage, h = 'picking', r.randint(6, 20)
                    store = r.choice(others + north)
                    sku = r.choice(stocked['DC1'])
                    exp = r.randint(4, 40)
                    exceptions.append({'site_id': 'DC1', 'process_stage': stage, 'exception_type': typ, 'to_site_id': store,
                                       'wave_id': f"W-DC1-{day:%m%d}-{r.choice(['AM', 'PM'])}", 'sku': sku, 'expected_qty': exp,
                                       'actual_qty': max(0, exp - r.randint(1, 5)), 'delay_minutes': 0,
                                       'occurred_at': T(day, h, r.randint(0, 59)),
                                       'cause': r.choice(['Pick face empty', 'Stock not in bin', 'Wrong bin scanned', 'Damaged on pick'])})
                else:
                    stage = 'wave_release' if typ == 'late_wave' else 'loading'
                    store = r.choices(north, north_w)[0] if after and r.random() < 0.8 else r.choice(others + north)
                    if typ == 'late_wave':
                        delay, cause, h = r.randint(35, 95), 'Wave released after the 05:00 slot (store wave template change)', 6
                    else:
                        delay, cause, h = r.randint(20, 70), r.choice(['No dock door free for the North trailer', 'Load sequence rework',
                                                                      'Trailer late to door; wave waiting']), r.randint(8, 18)
                    if not after:
                        cause = r.choice(['Dock door double booked', 'Load sequence rework', 'Late trailer'])
                    exceptions.append({'site_id': 'DC1', 'process_stage': stage, 'exception_type': typ, 'to_site_id': store,
                                       'wave_id': f"W-DC1-{day:%m%d}-{r.choice(['AM', 'PM'])}", 'sku': '', 'expected_qty': 0, 'actual_qty': 0,
                                       'delay_minutes': delay, 'occurred_at': T(day, h, r.randint(0, 59)), 'cause': cause})
    for site in ['DC2', 'DC3', 'DC4', 'DC5']:
        for wk in range(0, 11):
            monday = last_monday - timedelta(weeks=wk)
            for typ, n in (('short_pick', r.randint(8, 14)), ('late_wave', r.randint(0, 2)), ('loading_exception', r.randint(1, 4))):
                for _ in range(n):
                    day = min(monday + timedelta(days=r.randint(0, 6)), as_of)
                    stage = {'short_pick': 'picking', 'late_wave': 'wave_release', 'loading_exception': 'loading'}[typ]
                    exceptions.append({'site_id': site, 'process_stage': stage, 'exception_type': typ, 'to_site_id': r.choice(others),
                                       'wave_id': f"W-{site}-{day:%m%d}-AM", 'sku': r.choice(stocked[site]) if typ == 'short_pick' else '',
                                       'expected_qty': r.randint(4, 30) if typ == 'short_pick' else 0, 'actual_qty': 0,
                                       'delay_minutes': r.randint(15, 60) if typ != 'short_pick' else 0,
                                       'occurred_at': T(day, r.randint(6, 18), r.randint(0, 59)),
                                       'cause': 'Pick face empty' if typ == 'short_pick' else 'Dock door double booked'})
    for i, e in enumerate(exceptions):
        e['exception_id'] = f'EXC-{i + 1:06d}'
        e['updated_at'] = e['occurred_at']
        if e['exception_type'] == 'short_pick' and e['actual_qty'] == 0 and e['expected_qty']:
            e['actual_qty'] = max(0, e['expected_qty'] - r.randint(1, 4))

    # ------------------------------------------------------------------ allocation retries (history of earlier failures that were fixed)
    retries = []
    for ln in [x for x in order_lines if x['status'] == 'shipped' and x['line_no'] == 1 and x['site_id'] in ('DC1', 'DC2')
               and D(14) <= x['picked_at'].date() <= D(3)][:40:3]:
        t = ln['released_at'] - timedelta(hours=2)
        retries.append({'retry_id': f'RETRY-{len(retries) + 1:06d}', 'order_id': ln['order_id'], 'previous_status': 'allocation_failed',
                        'new_status': 'allocated', 'result': 'success', 'retried_at': t, 'created_by': r.choice(controllers[ln['site_id']]),
                        'notes': r.choice(['Stock replenished to pick face', 'Location unblocked then retried', 'Replenishment completed']),
                        'updated_at': t})

    # ------------------------------------------------------------------ location blocks, config changes, patches
    blocks = [{'block_id': 'LB-900001', 'location_id': 'DC1-A-05-02', 'site_id': 'DC1', 'reason': 'Damaged racking beam', 'blocked_at': T(D(40), 9),
               'blocked_by': 'EMP-00109', 'unblocked_at': T(D(33), 15), 'status': 'released'},
              {'block_id': 'LB-900002', 'location_id': 'DC2-D-03-01', 'site_id': 'DC2', 'reason': 'Awaiting recount after variance', 'blocked_at': T(D(25), 10),
               'blocked_by': 'EMP-00184', 'unblocked_at': T(D(23), 14), 'status': 'released'}]

    # ------------------------------------------------------------------ re-export story (02:14:Q7), own random stream
    # UK DCs ship stock on to Ireland and EU stores and the Venlo DC. Planted after the ledger so nothing else moves.
    rx = random.Random(1414)
    ie_stores = [x['site_id'] for x in stores if x['country'] == 'IE']
    eu_stores = [x['site_id'] for x in stores if x['country'] in ('DE', 'NL')]
    import_pool = [sk for sk in stocked['DC1'] if prod[sk]['country_of_origin'] not in ('GB', '') and prod[sk]['hazmat'] == 'none'
                   and stock_loc.get(('DC1', sk))]
    uk_pool = [sk for sk in stocked['DC1'] if prod[sk]['country_of_origin'] == 'GB' and stock_loc.get(('DC1', sk))]
    plan = []     # (weeks back, destination, qty)
    for wk in range(1, 12):
        plan += [(wk, rx.choice(ie_stores), rx.randint(120, 320)) for _ in range(3)]
        plan += [(wk, rx.choice(eu_stores), rx.randint(150, 400)) for _ in range(2)]
        plan.append((wk, 'DC4', rx.randint(600, 1500)))
    for wk, dest, qty in plan:
        sku = rx.choice(uk_pool if rx.random() < 0.15 else import_pool)
        created = D(wk * 7 + rx.randint(0, 3))
        received = wk >= 3
        tid = f'STR-{len(transfers) + 1:06d}'
        by = (controllers['DC1'] or ['EMP-00112'])[0]
        transfers.append({
            'transfer_id': tid, 'from_site_id': 'DC1', 'to_site_id': dest, 'sku': sku, 'qty_requested': qty, 'qty_allocated': qty,
            'qty_shipped': qty, 'qty_received': qty if received else 0, 'created_at': T(created, 10),
            'shipped_at': T(created + timedelta(days=2), 14), 'received_at': T(created + timedelta(days=5), 9) if received else None,
            'status': 'received' if received else 'shipped', 'reason': 'export', 'created_by': by, 'updated_at': T(created, 10)})
        mov(rx.choice(stock_loc[('DC1', sku)]), 'DC1', sku, 'transfer', -qty, tid, T(created + timedelta(days=2), 14), by)

    # ------------------------------------------------------------------ handling damage reports (own random stream)
    hr = random.Random(4040)
    damage = []
    non_sa = {sx: [d['sku'] for d in dc_stock if d['site_id'] == sx and prod[d['sku']]['category'] != 'Small Appliances'] for sx in DCS}
    stages = ['receiving', 'putaway', 'replenishment', 'picking', 'packing', 'loading']
    causes = {'receiving': 'Carton crushed on unloading', 'putaway': 'Pallet clipped by reach truck', 'replenishment': 'Case dropped during decanting',
              'picking': 'Item dropped at pick face', 'packing': 'Damaged while packing', 'loading': 'Cage tipped on loading'}

    def add_damage(site, sku, qty, stage, day, hour, cause=None):
        pool = (clerks[site] or ['EMP-00112']) if stage == 'receiving' else (pickers[site] or ['EMP-00103'])
        locs = stock_loc.get((site, sku)) or ['']
        damage.append({'report_id': f'HDR-{len(damage) + 1:06d}', 'site_id': site, 'sku': sku, 'location_id': hr.choice(locs),
                       'process_stage': stage, 'damage_qty': qty, 'cause': cause or causes[stage],
                       'reported_at': T(day, hour, hr.randint(0, 59)), 'reported_by': hr.choice(pool)})
    for site in DCS:
        for wk in range(0, 12):
            for _ in range(hr.randint(2, 5)):
                add_damage(site, hr.choice(non_sa[site]), hr.randint(1, 6), hr.choice(stages), D(wk * 7 + hr.randint(3, 9)), hr.randint(7, 19))
    # glass-fronted small appliances: our own handling damage is small and flat (the breakage rise is on the carrier lane)
    for wk in range(0, 12):
        add_damage('DC1', 'SKU-100532', 2, 'putaway' if wk % 2 else 'picking', D(wk * 7 + 4), 10 + wk % 5)
        add_damage('DC2', 'K-1700', 1, 'picking', D(wk * 7 + 5), 11 + wk % 4)
        if wk % 2 == 0:
            add_damage('DC3', 'SKU-100539', 1, 'receiving', D(wk * 7 + 6), 9 + wk % 6)
    damage.sort(key=lambda x: x['reported_at'])
    for i, x in enumerate(damage):
        x['report_id'] = f'HDR-{i + 1:06d}'

    return {
        'handling_damage_reports': damage, 'wave_configurations': [], 'inventory_status_mapping': [],
        'cause_codes': cause_codes, 'pack_specifications': pack_specs, 'location_inventory': location_inventory,
        'pallet_position_history': history, 'goods_receipts': receipts, 'replenishment_tasks': repl, 'order_lines': order_lines,
        'stock_movements': movements, 'cycle_count_tasks': tasks, 'cycle_count_results': results, 'pick_exceptions': exceptions,
        'stock_transfers': transfers, 'allocation_retries': retries, 'location_blocks': blocks,
    }


def _split(r, total, n):
    """Split a positive integer into n positive parts (random, summing to total)."""
    n = max(1, min(n, total))
    if n == 1:
        return [total]
    cuts = sorted(r.sample(range(1, total), n - 1))
    parts = [b - a for a, b in zip([0] + cuts, cuts + [total])]
    return parts


def _even_split(r, total, n):
    """Split into n roughly equal positive parts (within about 25 percent of the mean)."""
    n = max(1, min(n, total))
    w = [r.uniform(0.8, 1.2) for _ in range(n)]
    parts = [max(1, int(total * x / sum(w))) for x in w]
    parts[0] += total - sum(parts)
    return parts


def _pairs(r, products, dc_stock):
    """SKU pairs (same style, different size) that DC1 co-picks often, with the number of orders to plant."""
    dc1 = {d['sku'] for d in dc_stock if d['site_id'] == 'DC1'}
    by_style = {}
    for p in products:
        if p['sku'] in dc1 and p['supplier_id'] != AFFECTED_SUPPLIER and p['hazmat'] == 'none':
            by_style.setdefault(p['style_id'], []).append(p['sku'])
    styles = sorted([s for s, v in by_style.items() if len(v) >= 2])
    random.Random(11).shuffle(styles)
    counts = [64, 52, 41, 33, 27]
    out = []
    for s, c in zip(styles, counts):
        a, b = sorted(by_style[s])[:2]
        out.append(((a, b), c))
    return out
