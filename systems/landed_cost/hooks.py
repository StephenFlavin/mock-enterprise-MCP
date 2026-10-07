"""calculate_landed_cost_per_unit: actual landed cost (with optional extra tariff) and priced freight routing options."""
from datetime import date, timedelta

INS_RATE, HANDLING_RATE, HOLDING_PA = 0.0065, 0.012, 0.15   # current rates: insurance and handling stepped up recently


def _r(v, n=2):
    return None if v is None else round(v, n)


def _row(basis, routing, base, mode, freight, units, uplift, p50=None, p95=None, rel=None, lead=None):
    fob = base["fob"]
    duty = fob * base["duty_rate"]
    ins = (fob + freight) * INS_RATE
    hand = (fob + freight) * HANDLING_RATE
    hold = fob * HOLDING_PA / 52.0 * max(1, (lead or p50 or 7) // 7)
    return _out(basis, routing, base, mode, fob, freight, duty, fob * uplift / 100.0, ins, hand, hold, units, p50, p95, rel)


def _out(basis, routing, base, mode, fob, freight, duty, uplift, ins, hand, hold, units, p50, p95, rel):
    landed = fob + freight + duty + uplift + ins + hand + hold
    return {
        "basis": basis, "routing": routing, "po_id": base.get("po_id"), "sku": base.get("sku"),
        "origin_country": base["origin_country"], "mode": mode, "units": units,
        "fob_unit_gbp": _r(fob), "freight_unit_gbp": _r(freight), "duty_unit_gbp": _r(duty),
        "tariff_uplift_unit_gbp": _r(uplift), "insurance_unit_gbp": _r(ins), "handling_unit_gbp": _r(hand),
        "inventory_holding_unit_gbp": _r(hold), "landed_cost_unit_gbp": _r(landed),
        "total_landed_cost_gbp": _r(landed * units, 0),
        "transit_days_p50": p50, "transit_days_p95": p95, "reliability_pct": rel,
        "formula": "landed = FOB + freight + duty + extra tariff (FOB x uplift%) + insurance + handling + inventory holding",
    }


def calc_landed_cost_per_unit(ctx, po_id=None, sku=None, category=None, origin_country=None, units=None, tariff_uplift_pct=0.0):
    uplift = float(tariff_uplift_pct or 0.0)
    date_from = date.fromisoformat(str(ctx.as_of)) - timedelta(days=180)
    rows = ctx.q(
        """SELECT l.po_id, l.sku, l.origin_country, l.mode, l.units, l.fob_unit_gbp, l.freight_unit_gbp, l.duty_unit_gbp,
                  l.insurance_unit_gbp, l.handling_unit_gbp, l.inventory_holding_unit_gbp, l.lead_time_days,
                  p.weight_kg, po.dest_site_id
           FROM landed_cost_summary l JOIN master.products p ON p.sku = l.sku
           LEFT JOIN master.purchase_orders po ON po.po_id = l.po_id
           WHERE ($po_id IS NULL OR l.po_id = $po_id) AND ($sku IS NULL OR l.sku = $sku)
             AND ($category IS NULL OR p.category = $category)
             AND ($origin_country IS NULL OR l.origin_country = $origin_country)
             AND CAST(l.updated_at AS DATE) >= $d
           ORDER BY l.updated_at DESC, l.units DESC""",
        po_id=po_id, sku=sku, category=category, origin_country=origin_country, d=date_from)
    if not rows:
        return "No landed cost records match these filters in the last 180 days."

    out = []
    if po_id or sku:
        # one row per PO line, actual cost; routing options for the largest matching line
        for r in rows[:10]:
            n = int(units) if (units and len(rows) == 1) else r["units"]
            out.append(_out("actual (booked)", f"{r['mode']} as booked", r, r["mode"], r["fob_unit_gbp"], r["freight_unit_gbp"],
                            r["duty_unit_gbp"], r["fob_unit_gbp"] * uplift / 100.0, r["insurance_unit_gbp"], r["handling_unit_gbp"],
                            r["inventory_holding_unit_gbp"], n, None, None, None) | {"transit_days_p50": r["lead_time_days"]})
        base = max(rows, key=lambda r: r["units"]) if not sku else rows[0]
        base = {**base, "fob": base["fob_unit_gbp"], "duty_rate": base["duty_unit_gbp"] / base["fob_unit_gbp"] if base["fob_unit_gbp"] else 0.0}
        n = int(units) if units else base["units"]
        opts = ctx.q(
            """SELECT routing, mode, rate_per_kg_gbp, transit_days_p50, transit_days_p95, reliability_pct
               FROM freight_rates
               WHERE origin_country = $o AND dest_site_id = $d AND min_qty <= $n
                 AND effective_from <= CAST($as_of AS DATE) AND (effective_to IS NULL OR effective_to >= CAST($as_of AS DATE))
               ORDER BY transit_days_p50""", o=base["origin_country"], d=base["dest_site_id"] or "DC1", n=n)
        by_mode = {}
        for o in opts:
            freight = o["rate_per_kg_gbp"] * float(base["weight_kg"])
            row = _row("quoted routing option", o["routing"], base, o["mode"], freight, n, uplift,
                       o["transit_days_p50"], o["transit_days_p95"], o["reliability_pct"])
            out.append(row)
            by_mode.setdefault(o["mode"], row)
        air, sea_air = by_mode.get("air"), by_mode.get("sea_air")
        if air and sea_air:
            w = 0.5
            blend = {k: (air[k] * w + sea_air[k] * (1 - w)) if isinstance(air[k], float) and k.endswith("_gbp") else air[k]
                     for k in air}
            blend.update({"basis": "quoted routing option", "mode": "split",
                          "routing": f"Split order: 50% {air['routing']}; 50% {sea_air['routing']}",
                          "transit_days_p50": air["transit_days_p50"], "transit_days_p95": sea_air["transit_days_p95"],
                          "reliability_pct": min(air["reliability_pct"], sea_air["reliability_pct"]),
                          "total_landed_cost_gbp": _r(((air["landed_cost_unit_gbp"] + sea_air["landed_cost_unit_gbp"]) / 2) * n, 0)})
            blend["landed_cost_unit_gbp"] = _r((air["landed_cost_unit_gbp"] + sea_air["landed_cost_unit_gbp"]) / 2)
            out.append(blend)
        return out

    # aggregate: units-weighted average by origin and mode
    groups = {}
    for r in rows:
        groups.setdefault((r["origin_country"], r["mode"]), []).append(r)
    for (origin, mode), rs in sorted(groups.items()):
        tot = sum(r["units"] for r in rs)
        def w(k):
            return sum(r[k] * r["units"] for r in rs) / tot
        n = int(units) if units else tot
        fob = w("fob_unit_gbp")
        row = _out("actual (units-weighted)", f"{len(rs)} PO lines, {mode}", {"origin_country": origin}, mode, fob, w("freight_unit_gbp"),
                   w("duty_unit_gbp"), fob * uplift / 100.0, w("insurance_unit_gbp"), w("handling_unit_gbp"),
                   w("inventory_holding_unit_gbp"), n, round(w("lead_time_days")), None, None)
        out.append(row)
    out.sort(key=lambda r: r["landed_cost_unit_gbp"])
    return out
