"""Warehouse data: goods receipts, cycle counts, stock movements and pack specs."""
from datetime import datetime, timedelta

def generate(g):
    r = g.rng
    dcs = ['DC1', 'DC2', 'DC3', 'DC4', 'DC5']

    # Cause codes reference data
    cause_codes = [
        {'cause_code': 'CC-001', 'description': 'Counting error - digit transposition',
         'category': 'counting_error', 'intended_use': 'When count result is close but not exact, typically off by 1-10 units'},
        {'cause_code': 'CC-002', 'description': 'Damaged goods on receipt',
         'category': 'damage', 'intended_use': 'Goods damaged during transport or receipt'},
        {'cause_code': 'CC-003', 'description': 'Supplier short shipment',
         'category': 'supplier_short', 'intended_use': 'Supplier did not send full quantity ordered'},
        {'cause_code': 'CC-004', 'description': 'Carrier damage',
         'category': 'carrier_damage', 'intended_use': 'Goods damaged in transit by carrier'},
        {'cause_code': 'CC-005', 'description': 'System error',
         'category': 'system_error', 'intended_use': 'WMS or integration system malfunction'},
        {'cause_code': 'CC-006', 'description': 'Theft/shrinkage',
         'category': 'theft', 'intended_use': 'Unexplained loss of stock'},
        {'cause_code': 'CC-007', 'description': 'Expiry',
         'category': 'expiry', 'intended_use': 'Product expired and written off'},
        {'cause_code': 'CC-008', 'description': 'Processing error',
         'category': 'processing_error', 'intended_use': 'Error in goods receipt, pick or transfer'},
        {'cause_code': 'CC-999', 'description': 'Other',
         'category': 'other', 'intended_use': 'Miscellaneous causes pending investigation'},
    ]

    # Pack specifications for all products
    pack_specs = []
    products = g.master('products')
    for i, product in enumerate(products):
        pack_specs.append({
            'pack_spec_id': f'PKS-{i+1:06d}',
            'sku': product['sku'],
            'pack_type': r.choice(['polybag', 'carton', 'hanging', 'flat']),
            'units_per_pack': r.choice([1, 2, 5, 10, 20]),
            'packs_per_pallet': r.choice([100, 200, 400, 500]),
            'units_per_pallet': 0,  # Will calculate
            'pallet_height_cm': r.randint(120, 200),
            'pallet_weight_kg': r.randint(500, 1500),
            'bonded_suitable': product['hazmat'] == 'none',
            'created_at': g.as_of - timedelta(days=r.randint(90, 365)),
            'updated_at': g.as_of
        })
        # Calculate units_per_pallet
        pack_specs[-1]['units_per_pallet'] = (
            pack_specs[-1]['units_per_pack'] * pack_specs[-1]['packs_per_pallet']
        )

    # Goods receipts - generate many from POs across multiple days
    goods_receipts = []
    shipments_by_po = {}
    for s in g.master('shipments'):
        if s['po_id'] not in shipments_by_po:
            shipments_by_po[s['po_id']] = []
        shipments_by_po[s['po_id']].append(s)

    # Generate receipts for a broader range of POs
    all_pos = g.master('purchase_orders')
    for po in all_pos[:200]:  # Expand to 200 POs
        due = datetime.fromisoformat(po['due_date'])
        days = (due.date() - g.as_of).days
        if not -120 <= days <= 30 or po['status'] in ('cancelled', 'draft'):
            continue
        # Get PO lines for this PO
        po_lines_data = [l for l in g.master('po_lines') if l['po_id'] == po['po_id']]
        if not po_lines_data:
            continue
        shipment = shipments_by_po.get(po['po_id'], [None])[0]
        carrier_id = shipment['carrier_id'] if shipment else r.choice([c['carrier_id'] for c in g.master('carriers')])

        for line in po_lines_data:  # All lines in PO
            gr_id = f'GR-{len(goods_receipts) + 1:06d}'
            qty_ordered = int(line['qty_ordered'])
            # Realistic variance: 95-105% received
            qty_received = int(qty_ordered * r.uniform(0.95, 1.05))
            # Received can be before or after due date
            received_at = due - timedelta(days=r.randint(-7, 14))
            goods_receipts.append({
                'receipt_id': gr_id,
                'po_id': po['po_id'],
                'site_id': po['dest_site_id'],
                'sku': line['sku'],
                'qty_ordered': qty_ordered,
                'qty_received': qty_received,
                'qty_accepted': int(qty_received * r.uniform(0.95, 1.0)),
                'received_at': received_at,
                'received_by': f"EMP-{r.randint(1000, 9999):05d}",
                'dock': f"D{r.randint(1, 24):02d}",
                'carrier_id': carrier_id,
                'batch_number': f"BTH-{g.fake.year()}-{r.randint(1000, 9999)}" if r.random() > 0.5 else '',
                'expiry_date': g.as_of + timedelta(days=r.randint(30, 730)) if r.random() > 0.7 else None,
                'damage_qty': r.randint(0, max(1, qty_received // 50)) if r.random() > 0.8 else 0,
                'short_qty': max(0, qty_ordered - qty_received),
                'updated_at': received_at
            })

    # Cycle count tasks and results - much more data across 90 days
    cycle_count_tasks = []
    cycle_count_results = []
    locations = g.master('locations')

    # Create tasks for every location across 90 days
    for loc in locations:
        # Each location counted 3-5 times in the past 90 days
        for count_num in range(r.randint(3, 5)):
            task_id = f'CCT-{len(cycle_count_tasks) + 1:06d}'
            days_ago = r.randint(5, 90)
            counted_at = g.as_of - timedelta(days=days_ago)
            status_choice = r.random()
            if status_choice < 0.85:
                status = 'completed'
            elif status_choice < 0.95:
                status = 'planned'
            else:
                status = 'cancelled'

            cycle_count_tasks.append({
                'task_id': task_id,
                'location_id': loc['location_id'],
                'site_id': loc['site_id'],
                'zone': loc['zone'],
                'status': status,
                'assigned_to': f"EMP-{r.randint(1000, 9999):05d}",
                'created_at': counted_at - timedelta(days=r.randint(1, 7)),
                'released_at': counted_at - timedelta(days=r.randint(0, 5)) if status != 'planned' else None,
                'completed_at': counted_at if status == 'completed' else None,
                'cancelled_at': counted_at if status == 'cancelled' else None,
                'cancel_reason': r.choice(['Location blocked', 'Duplicate count', 'Staffing']) if status == 'cancelled' else '',
                'priority': r.randint(1, 100),
                'updated_at': counted_at
            })
            # Add cycle count results for completed tasks
            if status == 'completed':
                # 2-6 SKUs per location
                for k in range(r.randint(2, 6)):
                    system_qty = r.randint(10, 500)
                    accuracy_issue = r.random() < 0.12
                    variance = r.randint(-50, 50) if accuracy_issue else r.randint(-3, 3)
                    cycle_count_results.append({
                        'result_id': f'CCR-{len(cycle_count_results) + 1:06d}',
                        'task_id': task_id,
                        'location_id': loc['location_id'],
                        'sku': r.choice(products)['sku'],
                        'system_qty': system_qty,
                        'counted_qty': system_qty + variance,
                        'variance': variance,
                        'variance_pct': round(variance / system_qty * 100, 2) if system_qty else 0,
                        'counted_at': counted_at,
                        'accuracy_issue': accuracy_issue,
                        'reversed_within_48h': r.random() < 0.08,
                        'lot_number': f"LOT-{r.randint(1000, 9999)}" if r.random() > 0.6 else '',
                        'condition': r.choice(['good', 'good', 'good', 'good', 'damaged', 'expired']),
                        'updated_at': counted_at
                    })

    # Stock movements - receipts, putaways, picks (generate thousands)
    stock_movements = []

    # Generate movements from goods receipts
    for gr in goods_receipts:
        # Receipt movement
        location_choices = [l for l in locations if l['site_id'] == gr['site_id']]
        if not location_choices:
            continue

        mov = {
            'movement_id': f'MOV-{len(stock_movements) + 1:06d}',
            'location_id': r.choice(location_choices)['location_id'],
            'site_id': gr['site_id'],
            'sku': gr['sku'],
            'movement_type': 'receipt',
            'qty': gr['qty_received'],
            'reference_id': gr['receipt_id'],
            'moved_at': gr['received_at'],
            'moved_by': gr['received_by'],
            'batch_number': gr['batch_number'],
            'status': 'completed',
            'updated_at': gr['received_at']
        }
        stock_movements.append(mov)

        # Simulate multiple picks from this receipt across different orders
        if r.random() > 0.1:
            for _ in range(r.randint(2, 8)):
                pick_qty = min(r.randint(5, 150), max(1, gr['qty_received'] - 10))
                if pick_qty > 0:
                    stock_movements.append({
                        'movement_id': f'MOV-{len(stock_movements) + 1:06d}',
                        'location_id': mov['location_id'],
                        'site_id': gr['site_id'],
                        'sku': gr['sku'],
                        'movement_type': 'pick',
                        'qty': -pick_qty,
                        'reference_id': f"ORD-2026-{r.randint(100000, 999999)}",
                        'moved_at': gr['received_at'] + timedelta(days=r.randint(1, 60)),
                        'moved_by': f"EMP-{r.randint(1000, 9999):05d}",
                        'batch_number': gr['batch_number'],
                        'status': 'completed',
                        'updated_at': gr['received_at'] + timedelta(days=r.randint(1, 60))
                    })

        # Add some transfer movements
        if r.random() > 0.7:
            transfer_qty = min(r.randint(20, 100), max(1, gr['qty_received'] - 5))
            if transfer_qty > 0:
                stock_movements.append({
                    'movement_id': f'MOV-{len(stock_movements) + 1:06d}',
                    'location_id': mov['location_id'],
                    'site_id': gr['site_id'],
                    'sku': gr['sku'],
                    'movement_type': 'transfer',
                    'qty': -transfer_qty,
                    'reference_id': f"STR-{r.randint(100000, 999999)}",
                    'moved_at': gr['received_at'] + timedelta(days=r.randint(5, 45)),
                    'moved_by': f"EMP-{r.randint(1000, 9999):05d}",
                    'batch_number': gr['batch_number'],
                    'status': 'completed',
                    'updated_at': gr['received_at'] + timedelta(days=r.randint(5, 45))
                })

    # Stock transfers - rebalancing between DCs
    stock_transfers = []
    for i in range(r.randint(100, 200)):
        transfer_id = f'STR-{len(stock_transfers) + 1:06d}'
        from_site = r.choice(dcs)
        to_site = r.choice([d for d in dcs if d != from_site])
        created_at = g.as_of - timedelta(days=r.randint(1, 90))
        status_choice = r.random()
        if status_choice < 0.3:
            status = 'draft'
        elif status_choice < 0.5:
            status = 'confirmed'
        elif status_choice < 0.7:
            status = 'allocated'
        elif status_choice < 0.85:
            status = 'shipped'
        else:
            status = 'received'

        stock_transfers.append({
            'transfer_id': transfer_id,
            'from_site_id': from_site,
            'to_site_id': to_site,
            'sku': r.choice(products)['sku'],
            'qty_requested': r.randint(50, 1000),
            'qty_allocated': r.randint(40, 1000) if status != 'draft' else 0,
            'qty_shipped': r.randint(40, 1000) if status in ('shipped', 'received') else 0,
            'qty_received': r.randint(40, 1000) if status == 'received' else 0,
            'created_at': created_at,
            'shipped_at': created_at + timedelta(days=r.randint(1, 14)) if status in ('shipped', 'received') else None,
            'received_at': created_at + timedelta(days=r.randint(2, 21)) if status == 'received' else None,
            'status': status,
            'reason': r.choice(['rebalance', 'stockout', 'clearance', 'disposal', 'outlet']),
            'created_by': f"EMP-{r.randint(1000, 9999):05d}",
            'updated_at': created_at
        })

    return {
        'cause_codes': cause_codes,
        'pack_specifications': pack_specs,
        'goods_receipts': goods_receipts,
        'cycle_count_tasks': cycle_count_tasks,
        'cycle_count_results': cycle_count_results,
        'stock_movements': stock_movements,
        'stock_transfers': stock_transfers,
    }
