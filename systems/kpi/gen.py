"""Generate KPI targets, weekly actuals, variances, site metrics, circularity targets, root causes and alerts.

Story (all relative to g.as_of, the latest Monday):
- Four-week periods k=0 (latest) .. 5. Over the last 12 weeks five headline KPIs have slipped:
  lost-time injuries (DC2), stock turnover days, waste diversion, cost per unit, OTIF.
- ST214 (Glasgow Retail Park) and DC2 (Daventry DC) are the two worst sites; DC1 (Northampton) is third, missing cost and safety (same as hse and budgeting 09:88:Q1).
- Circularity: units collected / value recovered weekly KPIs with fixed 52-week totals for YoY.
"""
import math
from datetime import datetime, timedelta

# id, name, domain, unit, target (per week), better_when, aggregation, decimals, weekly noise (fraction of target)
KPIS = [
    ("KPI-0001", "On-Time-In-Full (OTIF)", "service", "%", 95.5, "higher", "avg", 1, 0.004),
    ("KPI-0002", "Cost per Unit Handled", "cost", "£", 2.35, "lower", "avg", 2, 0.006),
    ("KPI-0003", "Inventory Accuracy", "inventory", "%", 98.5, "higher", "avg", 1, 0.002),
    ("KPI-0004", "Stock Turnover Days", "inventory", "days", 28.0, "lower", "avg", 1, 0.006),
    ("KPI-0005", "Lost Time Injury Frequency", "safety", "rate", 0.5, "lower", "avg", 2, 0.03),
    ("KPI-0006", "Quality First Pass", "quality", "%", 96.5, "higher", "avg", 1, 0.003),
    ("KPI-0007", "Supplier OTIF", "service", "%", 94.0, "higher", "avg", 1, 0.004),
    ("KPI-0008", "GHG Emissions per Unit", "sustainability", "kg CO2e", 0.85, "lower", "avg", 2, 0.008),
    ("KPI-0009", "Waste Diversion Rate", "sustainability", "%", 72.0, "higher", "avg", 1, 0.004),
    ("KPI-0010", "DC Throughput", "service", "units/hr", 850.0, "higher", "avg", 0, 0.006),
    ("KPI-0011", "Circularity Units Collected", "sustainability", "units", 1000.0, "higher", "sum", 0, 0.03),
    ("KPI-0012", "Circularity Value Recovered", "sustainability", "£", 5000.0, "higher", "sum", 0, 0.03),
]

# actual / target factor for the four-week periods k = 0 (latest) .. 5
FACTORS = {
    "KPI-0001": [0.9466, 0.965, 0.985, 0.995, 0.998, 1.0],
    "KPI-0002": [1.068, 1.05, 1.03, 1.01, 1.0, 0.99],
    "KPI-0003": [0.996, 0.998, 1.0, 0.999, 1.0, 1.001],
    "KPI-0004": [1.1214, 1.09, 1.06, 1.02, 1.0, 0.99],
    "KPI-0005": [1.54, 1.32, 1.12, 1.04, 1.0, 0.96],
    "KPI-0006": [0.992, 0.995, 0.996, 0.998, 1.0, 1.0],
    "KPI-0007": [0.985, 0.99, 0.995, 1.0, 1.0, 1.0],
    "KPI-0008": [1.03, 1.02, 1.01, 1.0, 1.0, 0.99],
    "KPI-0009": [0.919, 0.945, 0.97, 0.99, 0.995, 1.0],
    "KPI-0010": [1.02, 1.01, 1.0, 0.99, 1.0, 1.01],
    "KPI-0011": [0.98, 0.97, 0.97, 0.96, 0.96, 0.95],
    "KPI-0012": [0.98, 0.97, 0.96, 0.96, 0.95, 0.95],
}
# 52-week totals for the summed circularity KPIs: (this year, prior year)
YEAR_TOTALS = {"KPI-0011": (49400, 40100), "KPI-0012": (245000, 190000)}

# Root causes for the latest-period (k=0) variances
CAUSES = {
    "KPI-0005": dict(
        site_id="DC2", severity="critical", dept="Operations", weeks=6, status="action_raised",
        cause="Forklift injuries at Daventry DC (DC2) after the peak temporary-labour intake; MHE refresher training not completed",
        factors="Agency staff started without MHE refresher; Night-shift aisle congestion; Two near-miss reports not escalated"),
    "KPI-0004": dict(
        site_id="", severity="high", dept="Supply Chain", weeks=28, status="open",
        cause="Excess seasonal stock landed ahead of peak; slow-moving lines sit well above cover targets",
        factors="Supplier minimum order quantities; Autumn range forecast over-called; Clearance plan not yet agreed"),
    "KPI-0009": dict(
        site_id="", severity="medium", dept="Sustainability", weeks=32, status="in_progress",
        cause="Regional recycling processor capped cardboard and plastics intake; overflow sent to residual waste",
        factors="Waste contract renegotiation pending; Contamination in mixed-waste skips"),
    "KPI-0002": dict(
        site_id="", severity="medium", dept="Operations", weeks=8, status="in_progress",
        cause="Peak-season overtime and agency labour driving up handling cost per unit",
        factors="Volume running ahead of forecast; Slow pick rate on the new returns flow"),
    "KPI-0001": dict(
        site_id="", severity="medium", dept="Logistics", weeks=9, status="action_raised",
        cause="Carrier capacity shortfall on store replenishment lanes and short-picks on promotional lines",
        factors="Two carriers declined peak loads; Promo stock allocated late to DCs"),
}


def severity_of(adverse_pct):
    if adverse_pct > 10:
        return "severe"
    if adverse_pct > 5:
        return "moderate"
    if adverse_pct > 2:
        return "minor"
    return "on_track"


def generate(g):
    r = g.rng
    as_of = g.as_of
    mid = datetime.min.time()

    def ts(d):
        return datetime.combine(d, mid)

    # ---- targets ------------------------------------------------------------------------
    kpi_targets = []
    for kid, name, domain, unit, target, better, agg, dp, noise in KPIS:
        if better == "higher":
            min_t, yellow_t = target * 0.90, target * 0.95
        else:
            min_t, yellow_t = target * 1.10, target * 1.05
        kpi_targets.append({
            "kpi_id": kid, "kpi_name": name, "domain": domain, "frequency": "weekly", "unit": unit,
            "better_when": better, "aggregation": agg,
            "target_value": round(target, 2), "min_threshold": round(min_t, 3),
            "yellow_threshold": round(yellow_t, 3),
            "effective_from": as_of - timedelta(days=300),
            "updated_at": ts(as_of - timedelta(days=90)),
        })

    # ---- weekly actuals (week i is i weeks before as_of; 104 weeks) --------------------
    weeks_n = 104
    series = {}
    for kid, name, domain, unit, target, better, agg, dp, noise in KPIS:
        fac = FACTORS[kid]
        vals = []
        for i in range(weeks_n):
            if i < 24:
                f = fac[i // 4]
            else:
                f = 1.0
            vals.append(target * f * (1 + r.gauss(0, noise)))
        # force each four-week period (k0..k5) to its exact mean factor
        for k in range(6):
            seg = vals[4 * k:4 * k + 4]
            adj = target * fac[k] - sum(seg) / 4
            for j in range(4):
                vals[4 * k + j] += adj
        if agg == "sum":
            this_total, prior_total = YEAR_TOTALS[kid]
            fixed = sum(vals[:24])
            rest = vals[24:52]
            scale = (this_total - fixed) / sum(rest)
            vals[24:52] = [v * scale for v in rest]
            prior = vals[52:104]
            pscale = prior_total / sum(prior)
            vals[52:104] = [v * pscale for v in prior]
            vals = [round(v) for v in vals]
            vals[51] += this_total - sum(vals[:52])
            vals[103] += prior_total - sum(vals[52:104])
        else:
            vals = [round(v, dp) for v in vals]
        series[kid] = vals

    kpi_actuals = []
    meta = {k[0]: k for k in KPIS}
    for kid, vals in series.items():
        _, name, domain, unit, target, better, agg, dp, noise = meta[kid]
        run_sum, run_n, run_year = 0.0, 0, None
        for i in range(weeks_n - 1, -1, -1):  # oldest first
            d = as_of - timedelta(days=7 * i)
            if d.year != run_year:
                run_sum, run_n, run_year = 0.0, 0, d.year
            run_sum += vals[i]
            run_n += 1
            ytd = run_sum if agg == "sum" else run_sum / run_n
            note = ""
            dq = "good" if r.random() > 0.08 else "estimated"
            kpi_actuals.append({
                "kpi_id": kid, "measured_date": d, "actual_value": vals[i],
                "ytd_value": round(ytd, 2), "vs_target_pct": round(vals[i] / target * 100, 1),
                "data_quality": dq, "notes": note,
            })

    # ---- variances (four-week periods, k=0 latest) --------------------------------------
    kpi_variances = []
    variance_of = {}
    for k in range(5, -1, -1):
        period_end = as_of - timedelta(days=28 * k)
        for kid, name, domain, unit, target, better, agg, dp, noise in KPIS:
            seg = series[kid][4 * k:4 * k + 4]
            actual = math.floor(sum(seg) / 4 * 100 + 0.5) / 100
            var = actual - target
            pct = var / target * 100
            adverse = pct if better == "lower" else -pct
            sev = severity_of(adverse)
            vid = f"VAR-{len(kpi_variances) + 1:06d}"
            variance_of[(kid, k)] = vid
            if k == 0:
                status = {"KPI-0005": "action_raised", "KPI-0004": "investigating", "KPI-0009": "investigating",
                          "KPI-0002": "root_cause_identified", "KPI-0001": "action_raised"}.get(kid, "open" if sev != "on_track" else "resolved")
            else:
                status = "resolved"
            kpi_variances.append({
                "variance_id": vid, "kpi_id": kid,
                "period_start": period_end - timedelta(days=27), "period_end": period_end,
                "target_value": round(target, 2), "actual_value": actual,
                "variance_value": round(var, 2), "variance_pct": round(pct, 1),
                "severity": sev, "status": status, "updated_at": ts(as_of),
            })

    # ---- root causes for the latest period ----------------------------------------------
    issue_root_causes = []
    for kid, c in CAUSES.items():
        issue_root_causes.append({
            "cause_id": f"CAS-{len(issue_root_causes) + 1:06d}",
            "variance_id": variance_of[(kid, 0)], "kpi_id": kid, "site_id": c["site_id"],
            "root_cause": c["cause"], "contributing_factors": c["factors"],
            "department_responsible": c["dept"], "severity": c["severity"],
            "identified_at": ts(as_of - timedelta(days=10)),
            "target_fix_date": as_of + timedelta(weeks=c["weeks"]),
            "status": c["status"], "updated_at": ts(as_of - timedelta(days=2)),
        })

    # ---- site metrics (weekly, 13 weeks, DCs + stores) -----------------------------------
    sites = [s for s in g.master("sites") if s["type"] in ("dc", "store")]
    story = {
        # latest-week values for the two worst sites; earlier weeks drift towards normal
        "ST214": dict(service=88.5, cost=3.12, ltif=1.2, fp=92.1, acc=95.5, oh=32),
        "DC2": dict(service=95.8, cost=2.45, ltif=0.8, fp=94.5, acc=97.1, oh=-25),
    }
    normal = dict(service=97.0, cost=2.15, ltif=0.3, fp=97.8, acc=99.1, oh=0)
    site_ids = [s["site_id"] for s in sites]
    decoys = {sid: r.choice(["service", "cost", "fp"]) for sid in r.sample([s for s in site_ids if s not in story and s.startswith("ST")], 6)}
    site_metrics = []
    for s in sites:
        sid = s["site_id"]
        for i in range(12, -1, -1):
            d = as_of - timedelta(days=7 * i)
            if sid in story:
                w = max(0.0, 1 - i / 8.0)  # 1 at latest week, 0 from 8 weeks ago
                tgt = story[sid]
                v = {k: normal[k] + (tgt[k] - normal[k]) * w for k in tgt}
                if sid == "DC2":
                    v["service"] = 96.4 + (tgt["service"] - 96.4) * w
                    v["cost"] = 2.2 + (tgt["cost"] - 2.2) * w
                row = dict(service=round(v["service"], 1), cost=round(v["cost"], 2), ltif=round(v["ltif"], 2),
                           fp=round(v["fp"], 1), acc=round(v["acc"], 1), oh=int(round(v["oh"])))
            else:
                row = dict(service=round(r.uniform(95.7, 98.8), 1), cost=round(r.uniform(1.95, 2.3), 2),
                           ltif=round(r.uniform(0.15, 0.45), 2), fp=round(r.uniform(96.6, 98.9), 1),
                           acc=round(r.uniform(98.6, 99.6), 1), oh=r.randint(-12, 12))
                if sid in decoys and i < 4:
                    m = decoys[sid]
                    if m == "service":
                        row["service"] = round(r.uniform(93.8, 94.8), 1)
                    elif m == "cost":
                        row["cost"] = round(r.uniform(2.45, 2.6), 2)
                    else:
                        row["fp"] = round(r.uniform(94.8, 95.8), 1)
                if sid == "DC1":    # Northampton: HSE's worst DC for incidents and the 09:87:Q5 cost per unit +18% story (service and quality stay on target)
                    w = max(0.0, 1 - i / 8.0)
                    row["cost"] = round(2.2 + (2.54 - 2.2) * w, 2)
                    row["ltif"] = round(0.3 + (0.65 - 0.3) * w, 2)
            site_metrics.append({
                "site_id": sid, "measured_date": d, "service_score": row["service"],
                "cost_per_unit_gbp": row["cost"], "safety_ltif": row["ltif"],
                "quality_first_pass_pct": row["fp"], "stock_accuracy_pct": row["acc"], "oh_es": row["oh"],
            })

    # ---- circularity channel targets (annual) --------------------------------------------
    circularity_targets = []
    for idx, (ch, units, value, cost) in enumerate([
        ("Reuse", 13000, 104000.0, 1.20), ("Repair", 6500, 52000.0, 3.00),
        ("Recycle", 28000, 28000.0, 0.60), ("Refurbish", 4500, 76000.0, 5.00)]):
        circularity_targets.append({
            "channel_id": f"CHN-{idx + 1:06d}", "channel_name": ch, "units_collected_target": units,
            "value_recovered_target_gbp": value, "handling_cost_per_unit_gbp": cost,
            "effective_from": as_of - timedelta(days=300),
        })

    # ---- alert thresholds (red = worst acceptable value, amber = warning) -----------------
    alert_thresholds = []
    for t in kpi_targets:
        on = "below" if t["better_when"] == "higher" else "above"
        for level, val in (("red", t["min_threshold"]), ("amber", t["yellow_threshold"])):
            alert_thresholds.append({
                "alert_id": f"ALT-{len(alert_thresholds) + 1:06d}", "kpi_id": t["kpi_id"],
                "alert_level": level, "threshold_value": round(val, 3), "alert_on": on, "enabled": True,
                "last_breached_at": ts(as_of - timedelta(days=3)) if t["kpi_id"] in ("KPI-0005", "KPI-0004") and level == "amber" else None,
                "updated_at": ts(as_of - timedelta(days=90)),
            })

    return {
        "kpi_targets": kpi_targets, "kpi_actuals": kpi_actuals, "kpi_variances": kpi_variances,
        "site_metrics": site_metrics, "circularity_targets": circularity_targets,
        "issue_root_causes": issue_root_causes, "alert_thresholds": alert_thresholds,
    }
