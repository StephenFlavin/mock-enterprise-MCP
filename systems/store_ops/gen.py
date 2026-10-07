"""Store operations data: KPIs, visits, action plans, tasks, shrink control, take-back pilots."""
from datetime import datetime, timedelta, date


def generate(g):
    """Generate store operations data."""
    r = g.rng
    
    # Get all store sites
    stores = [s for s in g.master("sites") if s["type"] == "store" and s["status"] == "open"]
    
    store_kpis = []
    store_visits = []
    action_plans = []
    week_tasks = []
    cycle_count_tasks = []
    shelf_availability_exceptions = []
    replenishment_priorities = []
    click_collect_demand = []
    shrink_control_programmes = []
    take_back_pilot_results = []
    backroom_constraints = []
    plan_vs_actual = []
    store_control_results = []
    
    # Shrink control programmes
    shrink_programmes = [
        ("SCP-0001", "RFID Tagging", "Tagging", "RFID tags on high-theft items", 2500, 15),
        ("SCP-0002", "Enhanced Staffing", "Staffing", "Additional floor staff during peak hours", 15000, 8),
        ("SCP-0003", "Store Layout", "Layout", "Improved sightlines and barrier placement", 5000, 12),
        ("SCP-0004", "System Rules", "System", "Inventory system audit improvements", 1000, 5),
        ("SCP-0005", "Take-Back", "Control", "In-store take-back programme", 3000, 3),
    ]
    for prog_id, name, control_type, desc, cost, reduction in shrink_programmes:
        shrink_control_programmes.append({
            "prog_id": prog_id,
            "programme_name": name,
            "control_type": control_type,
            "description": desc,
            "annual_cost_gbp": cost,
            "estimated_shrink_reduction_pct": reduction,
        })
    
    # Generate data for each month in the last year + next month
    for month_offset in range(-13, 1):
        month_date_val = g.days_ago(-month_offset * 30)
        if isinstance(month_date_val, datetime):
            month_date_val = month_date_val.date()
        month_date = month_date_val.replace(day=1)  # First day of month
        
        for store in stores:
            store_id = store["site_id"]
            
            # Generate KPIs for each store-month
            base_shrink = r.uniform(0.5, 4.0)
            base_availability = r.uniform(92, 98)
            base_labour = r.uniform(8, 16)
            
            # Add some variance by cluster
            if store["cluster"] == "A":
                base_shrink -= 0.5
                base_availability += 1
            elif store["cluster"] == "D":
                base_shrink += 0.5
                base_availability -= 1
            
            store_kpis.append({
                "site_id": store_id,
                "month": month_date,
                "shrink_pct": round(max(0.1, base_shrink), 2),
                "availability_pct": round(max(90, min(99, base_availability)), 1),
                "labour_cost_pct": round(base_labour, 1),
                "footfall": r.randint(3000, 45000),
                "sales_gbp": round(r.uniform(8000, 250000), 2),
                "margin_pct": round(r.uniform(25, 45), 1),
            })
            
            # Plan vs actual for each month
            plan_sales = round(r.uniform(80000, 300000), 2)
            actual_sales = round(plan_sales * r.uniform(0.85, 1.15), 2)
            variance = actual_sales - plan_sales
            variance_pct = round((variance / plan_sales * 100) if plan_sales else 0, 1)
            
            plan_vs_actual.append({
                "site_id": store_id,
                "month": month_date,
                "sales_plan_gbp": plan_sales,
                "sales_actual_gbp": actual_sales,
                "variance_gbp": round(variance, 2),
                "variance_pct": variance_pct,
                "margin_plan_pct": round(r.uniform(28, 42), 1),
                "margin_actual_pct": round(r.uniform(26, 44), 1),
            })
            
            # Backroom constraints (one per store)
            if month_offset == -1:  # Only generate once
                total_sqft = 500 + int(int(store["sqft"]) * 0.15)
                backroom_constraints.append({
                    "site_id": store_id,
                    "total_backroom_sqft": total_sqft,
                    "available_sqft": round(total_sqft * r.uniform(0.3, 0.7)),
                    "racking_capacity_pallets": r.randint(50, 200),
                    "bulk_floor_capacity_pallets": r.randint(20, 80),
                    "chilled_space_sqft": round(total_sqft * r.uniform(0.1, 0.25)),
                    "hazmat_compliance": r.choice([True, True, False]),
                    "take_back_space_available": r.choice([True, True, True, False]),
                })
    
    # Generate visits (recent weeks)
    employees = g.master("employees")
    area_managers = [e for e in employees if e.get("role") in ["Area Manager", "Store Manager"]]
    if not area_managers:
        area_managers = employees[:10]
    
    visit_id = 1
    for store in stores:
        if r.random() < 0.6:  # 60% of stores have a visit in the period
            num_visits = r.randint(1, 3)
            for _ in range(num_visits):
                visit_date_val = g.days_ago(r.randint(1, 60))
                if isinstance(visit_date_val, datetime):
                    visit_date_val = visit_date_val.date()
                store_visits.append({
                    "visit_id": f"VIS-{visit_id:06d}",
                    "site_id": store["site_id"],
                    "employee_id": r.choice(area_managers)["employee_id"],
                    "visit_date": visit_date_val,
                    "visit_purpose": r.choice([
                        "Quarterly performance review",
                        "Shrink investigation",
                        "Staff training",
                        "New initiative rollout",
                        "Mystery shopper follow-up",
                    ]),
                    "issues_found": r.randint(0, 8),
                    "actions_raised": r.randint(0, 5),
                    "duration_hours": round(r.uniform(2, 6), 1),
                    "status": r.choice(["completed", "completed", "planned"]),
                    "notes": g.fake.sentence(),
                    "updated_at": datetime.now(),
                })
                visit_id += 1
    
    # Generate action plans
    api_id = 1
    for store in stores:
        if r.random() < 0.7:  # 70% of stores have action items
            num_actions = r.randint(1, 4)
            for _ in range(num_actions):
                created_at_val = g.days_ago(r.randint(5, 90))
                if isinstance(created_at_val, datetime):
                    created_at_val = created_at_val.date()
                due_date = created_at_val + timedelta(days=r.randint(7, 45))
                action_plans.append({
                    "action_id": f"API-{api_id:06d}",
                    "site_id": store["site_id"],
                    "title": r.choice([
                        "Review RFID tagging of high-theft items",
                        "Implement daily floor walk routine",
                        "Audit stock counts for category",
                        "Staff training on loss prevention",
                        "Improve receiving process controls",
                        "Enhance front-end POS monitoring",
                        "Reorganize high-shrink category layout",
                    ]),
                    "owner": r.choice(area_managers)["employee_id"] if area_managers else "EMP-00001",
                    "due_date": due_date,
                    "status": r.choice(["open", "open", "in_progress"]),
                    "priority": r.choice(["low", "medium", "high"]),
                    "category": r.choice(["Shrink", "Availability", "Labour", "Safety"]),
                    "created_at": datetime.now(),
                    "completed_at": None,
                })
                api_id += 1
    
    # Generate weekly tasks for current and next weeks
    task_id = 1
    for store in stores:
        for weeks_offset in range(-2, 2):
            week_start_val = g.days_ago(-weeks_offset * 7)
            if isinstance(week_start_val, datetime):
                week_start_val = week_start_val.date()
            # Find the Monday of this week
            week_start = week_start_val - timedelta(days=week_start_val.weekday())
            
            # Typically 3-5 tasks per week
            num_tasks = r.randint(2, 5)
            for i in range(num_tasks):
                task_date = week_start + timedelta(days=r.randint(0, 6))
                task_type = r.choice(["Delivery", "Cycle Count", "Replenishment", "Maintenance", "Training"])
                
                week_tasks.append({
                    "task_id": f"TSK-{task_id:06d}",
                    "site_id": store["site_id"],
                    "week_start": week_start,
                    "task_name": f"{task_type} task",
                    "task_type": task_type,
                    "employee_id": r.choice(employees)["employee_id"] if employees else "EMP-00001",
                    "scheduled_date": task_date,
                    "scheduled_start_time": f"{r.choice([6, 7, 14, 18]):02d}:00",
                    "scheduled_duration_hours": round(r.uniform(1, 4), 1),
                    "status": r.choice(["scheduled", "completed", "scheduled"]),
                    "notes": g.fake.sentence() if r.random() < 0.3 else None,
                })
                task_id += 1
    
    # Generate cycle count tasks
    skus = g.master("products")[:50]  # Sample of SKUs
    cyc_id = 1
    for store in stores:
        if r.random() < 0.5:  # 50% of stores have cycle counts
            num_counts = r.randint(1, 3)
            for _ in range(num_counts):
                sku = r.choice(skus)
                count_date_val = g.days_ago(r.randint(-14, 7))
                if isinstance(count_date_val, datetime):
                    count_date_val = count_date_val.date()
                cyc_id_str = f"CYC-{cyc_id:06d}"
                
                system_qty = r.randint(10, 500)
                counted_qty = system_qty + r.randint(-20, 30)
                
                cycle_count_tasks.append({
                    "cycle_id": cyc_id_str,
                    "site_id": store["site_id"],
                    "sku": sku["sku"],
                    "location_id": None,
                    "category": sku.get("category", "General"),
                    "count_date": count_date_val,
                    "reason": r.choice(["Shrink investigation", "Stock taking", "Delivery variance", "Ad-hoc check"]),
                    "status": r.choice(["pending", "completed", "pending"]),
                    "system_quantity": system_qty,
                    "counted_quantity": counted_qty if r.random() < 0.6 else None,
                    "variance": counted_qty - system_qty if r.random() < 0.6 else None,
                    "created_at": datetime.now(),
                })
                cyc_id += 1
    
    # Shelf availability exceptions
    sae_id = 1
    for store in stores:
        if r.random() < 0.6:  # 60% of stores have exceptions
            num_exceptions = r.randint(1, 5)
            for _ in range(num_exceptions):
                sku = r.choice(skus)
                exc_date_val = g.days_ago(r.randint(-7, 1))
                if isinstance(exc_date_val, datetime):
                    exc_date_val = exc_date_val.date()
                
                shelf_availability_exceptions.append({
                    "exc_id": f"SAE-{sae_id:06d}",
                    "site_id": store["site_id"],
                    "sku": sku["sku"],
                    "exception_date": exc_date_val,
                    "status": r.choice(["open", "resolved"]),
                    "location": f"Aisle {r.randint(1, 12)}" if r.random() < 0.7 else None,
                    "system_stock": r.randint(5, 100),
                    "observed_on_shelf": r.randint(0, 10),
                    "likely_cause": r.choice(["Backroom", "Delivery pending", "Stock audit", "Damage"]),
                    "created_at": datetime.now(),
                })
                sae_id += 1
    
    # Replenishment priorities - track keys to avoid duplicates
    seen_replenishment_keys = set()
    for _ in range(len(stores) * 2):  # ~2 per store, carefully
        store = r.choice(stores)
        sku = r.choice(skus)
        key = (store["site_id"], sku["sku"])
        if key in seen_replenishment_keys:
            continue
        seen_replenishment_keys.add(key)
        
        effective_from_val = g.days_ago(r.randint(1, 30))
        if isinstance(effective_from_val, datetime):
            effective_from_val = effective_from_val.date()
        replenishment_priorities.append({
            "site_id": store["site_id"],
            "sku": sku["sku"],
            "priority_level": r.randint(1, 5),
            "reason": r.choice(["High shrink", "High demand", "Low availability", "Customer feedback"]),
            "effective_from": effective_from_val,
            "updated_at": datetime.now(),
        })
    
    # Click & collect demand - limit to recent 3 days and fewer SKUs
    seen_c2c_keys = set()
    for day_offset in range(-3, 0):
        date_val = g.days_ago(-day_offset)
        if isinstance(date_val, datetime):
            date_val = date_val.date()
        # Only for top 10 stores and 10 SKUs
        for store in r.sample(stores, min(10, len(stores))):
            for sku in r.sample(skus, min(10, len(skus))):
                key = (store["site_id"], sku["sku"], date_val)
                if key in seen_c2c_keys:
                    continue
                seen_c2c_keys.add(key)
                
                click_collect_demand.append({
                    "site_id": store["site_id"],
                    "sku": sku["sku"],
                    "date": date_val,
                    "forecasted_demand": r.randint(0, 50),
                    "actual_demand": r.randint(0, 60),
                    "reserved_quantity": r.randint(0, 30),
                    "online_allocation": r.randint(0, 100),
                })
    
    # Take-back pilot results
    pilot_stores = r.sample([s["site_id"] for s in stores], min(3, len(stores)))
    tbp_id = 1
    for site_id in pilot_stores:
        pilot_start_val = g.days_ago(r.randint(60, 180))
        if isinstance(pilot_start_val, datetime):
            pilot_start_val = pilot_start_val.date()
        pilot_end = pilot_start_val + timedelta(days=r.randint(30, 120))
        take_back_pilot_results.append({
            "pilot_id": f"TBP-{tbp_id:06d}",
            "site_id": site_id,
            "pilot_start": pilot_start_val,
            "pilot_end": pilot_end,
            "backroom_space_sqft": round(r.uniform(100, 300)),
            "monthly_participation_pct": round(r.uniform(10, 35), 1),
            "items_collected": r.randint(500, 3000),
            "total_weight_kg": round(r.uniform(200, 1500), 1),
            "carbon_savings_kg": round(r.uniform(50, 300), 1),
            "customer_satisfaction_score": round(r.uniform(3.5, 4.9), 1),
        })
        tbp_id += 1
    
    # Store control results (one per store per programme per month, recent months)
    for month_offset in range(-3, 0):
        month_date_val = g.days_ago(-month_offset * 30)
        if isinstance(month_date_val, datetime):
            month_date_val = month_date_val.date()
        month_date = month_date_val.replace(day=1)
        
        for store in r.sample(stores, min(20, len(stores))):
            for prog in r.sample(shrink_programmes, min(2, len(shrink_programmes))):
                prog_id = prog[0]
                control_cost = prog[4]
                store_control_results.append({
                    "site_id": store["site_id"],
                    "prog_id": prog_id,
                    "month": month_date,
                    "control_cost_gbp": round(control_cost * r.uniform(0.8, 1.2)),
                    "shrink_reduction_gbp": round(r.uniform(100, 5000)),
                    "payback_ratio": round(r.uniform(0.5, 8), 2),
                })
    
    return {
        "store_kpis": store_kpis,
        "store_visits": store_visits,
        "action_plans": action_plans,
        "week_tasks": week_tasks,
        "cycle_count_tasks": cycle_count_tasks,
        "shelf_availability_exceptions": shelf_availability_exceptions,
        "replenishment_priorities": replenishment_priorities,
        "click_collect_demand": click_collect_demand,
        "shrink_control_programmes": shrink_control_programmes,
        "take_back_pilot_results": take_back_pilot_results,
        "backroom_constraints": backroom_constraints,
        "plan_vs_actual": plan_vs_actual,
        "store_control_results": store_control_results,
    }
