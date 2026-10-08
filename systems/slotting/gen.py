"""DC layout and slotting data: zones, weekly zone metrics, layout changes, crossing points.

DC1 layout changes and crossing points are hand-written in seed/ (story rows); gen.py builds the zones and
metrics for every DC and light background changes/crossings for DC2-DC5.
"""
from datetime import timedelta

# (zone_type, zone_name, aisles, travel_m, locations, util_pct, picks_per_hour, congestion)
DC_ZONES = {
    'DC1': [
        ('pick', 'Pick zone A', [1, 2, 3, 4], 45, 2400, 89.0, 63.0, 70.0),
        ('pick', 'Pick zone B', [5, 6, 7], 55, 1800, 90.0, 62.0, 73.0),
        ('reserve', 'Reserve zone', [8, 9, 10, 11], 80, 3200, 84.0, 24.0, 62.0),
        ('bulk', 'Bulk floor', [12, 13], 120, 1600, 77.0, 14.0, 52.0),
        ('hazmat', 'Hazmat zone', [14], 95, 600, 70.0, 7.5, 38.0),
    ],
    'DC2': [
        ('pick', 'Pick zone A', [1, 2, 3], 42, 1600, 68.0, 56.0, 48.0),
        ('reserve', 'Reserve zone', [4, 5, 6], 75, 2400, 71.0, 22.0, 52.0),
        ('bulk', 'Bulk floor', [7, 8], 110, 1200, 64.0, 13.0, 43.0),
        ('returns', 'Returns zone', [9], 85, 400, 56.0, 7.0, 32.0),
    ],
    'DC3': [
        ('pick', 'Pick zone', [1, 2, 3], 40, 1400, 78.0, 58.0, 56.0),
        ('reserve', 'Reserve zone', [4, 5], 70, 1800, 74.0, 23.0, 50.0),
        ('bulk', 'Bulk floor', [6, 7], 100, 900, 68.0, 13.0, 44.0),
    ],
    'DC4': [
        ('pick', 'Pick zone', [1, 2], 38, 1200, 74.0, 57.0, 54.0),
        ('reserve', 'Reserve zone', [3, 4], 68, 1600, 72.0, 22.0, 48.0),
        ('bulk', 'Bulk floor', [5, 6], 95, 800, 66.0, 12.0, 42.0),
    ],
    'DC5': [
        ('pick', 'Pick zone', [1, 2], 35, 1000, 76.0, 59.0, 55.0),
        ('reserve', 'Reserve zone', [3, 4], 65, 1400, 73.0, 23.0, 49.0),
    ],
}


def generate(g):
    r = g.rng
    zones, metrics, changes, crossings = [], [], [], []
    change_no = 100
    cross_no = 100

    for site, cfgs in DC_ZONES.items():
        seen = {}
        for ztype, zname, aisles, travel, locs, util, pph, cong in cfgs:
            seen[ztype] = seen.get(ztype, 0) + 1
            zone_id = f"{site}-{ztype.upper()}-{chr(64 + seen[ztype])}"
            zones.append({
                'zone_id': zone_id, 'site_id': site, 'zone_name': zname, 'zone_type': ztype,
                'aisle_count': len(aisles), 'aisles': ','.join(str(a) for a in aisles),
                'total_locations': locs, 'active_locations': round(locs * util / 100),
                'avg_travel_distance_m': travel,
                'created_date': g.as_of - timedelta(days=r.randint(400, 900)),
            })
            # five weekly measurements, latest today; small noise and a gentle upward drift
            for i, days_ago in enumerate([28, 21, 14, 7, 0]):
                drift = (i - 2) * 0.5
                metrics.append({
                    'site_id': site, 'zone_id': zone_id, 'measured_date': g.as_of - timedelta(days=days_ago),
                    'utilisation_pct': round(util + drift + r.uniform(-0.6, 0.6), 1),
                    'avg_travel_distance_m': round(travel + r.uniform(-1.5, 1.5), 1),
                    'picks_per_hour': round(pph + r.uniform(-1.2, 1.2), 1),
                    'sku_count': round(locs * 0.14) + r.randint(-6, 6),
                    'total_on_hand': round(locs * 0.55 * util / 100 * 4) + r.randint(-40, 40),
                    'velocity_class': 'A' if ztype == 'pick' else ('B' if ztype == 'reserve' else 'C'),
                    'congestion_score': round(cong + drift + r.uniform(-1.5, 1.5), 1),
                })

            if site == 'DC1':
                continue  # DC1 changes and crossings are story rows in seed/
            # background crossing point per zone
            cross_no += 1
            a, b = aisles[0], aisles[-1]
            crossings.append({
                'crossing_id': f"XPT-{site}-{cross_no:03d}", 'site_id': site,
                'location_description': f"Aisle {a}/{b} cross-aisle, {zname}",
                'aisle_a': str(a), 'aisle_b': str(b), 'zone_id': zone_id,
                'fk_pedestrian_crossing': ztype in ('pick', 'reserve'),
                'incidents_q3': r.randint(0, 1), 'incidents_q2': r.randint(0, 1),
                'traffic_score': 'high' if ztype == 'pick' else r.choice(['low', 'medium']),
                'has_proximity_sensor': site in ('DC4', 'DC5') and ztype == 'pick',
                'has_speed_limiter': False,
                'visibility_rating': r.choice(['excellent', 'good', 'good', 'fair']),
            })
            # occasional small background change
            if r.random() < 0.5:
                change_no += 1
                d = g.as_of - timedelta(days=r.randint(10, 80))
                est = round(locs * 0.15)
                hrs = round(est / r.uniform(10, 14), 1)
                changes.append({
                    'layout_change_id': f"LYT-{change_no:06d}", 'site_id': site,
                    'change_type': r.choice(['aisle_relayout', 'product_consolidation']),
                    'affected_zones': zone_id, 'affected_aisles': str(aisles[0]),
                    'description': f"Minor slotting tidy in {zname}",
                    'effective_date': d, 'planned_date': d - timedelta(days=2),
                    'estimated_moves': est, 'actual_moves': est + r.randint(-10, 10),
                    'completion_pct': 100, 'status': 'completed',
                    'estimated_effort_hours': hrs, 'actual_effort_hours': round(hrs * r.uniform(0.95, 1.1), 1),
                    'notes': 'Completed on schedule', 'updated_at': d + timedelta(days=2),
                })

    return {'layout_zones': zones, 'layout_changes': changes, 'zone_metrics': metrics, 'crossing_points': crossings}
