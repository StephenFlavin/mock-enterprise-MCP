"""DC layout and slotting data: zones, utilisation metrics, layout changes, crossing points."""
from datetime import datetime, timedelta


def generate(g):
    r = g.rng

    # Zone configuration for each DC
    dc_zones = {
        'DC1': [
            {'zone_type': 'pick', 'zone_name': 'Pick zone A', 'aisles': 'A,B,C,D', 'travel': 45, 'locations': 2400},
            {'zone_type': 'pick', 'zone_name': 'Pick zone B', 'aisles': 'E,F,G', 'travel': 55, 'locations': 1800},
            {'zone_type': 'reserve', 'zone_name': 'Reserve zone', 'aisles': 'H,I,J,K', 'travel': 80, 'locations': 3200},
            {'zone_type': 'bulk', 'zone_name': 'Bulk floor', 'aisles': 'L,M', 'travel': 120, 'locations': 1600},
            {'zone_type': 'hazmat', 'zone_name': 'Hazmat zone', 'aisles': 'N', 'travel': 95, 'locations': 600},
        ],
        'DC2': [
            {'zone_type': 'pick', 'zone_name': 'Pick zone A', 'aisles': 'A,B,C', 'travel': 42, 'locations': 1600},
            {'zone_type': 'reserve', 'zone_name': 'Reserve zone', 'aisles': 'D,E,F', 'travel': 75, 'locations': 2400},
            {'zone_type': 'bulk', 'zone_name': 'Bulk floor', 'aisles': 'G,H', 'travel': 110, 'locations': 1200},
            {'zone_type': 'returns', 'zone_name': 'Returns zone', 'aisles': 'I', 'travel': 85, 'locations': 400},
        ],
        'DC3': [
            {'zone_type': 'pick', 'zone_name': 'Pick zone', 'aisles': 'A,B,C', 'travel': 40, 'locations': 1400},
            {'zone_type': 'reserve', 'zone_name': 'Reserve zone', 'aisles': 'D,E', 'travel': 70, 'locations': 1800},
            {'zone_type': 'bulk', 'zone_name': 'Bulk floor', 'aisles': 'F,G', 'travel': 100, 'locations': 900},
        ],
        'DC4': [
            {'zone_type': 'pick', 'zone_name': 'Pick zone', 'aisles': 'A,B', 'travel': 38, 'locations': 1200},
            {'zone_type': 'reserve', 'zone_name': 'Reserve zone', 'aisles': 'C,D', 'travel': 68, 'locations': 1600},
            {'zone_type': 'bulk', 'zone_name': 'Bulk floor', 'aisles': 'E,F', 'travel': 95, 'locations': 800},
        ],
        'DC5': [
            {'zone_type': 'pick', 'zone_name': 'Pick zone', 'aisles': 'A,B', 'travel': 35, 'locations': 1000},
            {'zone_type': 'reserve', 'zone_name': 'Reserve zone', 'aisles': 'C,D', 'travel': 65, 'locations': 1400},
        ],
    }

    zones, changes, metrics, crossings = [], [], [], []
    change_counter = 0
    crossing_counter = 0
    site_zone_ids = {}  # Map (site, type_idx) -> zone_id

    for site in ['DC1', 'DC2', 'DC3', 'DC4', 'DC5']:
        site_zones = dc_zones.get(site, [])
        type_counters = {}  # Track counter per zone type

        for zone_config in site_zones:
            zone_type = zone_config['zone_type']
            if zone_type not in type_counters:
                type_counters[zone_type] = 0

            type_counters[zone_type] += 1
            letter_idx = type_counters[zone_type] - 1

            # Create zone_id with full type name
            if zone_type == 'pick':
                zone_id = f"{site}-PICK-{chr(ord('A') + letter_idx)}"
            elif zone_type == 'reserve':
                zone_id = f"{site}-RESERVE-{chr(ord('A') + letter_idx)}"
            elif zone_type == 'bulk':
                zone_id = f"{site}-BULK-{chr(ord('A') + letter_idx)}"
            elif zone_type == 'hazmat':
                zone_id = f"{site}-HAZMAT-{chr(ord('A') + letter_idx)}"
            elif zone_type == 'returns':
                zone_id = f"{site}-RETURNS-{chr(ord('A') + letter_idx)}"
            else:
                zone_id = f"{site}-{zone_type.upper()}-{chr(ord('A') + letter_idx)}"

            site_zone_ids[(site, len(zones))] = zone_id

            active_locs = int(zone_config['locations'] * r.uniform(0.75, 0.95))
            zones.append({
                'zone_id': zone_id,
                'site_id': site,
                'zone_name': zone_config['zone_name'],
                'zone_type': zone_config['zone_type'],
                'aisle_count': len(zone_config['aisles'].split(',')),
                'aisle_letters': zone_config['aisles'],
                'total_locations': zone_config['locations'],
                'active_locations': active_locs,
                'avg_travel_distance_m': zone_config['travel'],
                'created_date': g.as_of - timedelta(days=r.randint(180, 365)),
            })

            # Add layout changes in last 90 days; August change for DC1
            if site == 'DC1' and zone_config['zone_type'] in ['pick', 'reserve']:
                # August layout change for DC1 zones
                change_counter += 1
                change_date = g.as_of - timedelta(days=35)  # ~August
                changes.append({
                    'layout_change_id': f"LYT-{change_counter:06d}",
                    'site_id': site,
                    'change_type': 'product_consolidation' if zone_config['zone_type'] == 'pick' else 'aisle_relayout',
                    'affected_zones': zone_id,
                    'affected_aisles': zone_config['aisles'].split(',')[0],
                    'description': f"Relocated clearance stock in {zone_config['zone_name']}" if r.random() > 0.5 else f"Rearranged {zone_config['zone_name']} for velocity",
                    'effective_date': change_date,
                    'planned_date': change_date - timedelta(days=3),
                    'estimated_moves': int(zone_config['locations'] * 0.3),
                    'actual_moves': int(zone_config['locations'] * 0.28),
                    'completion_pct': 100,
                    'status': 'completed',
                    'estimated_effort_hours': r.uniform(40, 80),
                    'actual_effort_hours': r.uniform(42, 85),
                    'notes': 'Completed on schedule',
                    'updated_at': change_date + timedelta(days=5),
                })

            # Add recent layout changes for some zones
            elif r.random() > 0.7:
                change_counter += 1
                change_date = g.as_of - timedelta(days=r.randint(5, 45))
                changes.append({
                    'layout_change_id': f"LYT-{change_counter:06d}",
                    'site_id': site,
                    'change_type': r.choice(['aisle_relayout', 'product_consolidation']),
                    'affected_zones': zone_id,
                    'affected_aisles': zone_config['aisles'].split(',')[0],
                    'description': f"Layout optimisation in {zone_config['zone_name']}",
                    'effective_date': change_date,
                    'planned_date': change_date - timedelta(days=2),
                    'estimated_moves': int(zone_config['locations'] * 0.2),
                    'actual_moves': int(zone_config['locations'] * r.uniform(0.18, 0.22)),
                    'completion_pct': 100,
                    'status': 'completed',
                    'estimated_effort_hours': r.uniform(20, 50),
                    'actual_effort_hours': r.uniform(22, 52),
                    'notes': 'Completed successfully',
                    'updated_at': change_date + timedelta(days=3),
                })

            # Metrics for last 30 days
            for days_ago in [30, 23, 16, 9, 2]:
                measured_date = g.as_of - timedelta(days=days_ago)

                # Higher utilisation for DC1, lower for DC2
                if site == 'DC1':
                    util = r.uniform(82, 94)
                elif site == 'DC2':
                    util = r.uniform(60, 75)
                else:
                    util = r.uniform(70, 85)

                picks_per_hour = r.uniform(45, 75) if zone_config['zone_type'] == 'pick' else r.uniform(10, 25)

                metrics.append({
                    'site_id': site,
                    'zone_id': zone_id,
                    'measured_date': measured_date,
                    'utilisation_pct': round(util, 1),
                    'avg_travel_distance_m': zone_config['travel'] + r.randint(-5, 5),
                    'picks_per_hour': round(picks_per_hour, 1),
                    'sku_count': r.randint(int(zone_config['locations'] * 0.05), int(zone_config['locations'] * 0.15)),
                    'total_on_hand': r.randint(int(zone_config['locations'] * 0.3), int(zone_config['locations'] * 0.7)),
                    'velocity_class': r.choices(['A', 'B', 'C'], [0.2, 0.3, 0.5])[0],
                    'congestion_score': round(r.uniform(20, 75), 1),
                })

        # Crossing points - one per zone roughly, reference the actual zone_ids
        type_idx_map = {}  # Track index per type for this site
        for i, zone_config in enumerate(site_zones):
            crossing_counter += 1
            aisles = zone_config['aisles'].split(',')
            aisle_a = aisles[0]
            aisle_b = aisles[-1] if len(aisles) > 1 else aisles[0]

            zone_type = zone_config['zone_type']
            if zone_type not in type_idx_map:
                type_idx_map[zone_type] = 0
            else:
                type_idx_map[zone_type] += 1

            letter_idx = type_idx_map[zone_type]

            zone_id = f"{site}-{zone_type.upper()}-{chr(ord('A') + letter_idx)}"
            if zone_type == 'pick':
                zone_id = f"{site}-PICK-{chr(ord('A') + letter_idx)}"
            elif zone_type == 'reserve':
                zone_id = f"{site}-RESERVE-{chr(ord('A') + letter_idx)}"
            elif zone_type == 'bulk':
                zone_id = f"{site}-BULK-{chr(ord('A') + letter_idx)}"
            elif zone_type == 'hazmat':
                zone_id = f"{site}-HAZMAT-{chr(ord('A') + letter_idx)}"
            elif zone_type == 'returns':
                zone_id = f"{site}-RETURNS-{chr(ord('A') + letter_idx)}"

            # More incidents in Q3 for DC1 after layout change
            q3_incidents = 0
            q2_incidents = 0
            if site == 'DC1':
                q3_incidents = r.randint(2, 6)
                q2_incidents = r.randint(0, 2)
            else:
                q3_incidents = r.randint(0, 2)
                q2_incidents = r.randint(0, 1)

            crossings.append({
                'crossing_id': f"XPT-{site}-{crossing_counter:03d}",
                'site_id': site,
                'location_description': f"Aisle {aisle_a}/{aisle_b} intersection, {zone_config['zone_name']}",
                'aisle_a': aisle_a,
                'aisle_b': aisle_b,
                'zone_id': zone_id,
                'fk_pedestrian_crossing': True if r.random() > 0.3 else False,
                'incidents_q3': q3_incidents,
                'incidents_q2': q2_incidents,
                'traffic_score': r.choice(['low', 'medium', 'high']),
                'has_proximity_sensor': False if site in ['DC2', 'DC3'] else (True if r.random() > 0.4 else False),
                'has_speed_limiter': False,
                'visibility_rating': r.choice(['excellent', 'good', 'fair', 'poor']),
            })

    return {
        'layout_zones': zones,
        'layout_changes': changes,
        'zone_metrics': metrics,
        'crossing_points': crossings,
    }
