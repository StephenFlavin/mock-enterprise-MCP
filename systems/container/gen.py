"""Container visibility and ocean freight tracking data."""
from datetime import datetime, timedelta
import hashlib


def generate(g):
    r = g.rng

    # Key ports by region
    ports = {
        'SHA': {'name': 'Shanghai', 'region': 'Southeast Asia'},
        'ROT': {'name': 'Rotterdam', 'region': 'Northern Europe'},
        'HKG': {'name': 'Hong Kong', 'region': 'Southeast Asia'},
        'SIN': {'name': 'Singapore', 'region': 'Southeast Asia'},
        'DXB': {'name': 'Dubai', 'region': 'Middle East'},
        'HCM': {'name': 'Ho Chi Minh City', 'region': 'Southeast Asia'},
        'BKK': {'name': 'Bangkok', 'region': 'Southeast Asia'},
        'VAL': {'name': 'Valencia', 'region': 'Southern Europe'},
        'HAM': {'name': 'Hamburg', 'region': 'Northern Europe'},
        'BNE': {'name': 'Brisbane', 'region': 'Oceania'},
    }

    # Get sea POs from master
    sea_pos = [po for po in g.master("purchase_orders")
               if po["mode"] == "sea" and po["status"] in ("open", "confirmed", "shipped")]

    # Map suppliers to origin ports
    suppliers = g.master("suppliers")
    supplier_by_id = {s["supplier_id"]: s for s in suppliers}

    def supplier_origin_port(supplier_id):
        sup = supplier_by_id.get(supplier_id)
        if not sup:
            return 'SHA'
        country = sup.get('country', 'CN')
        country_ports = {
            'CN': 'SHA', 'VN': 'HCM', 'IN': 'DXB', 'TR': 'DXB', 'IT': 'ROT',
            'FR': 'HAM', 'DE': 'HAM', 'GB': 'ROT', 'MX': 'DXB'
        }
        return country_ports.get(country, 'SHA')

    vessels = []
    container_shipments = []
    container_contents = []
    port_status = []
    transit_history = []
    disruptions = []
    disruption_costs = []
    rail_segments = []
    port_dwell_history = []
    eta_predictions = []

    # Create port status (current)
    for port_code, port_info in ports.items():
        congestion = r.choice(['low', 'low', 'medium', 'high'])
        status = 'open'
        if congestion == 'high':
            status = r.choice(['open', 'congested'])
        port_status.append({
            'port_code': port_code,
            'port_name': port_info['name'],
            'region': port_info['region'],
            'status': status,
            'current_wait_hours': r.uniform(6, 48) if congestion in ['medium', 'high'] else r.uniform(0, 12),
            'congestion_level': congestion,
            'vessels_waiting': r.randint(0, 15) if congestion == 'high' else r.randint(0, 5),
            'avg_dwell_hours': r.uniform(24, 120) if congestion == 'high' else r.uniform(12, 48),
            'status_updated_at': g.as_of + timedelta(hours=-r.randint(1, 12))
        })

    # Create vessels and associated shipments
    routes = [
        ('SHA', 'ROT', 'China-Europe'),
        ('SHA', 'HAM', 'China-Europe'),
        ('HKG', 'ROT', 'China-Europe'),
        ('HCM', 'ROT', 'Vietnam-Europe'),
        ('SIN', 'ROT', 'Singapore-Europe'),
        ('BKK', 'HAM', 'Thailand-Europe'),
        ('DXB', 'ROT', 'Middle East-Europe'),
    ]

    # Filter POs by destination site and create shipments
    po_idx = 0
    for route_origin, route_dest, route_name in routes:
        for vessel_num in range(2):
            vessel_id = f"CONT-VESSEL-{len(vessels) + 1:03d}"
            vessel_name = f"{route_name.split('-')[0]}-{vessel_num+1:02d}"

            # Vessel currently in transit
            days_into_route = r.randint(5, 20)
            depart_time = g.as_of - timedelta(days=days_into_route)
            eta_time = g.as_of + timedelta(days=r.randint(3, 10))

            current_status = r.choice(['underway', 'anchored', 'underway'])
            current_port = route_dest if current_status == 'anchored' else 'At Sea'

            vessels.append({
                'vessel_id': vessel_id,
                'name': vessel_name,
                'current_port': current_port,
                'berth_status': current_status,
                'current_position': f"{r.uniform(40, 60):.2f}N, {r.uniform(-20, 30):.2f}E",
                'eta_port': route_dest,
                'eta_timestamp': eta_time,
                'eta_berth_timestamp': eta_time + timedelta(hours=r.randint(6, 24)),
                'container_count': 0,
                'updated_at': g.as_of - timedelta(hours=r.randint(1, 48))
            })

            # Add containers to this vessel
            containers_per_vessel = r.randint(30, 80)
            for cont_idx in range(containers_per_vessel):
                if po_idx >= len(sea_pos):
                    break
                po = sea_pos[po_idx]
                po_idx += 1

                origin_port = supplier_origin_port(po['supplier_id'])
                container_id = f"CONT-{len(container_shipments) + 1:06d}"
                shipment_id = f"SHIP-{len(container_shipments) // 4 + 1:05d}"

                # Determine if container is already at destination or still in transit
                days_since_ship = (g.as_of - datetime.fromisoformat(po['ship_date']).date()).days
                est_transit = r.randint(20, 40)

                if days_since_ship < est_transit:
                    status = r.choice(['in_transit', 'at_port', 'in_transit'])
                    actual_arrival = None
                else:
                    status = r.choice(['delayed', 'delayed', 'in_transit'])
                    actual_arrival = datetime.fromisoformat(po['ship_date']) + timedelta(days=est_transit)

                container_value = float(po['total_value']) * (0.9 + r.random() * 0.2)

                container_shipments.append({
                    'container_id': container_id,
                    'shipment_id': shipment_id,
                    'vessel_id': vessel_id,
                    'origin_port': origin_port,
                    'destination_port': route_dest,
                    'next_port': route_dest,
                    'route': route_name,
                    'transship_port': None,
                    'container_type': r.choice(['40ft', '40ft', '20ft']),
                    'status': status,
                    'actual_arrival': actual_arrival,
                    'destination_site_id': po['dest_site_id'],
                    'value_gbp': container_value,
                    'booking_date': datetime.fromisoformat(po['order_date']).date(),
                    'updated_at': g.as_of - timedelta(hours=r.randint(1, 72))
                })

                # Add container contents
                products = g.master("products")
                skus_in_po = [p for p in products if p['supplier_id'] == po['supplier_id']]
                if not skus_in_po:
                    skus_in_po = r.sample(products, 3)

                lines = r.randint(1, 5)
                for line_num in range(1, lines + 1):
                    sku_obj = r.choice(skus_in_po)
                    sku = sku_obj['sku']
                    quantity = r.randint(50, 500)
                    unit_cost = float(sku_obj.get('unit_cost_gbp', 20))
                    total_value = quantity * unit_cost

                    container_contents.append({
                        'container_id': container_id,
                        'line_number': line_num,
                        'sku': sku,
                        'quantity': quantity,
                        'unit_cost_gbp': unit_cost,
                        'total_value_gbp': total_value
                    })

                vessels[-1]['container_count'] += 1

    # Create transit history
    for route_origin, route_dest, route_name in routes:
        for historical_idx in range(r.randint(8, 15)):
            days_ago = r.randint(30, 180)
            depart_date = g.as_of - timedelta(days=days_ago)
            planned_days = r.randint(20, 35)
            actual_days = planned_days + r.randint(-5, 15)

            transit_history.append({
                'route_code': route_name,
                'transit_id': f"TRN-{len(transit_history) + 1:06d}",
                'origin_port': route_origin,
                'destination_port': route_dest,
                'planned_transit_days': planned_days,
                'actual_transit_days': float(actual_days),
                'departure_date': depart_date.date(),
                'arrival_date': (depart_date + timedelta(days=actual_days)).date(),
                'delay_days': float(max(0, actual_days - planned_days)),
                'port_dwell_hours': r.uniform(24, 96),
                'containers_count': r.randint(40, 120)
            })

    # Create disruptions
    disruption_types = ['weather', 'strike', 'closure', 'congestion']
    affected_regions = ['Southeast Asia', 'Northern Europe', 'Southern Europe', 'Middle East']

    for disr_idx in range(r.randint(3, 6)):
        days_ago = r.randint(10, 180)
        duration = r.randint(2, 14)

        disruptions.append({
            'disruption_id': f"DISR-{len(disruptions) + 1:06d}",
            'event_type': r.choice(disruption_types),
            'affected_port': r.choice(list(ports.keys())),
            'region': r.choice(affected_regions),
            'start_date': (g.as_of - timedelta(days=days_ago)).date(),
            'end_date': (g.as_of - timedelta(days=days_ago - duration)).date(),
            'duration_days': duration,
            'containers_affected': r.randint(20, 200),
            'description': f"Weather event affecting operations"
        })

    # Create disruption costs
    for disr in disruptions:
        num_costs = r.randint(1, 3)
        for cost_idx in range(num_costs):
            cost_types = ['demurrage', 'detention', 'air_freight', 'transshipment']
            containers_affected = r.randint(5, disr['containers_affected'])
            cost_per_container = r.uniform(50, 500)

            disruption_costs.append({
                'cost_id': f"COST-{len(disruption_costs) + 1:06d}",
                'disruption_id': disr['disruption_id'],
                'cost_type': r.choice(cost_types),
                'cost_gbp': containers_affected * cost_per_container,
                'containers_affected': containers_affected,
                'cost_per_container_gbp': cost_per_container
            })

    # Create rail segments
    rail_routes = [
        ('VAL', 'HAM', 'Valencia-Hamburg'),
        ('VAL', 'ROT', 'Valencia-Rotterdam'),
        ('DXB', 'ROT', 'Dubai-Rotterdam'),
        ('SIN', 'HCM', 'Singapore-HCM'),
    ]

    for origin, dest, name in rail_routes:
        on_time = r.randint(70, 95)
        total_transits = r.randint(20, 50)

        rail_segments.append({
            'segment_id': f"RAIL-{len(rail_segments) + 1:06d}",
            'origin_port': origin,
            'destination_port': dest,
            'region': 'Europe' if 'Europe' in name or origin in ['VAL', 'HAM', 'ROT'] else 'Southeast Asia',
            'transit_count': total_transits,
            'on_time_count': int(total_transits * on_time / 100),
            'on_time_pct': float(on_time),
            'avg_delay_hours': r.uniform(0, 24) if on_time < 90 else r.uniform(0, 12),
            'reliability_score': float(on_time)
        })

    # Create port dwell history
    for port_code in ports.keys():
        for history_idx in range(r.randint(10, 20)):
            days_ago = r.randint(1, 180)
            dwell_history_append = {
                'port_code': port_code,
                'dwell_id': f"DWEL-{len(port_dwell_history) + 1:06d}",
                'arrival_date': (g.as_of - timedelta(days=days_ago)).date(),
                'dwell_hours': r.uniform(12, 144),
                'vessel_count': r.randint(1, 8),
                'congestion_status': r.choice(['low', 'medium', 'high'])
            }
            port_dwell_history.append(dwell_history_append)

    # Create ETA predictions
    for ship in container_shipments[:min(50, len(container_shipments))]:
        for pred_idx in range(r.randint(3, 6)):
            days_ago = r.randint(1, 30)
            pred_date = g.as_of - timedelta(days=days_ago)
            actual_eta = ship.get('actual_arrival') or (g.as_of + timedelta(days=r.randint(1, 20)))
            pred_eta = actual_eta + timedelta(hours=r.randint(-48, 72))

            eta_predictions.append({
                'prediction_id': f"ETA-{len(eta_predictions) + 1:06d}",
                'vessel_id': ship['vessel_id'],
                'route': ship['route'],
                'prediction_date': pred_date.date() if isinstance(pred_date, datetime) else pred_date,
                'predicted_eta': pred_eta,
                'actual_eta': actual_eta,
                'eta_accuracy_hours': float((actual_eta - pred_eta).total_seconds() / 3600)
            })

    return {
        'vessels': vessels,
        'container_shipments': container_shipments,
        'container_contents': container_contents,
        'port_status': port_status,
        'transit_history': transit_history,
        'disruptions': disruptions,
        'disruption_costs': disruption_costs,
        'rail_segments': rail_segments,
        'port_dwell_history': port_dwell_history,
        'eta_predictions': eta_predictions
    }
