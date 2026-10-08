"""Python tools for store workforce management calculations."""
import math
from datetime import date, timedelta

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
OPEN_HOURS = list(range(9, 21))  # store trades 09:00-21:00

# Share of the week's footfall by day and of each day's footfall by hour (from the store footfall forecast shape).
DAY_SHARE = [1703, 1715, 1842, 1921, 2319, 3368, 2452]
HOUR_SHAPE = {
    "weekday": [79, 75, 155, 157, 205, 203, 183, 186, 122, 120, 118, 112],
    "saturday": [164, 161, 308, 315, 383, 414, 340, 348, 240, 237, 227, 231],
    "sunday": [120, 119, 220, 223, 276, 289, 267, 278, 159, 171, 161, 169],
}
CUSTOMERS_PER_STAFF_HOUR = 70   # visitors one colleague can serve and keep the floor tidy in an hour
DELIVERY_START = 6              # deliveries arrive at 06:00, before the store opens
MIN_COVER = 2                   # never fewer than two colleagues while open (key holder plus till)


def _hhmm(t):
    h, m = str(t).split(":")
    return int(h) * 60 + int(m)


def calc_labour_requirement(ctx, site_id, week_start, forecast_footfall, delivery_days="tuesday,friday",
                            day=None, staff_off=0):
    d = date.fromisoformat(str(week_start)[:10])
    monday = d - timedelta(days=d.weekday())
    rota = ctx.q(
        "SELECT rota_id, status FROM staff_rotas WHERE site_id = $s AND week_start = CAST($w AS DATE) "
        "ORDER BY CASE status WHEN 'archived' THEN 1 ELSE 0 END, rota_id DESC LIMIT 1",
        s=site_id, w=monday.isoformat())
    if not rota:
        return f"No rota exists for {site_id} for the week starting {monday}; nothing to compare the requirement with."
    rota_id = rota[0]["rota_id"]
    std = ctx.q("SELECT standard_hours FROM labour_standards WHERE task_category = 'receiving' AND status = 'active'")
    receiving_hours = int(math.ceil(std[0]["standard_hours"])) if std else 2
    shifts = ctx.q(
        "SELECT shift_date, start_time, end_time, staff_id FROM rota_shifts WHERE rota_id = $r AND status <> 'cancelled'",
        r=rota_id)
    deliveries = {x.strip().lower() for x in str(delivery_days or "").split(",") if x.strip()}
    want_day = DAYS.index(day.capitalize()) if day else None
    staff_off = int(staff_off or 0)

    out = []
    for i, name in enumerate(DAYS):
        if want_day is not None and i != want_day:
            continue
        the_date = monday + timedelta(days=i)
        shape = HOUR_SHAPE["saturday" if i == 5 else "sunday" if i == 6 else "weekday"]
        day_ff = forecast_footfall * DAY_SHARE[i] / sum(DAY_SHARE)
        day_shifts = [s for s in shifts if str(s["shift_date"])[:10] == the_date.isoformat()]
        n_staff = len({s["staff_id"] for s in day_shifts})
        absent_factor = max(0.0, (n_staff - staff_off) / n_staff) if (want_day == i and staff_off and n_staff) else 1.0
        is_delivery = name.lower() in deliveries
        hours = ([DELIVERY_START + k for k in range(receiving_hours)] if is_delivery else []) + OPEN_HOURS
        for h in hours:
            open_ = h in OPEN_HOURS
            ff = day_ff * shape[h - 9] / sum(shape) if open_ else 0.0
            floor = max(MIN_COVER, math.ceil(ff / CUSTOMERS_PER_STAFF_HOUR)) if open_ else 0
            recv = 1 if (is_delivery and h < 9) else 0
            required = floor + recv
            rostered = sum(1 for s in day_shifts if _hhmm(s["start_time"]) <= h * 60 and _hhmm(s["end_time"]) >= (h + 1) * 60)
            rostered_after = round(rostered * absent_factor, 1)
            gap = round(rostered_after - required, 1)
            out.append({
                "site_id": site_id, "rota_id": rota_id, "date": the_date.isoformat(), "weekday": name,
                "hour": f"{h:02d}:00", "forecast_visitors": round(ff),
                "minimum_cover": MIN_COVER, "required_staff": required, "rostered_staff": rostered_after, "gap": gap,
                "status": "short" if gap < 0 else "over" if gap >= 2 else "ok",
                "note": "receiving before opening" if recv else "",
            })
    if not out:
        return "No hours to plan."
    short = sum(-r["gap"] for r in out if r["gap"] < 0)
    over = sum(r["gap"] for r in out if r["status"] == "over")
    out[0]["formula"] = (
        f"required = max({MIN_COVER}, ceil(hourly visitors / {CUSTOMERS_PER_STAFF_HOUR})) + 1 receiving person from "
        f"06:00 for {receiving_hours}h before opening on delivery days; hourly visitors = weekly forecast x day share x hour share; "
        f"with {staff_off} absent on the chosen day rostered = rostered x (staff that day - absent) / staff that day. "
        f"Total short {short:.1f} staff-hours, over (2+ spare) {over:.1f} staff-hours."
    )
    return out
