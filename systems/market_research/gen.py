"""Market research data: consumer surveys, market sizing, competitor intelligence, local events."""
from datetime import timedelta


def generate(g):
    r = g.rng

    # Survey responses
    # background noise only on topics no persona question targets; story topics are fully seeded
    topics = ["home products", "small kitchen appliances"]
    themes = ["price", "quality", "design", "convenience", "brand"]
    age_groups = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
    regions = ["UK", "Germany", "France", "Spain", "Poland", "Czechia", "Japan", "USA"]
    genders = ["female", "male", "other"]

    survey_responses = []
    for i in range(60):
        response_text = g.fake.sentence(nb_words=10)
        response = {
            "response_id": f"SR-{i + 1:06d}",
            "topic": r.choice(topics),
            "respondent_age_group": r.choice(age_groups),
            "respondent_region": r.choice(regions),
            "respondent_gender": r.choice(genders),
            "response_rating": r.randint(1, 5),
            "theme": r.choice(themes),
            "response_text": response_text,
            "response_date": g.date_between(180, 0)
        }
        survey_responses.append(response)

    # Anthropometric measurements: fully seeded (seed/anthropometric_measurements.csv)
    anthropometric = []

    # Product size charts
    categories = ["womenswear", "menswear"]
    sizes = ["XS", "S", "M", "L", "XL", "XXL"]

    size_charts = []
    # womenswear: our own UK size chart as held in plm for STY-5520 (UK 8-18: bust, waist, hip, length), so both systems agree
    PLM_WOMEN = [("8", 82, 64, 90, 60), ("10", 86, 68, 94, 62), ("12", 90, 72, 98, 64), ("14", 94, 76, 102, 66),
                 ("16", 100, 82, 108, 68), ("18", 106, 88, 114, 70)]
    for i, category in enumerate(categories):
        if category == "womenswear":
            for j, (size, chest, waist, hip, length) in enumerate(PLM_WOMEN):
                size_charts.append({"size_chart_id": f"SC-{i * 6 + j + 1:06d}", "category": category, "size_label": f"UK {size}",
                                    "chest_cm": chest, "waist_cm": waist, "hip_cm": hip, "length_cm": length})
            continue
        for j, size in enumerate(sizes):
            # Size progresses with chest/waist/hip
            base_chest = 76 + (j * 4) + (16 if category == "menswear" else 0)   # menswear charts run larger than womenswear
            base_waist = 61 + (j * 4) + (17 if category == "menswear" else 0)
            base_hip = 86 + (j * 4) + (6 if category == "menswear" else 0)
            base_length = 60 + (j * 2) + (10 if category == "menswear" else 0)

            chart = {
                "size_chart_id": f"SC-{i * 6 + j + 1:06d}",
                "category": category,
                "size_label": size,
                "chest_cm": base_chest,
                "waist_cm": base_waist,
                "hip_cm": base_hip,
                "length_cm": base_length
            }
            size_charts.append(chart)

    # Market data and launches are fully seeded
    market_data = []
    market_launches = []

    # Local competitors
    stores = ["ST100", "ST150"]  # ST214, ST001, ST050 are seeded
    competitor_names = ["CompetitorA", "CompetitorB", "Local Discount Store", "Premium Retailer", "Online Only"]
    categories_comp = ["premium", "discount", "online", "grocery focus", "fashion focus"]
    activities = ["price reduction", "new opening", "expansion", "temporary closure", "rebranding"]

    local_competitors = []
    for i, store in enumerate(stores):
        for j in range(4):  # 4 competitors per store
            comp = {
                "competitor_id": f"LC-{i * 4 + j + 1:06d}",
                "country": "UK",
                "site_id": store,
                "competitor_name": f"{r.choice(competitor_names)} {j}",
                "estimated_stores": 1,
                "category_focus": r.choice(categories_comp),
                "distance_m": r.randint(50, 2000),
                "last_observed_activity": r.choice(activities),
                "last_observed_date": g.date_between(60, 0)
            }
            local_competitors.append(comp)

    # Local events
    event_types = ["festival", "market", "sports event", "concert", "community event"]
    impacts = ["high footfall increase", "moderate increase", "potential parking issues", "disruption to access"]

    local_events = []
    for i, store in enumerate(stores):
        for j in range(3):  # 3 events per store
            event = {
                "event_id": f"EV-{i * 3 + j + 1:06d}",
                "site_id": store,
                "event_name": f"Local {r.choice(event_types)}",
                "expected_attendance": r.randint(500, 8000),
                "event_type": r.choice(event_types),
                "event_date": g.date_between(60, 0),
                "expected_visitor_impact": r.choice(impacts)
            }
            local_events.append(event)

    # Road works
    location_desc = ["main access road", "nearby junction", "adjacent street", "parking area access"]
    impacts_road = ["access disruption", "parking reduction", "minor delays", "significant congestion"]

    road_works = []
    for i, store in enumerate(stores):
        for j in range(2):  # 2 road works per store
            start = g.date_between(30, 5)
            end = start + timedelta(days=r.randint(7, 60))

            work = {
                "roadwork_id": f"RW-{i * 2 + j + 1:06d}",
                "site_id": store,
                "start_date": start,
                "end_date": end,
                "location_description": r.choice(location_desc),
                "expected_impact": r.choice(impacts_road)
            }
            road_works.append(work)

    return {
        "survey_responses": survey_responses,
        "anthropometric_measurements": anthropometric,
        "product_size_charts": size_charts,
        "market_data": market_data,
        "local_competitors": local_competitors,
        "local_events": local_events,
        "road_works": road_works,
        "market_launches": market_launches
    }
