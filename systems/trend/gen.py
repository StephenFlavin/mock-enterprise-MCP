"""Generate trend data: trends, search interest, social mentions, sales trends, commodity prices, forecasts.

Series are deterministic shape functions plus small seeded noise, so the planted stories (quiet luxury falling,
oversized outerwear peaking, dopamine decor as a fad, K-1700 eight-week slide) are what a correct read finds.
"""
import math
from datetime import date, timedelta

MARKETS = ["UK", "US", "Germany"]


def _bump(t, tp, w, base, peak):
    """Gaussian rise and fall: t = weeks from now (<=0 is history), tp = peak week."""
    return base + (peak - base) * math.exp(-0.5 * ((t - tp) / w) ** 2)


# term: (category, trend shape (tp, w, base, peak), {market: (shift_weeks_earlier, scale)}, social mentions per index point,
#        sentiment (start, end))
LEAD = {  # weeks a market leads the UK (negative = lags)
    "Womenswear": {"UK": 0, "US": 10, "Germany": -6},
    "Home": {"UK": 0, "US": -4, "Germany": 14},
    "General": {"UK": 0, "US": 0, "Germany": 0},
}
SCALE = {"UK": 1.0, "US": 0.92, "Germany": 0.88}
MENTION_SCALE = {"UK": 1.0, "US": 2.0, "Germany": 0.7}

TERMS = {
    # Womenswear
    "quiet luxury": ("Womenswear", (-31, 16, 14, 86), 12, (60, 56)),
    "bold maximalism": ("Womenswear", (40, 30, 8, 80), 20, (70, 76)),
    "oversized outerwear": ("Womenswear", (4, 24, 18, 80), 36, (74, 62)),
    "chocolate brown": ("Womenswear", (25, 22, 15, 78), 22, (72, 76)),
    "butter yellow": ("Womenswear", (-14, 10, 10, 82), 28, (80, 58)),
    "boucle knitwear": ("Womenswear", (30, 36, 20, 70), 12, (68, 70)),
    "recycled wool": ("Womenswear", (55, 40, 12, 55), 6, (74, 80)),
    "wide leg trousers": ("Womenswear", (14, 30, 25, 74), 15, (70, 72)),
    # Home
    "wellness recovery": ("Home", (40, 34, 12, 88), 25, (72, 79)),
    "japandi": ("Home", (30, 40, 25, 70), 14, (74, 77)),
    "dopamine decor": ("Home", (3, 11, 8, 92), 38, (82, 61)),
    "sleep sanctuary": ("Home", (60, 45, 10, 75), 9, (70, 76)),
    # General
    "sustainable fashion": ("General", (0, 400, 55, 58), 20, (74, 76)),
}

# Core category terms for the top-ten categories: (department, search level now, 12w growth %, social level now, 12w growth %)
CATEGORY_TERMS = {
    "shirts": ("Menswear", 46, 2, 800, 1),
    "audio": ("Electricals", 72, 38, 3400, 45),
    "outerwear": ("Menswear", 64, 22, 2900, 25),
    "trousers": ("Menswear", 50, -2, 900, 0),
    "footwear": ("Accessories", 58, -18, 2600, 24),
    "babywear": ("Kids", 40, 3, 700, 2),
    "jewellery": ("Accessories", 55, 27, 1500, -15),
    "small appliances": ("Electricals", 61, 30, 1100, 1),
    "fragrance": ("Beauty", 68, 33, 4100, 40),
    "knitwear": ("Menswear", 52, 12, 1600, 10),
}


def generate(g):
    r = g.rng
    as_of = g.as_of
    d = lambda s: date.fromisoformat(s)

    def week_end(k):  # k weeks ago, Sunday before as_of (Monday)
        return as_of - timedelta(days=1 + 7 * k)

    # ---- Trends ----
    T = lambda *a: dict(zip(["trend_id", "name", "category", "dimension", "region", "lifecycle_stage", "staying_power",
                             "started_date", "peak_date", "forecast_end_date", "driving_segment", "search_term", "description"], a))
    trends = [
        T("TRD-000001", "Quiet Luxury", "Womenswear", "theme", "UK", "declining", "fad", "2023-06-15", "2026-03-01", "2027-06-01",
          "SEG-001 Premium Loyalists", "quiet luxury", "Premium understated aesthetics and quality-focused basics"),
        T("TRD-000002", "Oversized Outerwear", "Womenswear", "silhouette", "UK", "peak", "cyclical", "2024-09-01", "2026-11-01", "2027-06-01",
          "SEG-005 Trend Followers", "oversized outerwear", "Oversized silhouettes in coats and jackets"),
        T("TRD-000003", "Wellness & Recovery", "Home", "theme", "UK", "growing", "structural", "2025-01-01", "2027-09-01", "2029-01-01",
          "SEG-003 Conscious Shoppers", "wellness recovery", "Health-focused home products: sleep, recovery and relaxation"),
        T("TRD-000004", "Sustainable Materials", "General", "material", "UK", "growing", "structural", "2022-06-01", "2028-01-01", "2030-01-01",
          "SEG-003 Conscious Shoppers", "sustainable fashion", "Recycled and eco-friendly materials"),
        T("TRD-000005", "Japandi Interiors", "Home", "theme", "UK", "growing", "structural", "2023-11-01", "2027-06-01", "2028-12-01",
          "SEG-001 Premium Loyalists", "japandi", "Japanese-Scandinavian calm interiors: natural materials, low clutter"),
        T("TRD-000006", "Dopamine Decor", "Home", "theme", "UK", "growing", "fad", "2026-01-15", "2026-10-25", "2027-03-01",
          "SEG-005 Trend Followers", "dopamine decor", "Bright, maximal colour-led home accessories driven by social video"),
        T("TRD-000007", "Sleep Sanctuary", "Home", "theme", "UK", "emerging", "structural", "2025-09-01", "2028-03-01", "2029-06-01",
          "SEG-003 Conscious Shoppers", "sleep sanctuary", "Bedroom as a restorative space: bedding, lighting, scent"),
        T("TRD-000008", "Bold Maximalism", "Womenswear", "theme", "UK", "emerging", "structural", "2026-02-01", "2027-09-01", "2028-09-01",
          "SEG-005 Trend Followers", "bold maximalism", "Colour, print and statement texture replacing understated minimalism"),
        T("TRD-000009", "Chocolate Brown", "Womenswear", "colour", "UK", "growing", "cyclical", "2025-09-01", "2027-03-01", "2027-12-01",
          "SEG-001 Premium Loyalists", "chocolate brown", "Deep brown as the lead neutral for coats, knitwear and tailoring"),
        T("TRD-000010", "Butter Yellow", "Womenswear", "colour", "UK", "declining", "fad", "2025-03-01", "2026-06-15", "2027-01-01",
          "SEG-005 Trend Followers", "butter yellow", "Soft pastel yellow, peaked in spring/summer and now fading"),
        T("TRD-000011", "Boucle & Textured Knits", "Womenswear", "material", "UK", "growing", "cyclical", "2025-06-01", "2027-05-01", "2028-03-01",
          "SEG-001 Premium Loyalists", "boucle knitwear", "Boucle, brushed and textured knit surfaces"),
        T("TRD-000012", "Recycled Wool Blends", "Womenswear", "material", "UK", "emerging", "structural", "2026-03-01", "2028-06-01", "2029-12-01",
          "SEG-003 Conscious Shoppers", "recycled wool", "Recycled wool blends for coats and knitwear"),
        T("TRD-000013", "Wide-Leg Tailoring", "Womenswear", "silhouette", "UK", "growing", "cyclical", "2025-04-01", "2027-01-15", "2028-01-01",
          "SEG-001 Premium Loyalists", "wide leg trousers", "Wide-leg trousers and relaxed tailoring"),
        T("TRD-000014", "Gorpcore", "Womenswear", "theme", "UK", "fading", "fad", "2022-04-01", "2023-05-01", "2025-12-01",
          "SEG-005 Trend Followers", "", "Technical outdoor wear as streetwear (historic)"),
        T("TRD-000015", "Cottagecore Textiles", "Home", "theme", "UK", "fading", "fad", "2021-03-01", "2022-01-01", "2024-06-01",
          "SEG-004 Essential Buyers", "", "Floral and rustic home textiles (historic)"),
    ]
    for t in trends:
        t["updated_at"] = as_of

    # ---- Search interest and social mentions ----
    search, social = [], []
    cat_of = {}
    for term, (cat, (tp, w, base, peak), per_pt, (s0, s1)) in TERMS.items():
        cat_of[term] = cat
        for m in MARKETS:
            lead = LEAD[cat][m]
            prev = None
            for k in range(52, -1, -1):
                t = -k
                clean = _bump(t, tp - lead, w, base, peak) * SCALE[m]
                vol = max(3, min(98, round(clean + r.uniform(-2, 2))))
                nxt = _bump(t + 1, tp - lead, w, base, peak) * SCALE[m]
                slope = nxt - clean
                direction = "rising" if slope > 0.5 else "falling" if slope < -0.5 else "stable"
                search.append({"term": term, "category": cat, "market": m, "week_ending": week_end(k), "search_volume": vol,
                               "trend_direction": direction, "updated_at": as_of})
                # social leads search by about four weeks
                s_clean = _bump(t, tp - lead - 4, w, base, peak) * SCALE[m]
                mentions = max(20, round(s_clean * per_pt * MENTION_SCALE[m] * r.uniform(0.95, 1.05)))
                sent = round(s0 + (s1 - s0) * (52 - k) / 52 + r.uniform(-1.5, 1.5))
                social.append({"term": term, "category": cat, "market": m, "week_ending": week_end(k), "mention_count": mentions,
                               "sentiment_pct_positive": sent, "updated_at": as_of})
    for term, (dept, s_now, s_g, m_now, m_g) in CATEGORY_TERMS.items():
        for m in MARKETS:
            for k in range(52, -1, -1):
                t = -k
                sv = s_now * SCALE[m] * (1 + s_g / 100) ** (t / 12)
                mv = m_now * MENTION_SCALE[m] * (1 + m_g / 100) ** (t / 12)
                vol = max(3, min(98, round(sv + r.uniform(-1.5, 1.5))))
                direction = "rising" if s_g > 5 else "falling" if s_g < -5 else "stable"
                search.append({"term": term, "category": dept, "market": m, "week_ending": week_end(k), "search_volume": vol,
                               "trend_direction": direction, "updated_at": as_of})
                social.append({"term": term, "category": dept, "market": m, "week_ending": week_end(k),
                               "mention_count": max(20, round(mv * r.uniform(0.96, 1.04))),
                               "sentiment_pct_positive": round(68 + r.uniform(-3, 3)), "updated_at": as_of})

    # ---- SKU sales trends (K-1700 eight-week slide; PF-220 steady) ----
    sku_sales = []
    k_units = {8: 250, 7: 236, 6: 222, 5: 208, 4: 196, 3: 186, 2: 178, 1: 172, 0: 188}
    k_rating = {8: 4.2, 7: 4.1, 6: 3.9, 5: 3.8, 4: 3.7, 3: 3.6, 2: 3.5, 1: 3.5, 0: 3.5}
    k_return = {8: 3.0, 7: 3.9, 6: 4.8, 5: 5.7, 4: 6.4, 3: 7.0, 2: 7.3, 1: 7.5, 0: 7.4}
    for k in range(26, -1, -1):
        if k > 8:
            units = round(265 + r.uniform(-10, 10)); rating = round(4.3 + r.uniform(-0.05, 0.1), 1)
            ret = round(2.4 + r.uniform(-0.3, 0.4), 1)
        else:
            units, rating, ret = k_units[k], k_rating[k], k_return[k]
        price = 69.99 if k == 0 else 77.99  # promotion price in the latest week
        sku_sales.append({"sku": "K-1700", "week_ending": week_end(k), "units_sold": units, "revenue_gbp": round(units * price, 2),
                          "avg_rating": rating, "return_rate_pct": ret, "updated_at": as_of})
        pu = round(165 + r.uniform(-8, 8))
        sku_sales.append({"sku": "PF-220", "week_ending": week_end(k), "units_sold": pu, "revenue_gbp": round(pu * 77.99, 2),
                          "avg_rating": round(4.2 + r.uniform(-0.1, 0.1), 1), "return_rate_pct": round(2.1 + r.uniform(-0.3, 0.3), 1),
                          "updated_at": as_of})

    # ---- Commodity prices: weekly history (52w) plus a forward curve (25w) ----
    # commodity: (now price, currency, unit, 12-month change %, next-26-week change %)
    comms = {"cotton": (2.10, "USD", "per kg", 18, 5), "polyester": (1.30, "USD", "per kg", 12, 3),
             "nylon": (3.10, "USD", "per kg", 9, 2), "down": (58.0, "USD", "per kg", 21, 6),
             "recycled polyester": (1.55, "USD", "per kg", 8, 2), "zinc": (2900.0, "USD", "per tonne", 9, 1),
             "steel": (540.0, "GBP", "per tonne", -1, 0), "nickel": (16800.0, "USD", "per tonne", 4, 1)}
    commodity_prices = []
    for c, (now, cur, unit, g12, gf) in comms.items():
        for k in range(52, -26, -1):
            if k > 0:
                p = now * (1 + g12 / 100 * (-k / 52)) * (1 + r.uniform(-0.01, 0.01))
                src = "Market data"
            elif k == 0:
                p, src = now, "Market data"
            else:
                p = now * (1 + gf / 100 * (-k / 26))
                src = "Forward curve (forecast)"
            commodity_prices.append({"commodity": c, "date": week_end(k), "price_per_unit": round(p, 3 if now < 10 else 1),
                                     "currency": cur, "unit": unit, "source": src, "updated_at": as_of})

    # ---- Silhouette cycles ----
    S = lambda *a: dict(zip(["silhouette_id", "silhouette_name", "category", "first_peak_year", "first_cycle_duration_months",
                             "second_peak_year", "second_cycle_duration_months", "notes"], a))
    silhouette_cycles = [
        S("SIL-000001", "Oversized", "Outerwear", 1994, 36, 2010, 30,
          "Both cycles: search peaked about 3 months before sales; peak was followed by falling social mentions and a rising markdown rate; "
          "decline lasted roughly 12 months after the peak"),
        S("SIL-000002", "Oversized", "Knitwear", 2016, 22, 2021, 18,
          "Shorter cycles; social mentions turned down first, search followed 6-8 weeks later; sales fell within a season of the search peak"),
        S("SIL-000003", "Oversized", "Tailoring", 2018, 28, 0, 0, "Oversized blazers: slow 18-month rise, 10-month decline"),
        S("SIL-000004", "Fitted", "General", 2015, 24, 0, 0, "Body-conscious silhouettes popular 2015-2019"),
        S("SIL-000005", "Maxi", "Womenswear", 2012, 20, 2024, 18, "Long flowing silhouettes returned with fashion cycles"),
        S("SIL-000006", "Wide-leg", "Trousers", 2005, 30, 2019, 24, "Wide-leg trousers returned every 12-14 years; second cycle ended with the 2020 shift to joggers"),
    ]

    # ---- Trend adoption by market (days a market led the UK; negative = lagged) ----
    leads = {
        "TRD-000001": {"US": 70, "Germany": -30, "Australia": -20}, "TRD-000002": {"US": 73, "Germany": -35, "Australia": -15},
        "TRD-000009": {"US": 63, "Germany": -28, "Australia": -14}, "TRD-000014": {"US": 84, "Germany": -21, "Australia": -28},
        "TRD-000003": {"Germany": 98, "US": -28, "Australia": -35}, "TRD-000005": {"Germany": 112, "US": -14, "Australia": -30},
        "TRD-000006": {"Germany": 84, "US": -21, "Australia": -35}, "TRD-000015": {"Germany": 105, "US": -7, "Australia": -28},
    }
    by_id = {t["trend_id"]: t for t in trends}
    trend_adoption = []
    for tid, lm in leads.items():
        t = by_id[tid]
        uk = d(t["started_date"])
        for m, lead in [("UK", 0)] + list(lm.items()):
            start = uk - timedelta(days=lead)
            el = (as_of - start).days
            if t["lifecycle_stage"] == "fading":
                stage, share = "saturated", round(14 + (lead % 5), 1)
            else:
                stage = "early_adopter" if el < 330 else "mainstream" if el < 900 else "saturated"
                share = round(min(30, 4 + el / 45) * (1.0 if m == "UK" else 0.8), 1)
            trend_adoption.append({"trend_id": tid, "market": m, "adoption_start_date": start, "adoption_stage": stage,
                                   "market_share_pct": share, "updated_at": as_of})

    # ---- Product launches ----
    L = lambda *a: dict(zip(["launch_id", "product_name", "competitor_id", "trend_id", "launch_date", "category", "price_gbp",
                             "success_metric", "traction_note", "failure_reason"], a))
    product_launches = [
        L("LCH-000101", "Weighted Sleep Blanket 6kg", "John Lewis", "TRD-000003", "2026-01-26", "Home", 79, "success",
          "90% of first buy sold in 8 weeks; two reorders", ""),
        L("LCH-000102", "Percussion Massage Gun", "Argos", "TRD-000003", "2026-02-23", "Personal Care", 59, "success",
          "Top-5 wellness seller; 4.3 average rating", ""),
        L("LCH-000103", "Recovery Slides", "JD Sports", "TRD-000003", "2026-03-16", "Footwear", 35, "success",
          "38% repeat purchase rate", ""),
        L("LCH-000104", "Infrared Sauna Blanket", "HomeShop Direct", "TRD-000003", "2026-02-02", "Home", 349, "failure",
          "Sell-through under 20% and heavy markdowns",
          "Priced at 349 pounds, three times comfort-priced alternatives, with no clear use occasion"),
        L("LCH-000105", "Compression Recovery Boots", "Peloton", "TRD-000003", "2026-03-02", "Personal Care", 499, "failure",
          "60% of stock unsold after 12 weeks", "Bulky, 499 pounds and low repeat use"),
        L("LCH-000106", "Cold Plunge Tub", "Lululemon", "TRD-000003", "2026-04-13", "Home", 899, "failure",
          "Under 1 unit per store per week", "Needs plumbing and floor space; not a gifting item"),
        L("LCH-000107", "Sunrise Alarm Sleep Light", "Currys", "TRD-000003", "2026-05-04", "Electricals", 44, "moderate",
          "Steady seller but needed discounting at peak", ""),
        L("LCH-000108", "Aromatherapy Diffuser Range", "John Lewis", "TRD-000003", "2026-04-27", "Home", 29, "moderate",
          "Gifting driven; low repeat", ""),
        L("LCH-000109", "Magnesium Bath Soak Set", "Holland & Barrett", "TRD-000003", "2026-05-18", "Beauty", 14, "success",
          "Giftable; sold out twice", ""),
        L("LCH-000110", "Oversized Wool-Blend Coat", "Zara", "TRD-000002", "2025-11-03", "Womenswear", 129, "success",
          "Best-selling coat of the season", ""),
        L("LCH-000111", "Oversized Puffer Jacket", "Uniqlo", "TRD-000002", "2026-02-02", "Womenswear", 99, "success",
          "Sold through in 7 weeks", ""),
        L("LCH-000112", "Quiet Luxury Capsule", "H&M", "TRD-000001", "2026-03-02", "Womenswear", 89, "failure",
          "Marked down 50% within 8 weeks", "Launched after search had peaked; market saturation, timing too late"),
        L("LCH-000113", "Chocolate Brown Tailoring Capsule", "Zara", "TRD-000009", "2026-08-17", "Womenswear", 119, "success",
          "Early sell-through ahead of plan", ""),
        L("LCH-000114", "Dopamine Decor Cushions and Throws", "H&M", "TRD-000006", "2026-04-06", "Home", 25, "moderate",
          "Fast first sell-through, discounted from week 8", ""),
    ]
    for p in product_launches:
        p["updated_at"] = as_of

    # ---- Competitor risk disclosures ----
    C = lambda *a: dict(zip(["disclosure_id", "competitor_id", "risk_type", "disclosure_date", "horizon_years", "risk_description",
                             "adjustment_action", "impact_level"], a))
    risks = [
        C("CRD-000001", "Inditex", "geopolitical", "2026-08-03", 3, "Red Sea and Middle East shipping disruption raising transit times and freight cost",
          "Nearshoring about 25% of volume to Morocco, Portugal and Turkey by 2028 and holding extra safety stock", "high"),
        C("CRD-000002", "H&M", "climate", "2026-09-14", 5, "Water scarcity and heat in cotton-growing regions driving cotton cost and quality volatility",
          "Shifting to recycled and certified cotton; 100% recycled or sustainably sourced materials by 2030", "medium"),
        C("CRD-000003", "Fast Retailing", "regulatory", "2026-07-20", 2, "EU CSDDD due diligence and forced-labour import rules",
          "Full supplier traceability programme and third-party audits of tier-1 and tier-2 factories", "high"),
        C("CRD-000004", "Kering", "supply_chain", "2026-08-30", 3, "Luxury leather supply tightness",
          "Investing in lab-grown leather R&D and securing long-term hide contracts", "medium"),
        C("CRD-000005", "Primark", "climate", "2026-09-02", 3, "Extreme heat and flooding disrupting Bangladesh and Pakistan factory output",
          "Dual-sourcing every core category and funding factory heat-resilience upgrades", "high"),
        C("CRD-000006", "Next", "geopolitical", "2026-08-20", 3, "Tariff changes on Asian-sourced apparel across the US, UK and EU",
          "Re-pricing and moving 15% of volume from China to Vietnam and Turkey", "medium"),
        C("CRD-000007", "Marks & Spencer", "regulatory", "2026-09-08", 2, "UK and EU extended producer responsibility rules for textiles",
          "Launching a take-back and recycled-fibre programme", "medium"),
        C("CRD-000008", "H&M", "regulatory", "2026-07-28", 4, "EU digital product passport and ecodesign rules for apparel",
          "Building product-level material and origin data into its PLM", "low"),
        C("CRD-000009", "Primark", "supply_chain", "2026-09-21", 1, "Port congestion and volatile container rates",
          "Booking more fixed-rate capacity and shifting some flows to rail", "low"),
    ]
    for c in risks:
        c["updated_at"] = as_of

    # ---- Innovative materials and techniques ----
    M = lambda *a: dict(zip(["material_id", "material_name", "material_category", "readiness_level", "primary_use", "supplier_examples",
                             "cost_vs_standard_pct", "weight_vs_standard_pct", "performance_benefits", "compliance_impact"], a))
    materials = [
        M("MTL-000001", "Recycled Polyester", "Sustainable", "mature", "General apparel", "Repreve; Avantem", -2.5, 0.0,
          "Reduced carbon footprint; same performance as virgin polyester", "Qualifies for sustainable labelling in most regions"),
        M("MTL-000002", "Performance Recycled Nylon", "Performance", "volume_proven", "Active and outerwear", "ECONYL; Repreve", 5.5, -12.0,
          "Lighter weight; enhanced durability; water-resistant", "Well-established in market"),
        M("MTL-000003", "Seamless 3D Knit Construction", "Technique", "volume_proven", "Knitwear and activewear", "Santoni; Stoll", -8.0, -6.0,
          "Cuts labour and fabric waste because there is no cut-and-sew", "No new compliance requirements"),
        M("MTL-000004", "Ultrasonic Welded Seams", "Technique", "volume_proven", "Outerwear and bags", "Sonobond; Branson", -6.0, -4.0,
          "Replaces stitching and seam tape; waterproof seams", "No new compliance requirements"),
        M("MTL-000005", "Glass-Filled Recycled Polypropylene", "Technical", "volume_proven", "Appliance housings such as kettles and fans", "Borealis; SABIC", -7.0, -9.0,
          "Lighter and cheaper housing with the same stiffness", "Needs food-contact and flammability re-testing for appliances"),
        M("MTL-000006", "Lab-Grown Leather", "Technical", "pilot", "Premium footwear and accessories", "VitroLabs; Modern Meadow", 45.0, -5.0,
          "No animal welfare issues; customisable properties", "New regulatory framework emerging in EU"),
        M("MTL-000007", "Bio-Based Nylon (castor)", "Sustainable", "pilot", "Activewear and outerwear", "Arkema; Evonik", 22.0, -8.0,
          "Plant-derived with the performance of nylon 6,6", "Supports bio-based content claims"),
        M("MTL-000008", "Magnesium Alloy Die-Cast Housings", "Technical", "pilot", "Small appliance bodies", "Meridian; Wencan", 12.0, -35.0,
          "Much lighter than aluminium or steel housings", "Needs safety and recyclability review"),
        M("MTL-000009", "Mycelium Leather", "Sustainable", "experimental", "Accessories and experimental pieces", "Bolt Threads", 85.0, -20.0,
          "Fully biodegradable; mushroom-based", "Positive for circular economy claims"),
        M("MTL-000010", "Algae-Based Foam", "Sustainable", "experimental", "Footwear midsoles", "Bloom", 60.0, -25.0,
          "Lightweight foam from algae biomass", "Unproven durability claims"),
        M("MTL-000011", "Aerogel Insulation Fill", "Performance", "experimental", "Padded outerwear", "Aspen Aerogels", 150.0, -30.0,
          "Very thin, light insulation", "Dust and handling safety review needed"),
    ]
    for m in materials:
        m["updated_at"] = as_of

    # ---- Seasonal events ----
    E = lambda *a: dict(zip(["event_id", "event_name", "event_type", "market", "start_date", "end_date", "sales_lift_pct"], a))
    events = [
        E("EVT-000001", "Black Friday & Cyber Monday", "Shopping", "UK", "2026-11-23", "2026-11-30", 280.0),
        E("EVT-000002", "Boxing Day Sale", "Shopping", "UK", "2026-12-26", "2027-01-07", 320.0),
        E("EVT-000003", "Black Friday & Cyber Monday", "Shopping", "US", "2026-11-27", "2026-12-02", 350.0),
        E("EVT-000004", "Christmas Season", "Holiday", "UK", "2026-11-01", "2026-12-23", 450.0),
        E("EVT-000005", "Spring Sale", "Shopping", "Germany", "2027-03-01", "2027-03-15", 150.0),
        E("EVT-000006", "Singles' Day", "Shopping", "UK", "2026-11-11", "2026-11-11", 60.0),
        E("EVT-000007", "Christmas Delivery Cut-off", "Holiday", "UK", "2026-12-16", "2026-12-18", 90.0),
        E("EVT-000008", "Black Week", "Shopping", "Germany", "2026-11-23", "2026-11-30", 220.0),
        E("EVT-000009", "Summer Sale", "Shopping", "UK", "2026-07-01", "2026-07-31", 180.0),
        E("EVT-000010", "Black Friday & Cyber Monday (last year)", "Shopping", "UK", "2025-11-24", "2025-12-01", 265.0),
    ]
    for e in events:
        e["updated_at"] = as_of

    # ---- Trend forecasts ----
    F = lambda *a: dict(zip(["forecast_id", "trend_id", "season", "market", "forecast_text", "confidence_level"], a))
    forecasts = [
        F("FCT-000001", "TRD-000002", "AW27", "UK",
          "Oversized stays the main coat shape for AW27 but moves to structured, shoulder-led cuts. UK peak is around the next 4-5 weeks and decline starts in early 2027, so taper AW27 volumes and keep it to a minority of the coat range.", "high"),
        F("FCT-000002", "TRD-000002", "AW27", "US",
          "US led the UK by about ten weeks and is already easing; by AW27 oversized is replenishment only in the US.", "high"),
        F("FCT-000003", "TRD-000001", "AW27", "UK",
          "Quiet luxury is in decline, with search down about 50% from peak. Premium basics survive as a quality position but the understated styling cue fades over the next 9-12 months to mid 2027.", "medium"),
        F("FCT-000004", "TRD-000008", "AW27", "UK",
          "Bold maximalism (colour, print, statement texture) replaces quiet luxury over the next 12-18 months, peaking around mid 2027 and lasting into 2028.", "medium"),
        F("FCT-000005", "TRD-000009", "AW27", "UK",
          "Chocolate brown is the lead AW27 colour: early in its cycle, peaking early 2027. Safe for coats, knitwear and tailoring and strongly relevant to Premium Loyalists.", "high"),
        F("FCT-000006", "TRD-000010", "AW27", "UK",
          "Butter yellow is past peak and fading fast; use only as an accent colour.", "low"),
        F("FCT-000007", "TRD-000011", "AW27", "UK",
          "Boucle and textured knits keep growing through AW27 and suit the Premium Loyalists customer.", "medium"),
        F("FCT-000008", "TRD-000012", "AW27", "UK",
          "Recycled wool blends are early in the cycle and a differentiator for Conscious Shoppers; low volume now, growing into 2028.", "medium"),
        F("FCT-000009", "TRD-000013", "AW27", "UK",
          "Wide-leg tailoring keeps growing and peaks around January 2027; core silhouette for AW27 trousers.", "high"),
        F("FCT-000010", "TRD-000002", "SS27", "UK",
          "Oversized peaks in autumn 2026 and begins to decline in early 2027; fitted alternatives emerge for SS27.", "medium"),
        F("FCT-000011", "TRD-000003", "AW27", "UK",
          "Wellness and recovery stays strong through the holiday season and into 2027, with a long runway to 2029.", "high"),
        F("FCT-000012", "TRD-000005", "AW27", "UK",
          "Japandi keeps a steady structural climb and peaks around mid 2027.", "high"),
        F("FCT-000013", "TRD-000006", "AW27", "UK",
          "Dopamine decor is a fad: peaks within weeks and falls away sharply by spring 2027. Test only, do not commit volume.", "low"),
        F("FCT-000014", "TRD-000007", "AW27", "UK",
          "Sleep sanctuary is early in its cycle with a long runway to 2029.", "medium"),
        F("FCT-000015", "TRD-000006", "AW27", "Germany",
          "Dopamine decor is already past peak in Germany, which led the UK by about 12 weeks.", "medium"),
    ]
    for f in forecasts:
        f["updated_at"] = as_of

    return {
        "trends": trends, "market_search_interest": search, "social_mentions": social, "sku_sales_trends": sku_sales,
        "commodity_prices": commodity_prices, "silhouette_cycles": silhouette_cycles, "trend_adoption": trend_adoption,
        "product_launches": product_launches, "competitor_risk_disclosures": risks, "innovative_materials": materials,
        "seasonal_events": events, "trend_forecasts": forecasts,
    }
