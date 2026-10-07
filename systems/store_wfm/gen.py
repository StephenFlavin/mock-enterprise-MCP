"""Background workforce data: rotas, shifts, labour standards and staff availability."""
from datetime import datetime, time, timedelta


def generate(g):
    r = g.rng

    # Get store employees
    employees = [e for e in g.master("employees") if e["site_id"].startswith("ST")]
    stores = [s for s in g.master("sites") if s["type"] == "store"][:10]  # Limit to first 10 stores

    rotas, shifts, availability = [], [], []

    # Generate rotas for the last 8 weeks and next 2 weeks
    for week_offset in range(-8, 2):
        week_start = datetime.combine(g.weeks(1)[0], time(0, 0)) + timedelta(weeks=week_offset)
        week_start = week_start.date()

        for store in stores:
            # Get employees at this store
            store_employees = [e for e in employees if e["site_id"] == store["site_id"]]
            if not store_employees:
                continue

            rota_id = f"ROT-{len(rotas) + 1:06d}"
            past = week_start < g.as_of
            rota_status = r.choice(["completed", "published"]) if past else r.choice(["draft", "approved"])

            rotas.append({
                "rota_id": rota_id,
                "site_id": store["site_id"],
                "week_start": week_start,
                "status": rota_status,
                "approved_by": r.choice(store_employees)["employee_id"] if past else None,
                "approved_at": (datetime.combine(week_start, time(9, 0)) - timedelta(days=3)) if past else None,
                "updated_at": datetime.combine(week_start, time(8, 0)) - timedelta(days=5),
                "total_hours": 0
            })

            # Generate shifts for this rota (2-3 shifts per employee per week)
            total_hours = 0
            for emp in r.sample(store_employees, min(8, len(store_employees))):
                days_worked = r.randint(3, 5)
                for _ in range(days_worked):
                    day_of_week = r.randint(0, 6)
                    shift_hours = r.choice([4, 6, 8, 8.5])
                    start_hour = r.choice([7, 8, 9, 10])

                    shift_start = datetime.combine(
                        week_start + timedelta(days=day_of_week),
                        time(start_hour, 0)
                    )
                    shift_end = shift_start + timedelta(hours=shift_hours)

                    task_category = r.choice(["shelf", "till", "receiving", "stock", "checkout", "relabel", "cleaning"])

                    shifts.append({
                        "shift_id": f"SFT-{len(shifts) + 1:06d}",
                        "rota_id": rota_id,
                        "employee_id": emp["employee_id"],
                        "day_of_week": day_of_week,
                        "shift_start": shift_start,
                        "shift_end": shift_end,
                        "task_category": task_category,
                        "hours_worked": shift_hours,
                        "status": "scheduled",
                        "updated_at": datetime.combine(week_start, time(8, 0)) - timedelta(days=5)
                    })
                    total_hours += shift_hours

            rotas[-1]["total_hours"] = round(total_hours, 1)

            # Generate availability records for this week
            for emp in store_employees:
                days_off = r.choices(range(7), k=r.randint(0, 2))
                availability.append({
                    "availability_id": f"AVL-{len(availability) + 1:06d}",
                    "employee_id": emp["employee_id"],
                    "week_start": week_start,
                    "monday_available": 0 not in days_off,
                    "tuesday_available": 1 not in days_off,
                    "wednesday_available": 2 not in days_off,
                    "thursday_available": 3 not in days_off,
                    "friday_available": 4 not in days_off,
                    "saturday_available": 5 not in days_off,
                    "sunday_available": 6 not in days_off,
                    "notes": r.choice(["", "", "", "Requested time off", "Sick leave"]),
                    "updated_at": datetime.combine(week_start, time(8, 0)) - timedelta(days=7)
                })

    # Labour standards
    standards = [
        {"standard_id": "STD-000001", "task_category": "receiving", "description": "Unload and process delivery", "standard_hours": 2.0, "unit_of_measure": "per delivery"},
        {"standard_id": "STD-000002", "task_category": "shelf", "description": "Stock shelves with merchandise", "standard_hours": 1.0, "unit_of_measure": "per 1000 units"},
        {"standard_id": "STD-000003", "task_category": "till", "description": "Till operation and customer service", "standard_hours": 1.0, "unit_of_measure": "per shift"},
        {"standard_id": "STD-000004", "task_category": "stock", "description": "Stock take and stock checking", "standard_hours": 3.0, "unit_of_measure": "per count"},
        {"standard_id": "STD-000005", "task_category": "checkout", "description": "Checkout staff", "standard_hours": 1.0, "unit_of_measure": "per shift"},
        {"standard_id": "STD-000006", "task_category": "relabel", "description": "Price relabeling", "standard_hours": 0.5, "unit_of_measure": "per 100 items"},
        {"standard_id": "STD-000007", "task_category": "cleaning", "description": "Store cleaning and maintenance", "standard_hours": 2.0, "unit_of_measure": "per shift"},
    ]

    # Labour costs by store/week
    labour_costs = []
    for week_offset in range(-8, 2):
        week_start = datetime.combine(g.weeks(1)[0], time(0, 0)) + timedelta(weeks=week_offset)
        week_start = week_start.date()

        for store in stores:
            # Find rota for this store and week
            rota = next((ro for ro in rotas if ro["site_id"] == store["site_id"] and ro["week_start"] == week_start), None)
            if not rota:
                continue

            total_hours = rota["total_hours"]
            avg_hourly_rate = r.uniform(11.5, 14.5)
            total_cost = round(total_hours * avg_hourly_rate, 2)

            # Generate sales for the week
            store_employees = [e for e in employees if e["site_id"] == store["site_id"]]
            sales = round(r.uniform(3000, 15000), 2) if store_employees else 0

            labour_pct = round((total_cost / sales * 100), 1) if sales > 0 else 0

            labour_costs.append({
                "site_id": store["site_id"],
                "week_start": week_start,
                "total_hours": round(total_hours, 1),
                "total_labour_cost_gbp": total_cost,
                "average_hourly_rate_gbp": round(avg_hourly_rate, 2),
                "sales_value_gbp": sales,
                "labour_cost_pct": labour_pct,
                "updated_at": datetime.combine(week_start, time(9, 0))
            })

    return {
        "staff_rotas": rotas,
        "rota_shifts": shifts,
        "labour_standards": standards,
        "staff_availability": availability,
        "labour_costs": labour_costs
    }
