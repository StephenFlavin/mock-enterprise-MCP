"""Market research data: consumer surveys, market sizing, competitor intelligence, local events."""
from datetime import timedelta


def generate(g):
    r = g.rng

    # Survey responses
    topics = ["resale programme", "outdoor clothing preferences", "consumer priorities", "home products", "small kitchen appliances"]
    age_groups = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
    regions = ["UK", "Germany", "France", "Spain", "Poland", "Czechia", "Japan", "USA"]
    genders = ["female", "male", "other"]

    survey_responses = []
    for i in range(80):
        response_text = g.fake.sentence(nb_words=10)
        response = {
            "response_id": f"SR-{i + 1:06d}",
            "topic": r.choice(topics),
            "respondent_age_group": r.choice(age_groups),
            "respondent_region": r.choice(regions),
            "respondent_gender": r.choice(genders),
            "response_rating": r.randint(1, 5),
            "response_text": response_text,
            "response_date": g.date_between(-180, 0)
        }
        survey_responses.append(response)

    # Anthropometric measurements
    countries = ["GB", "DE", "FR"]
    genders = ["female", "male"]
    age_groups = ["20-30", "30-40", "40-50"]

    anthropometric = []
    for i in range(18):  # 3 countries x 2 genders x 3 age groups
        base_chest = r.randint(80, 100)
        base_waist = r.randint(65, 85)
        base_hip = r.randint(85, 110)
        base_height = r.randint(155, 185)

        measurement = {
            "measurement_id": f"AM-{i + 1:06d}",
            "country": r.choice(countries),
            "gender": r.choice(genders),
            "age_group": r.choice(age_groups),
            "sample_size": r.randint(100, 500),
            "chest_cm": base_chest + r.randint(-5, 5),
            "waist_cm": base_waist + r.randint(-5, 5),
            "hip_cm": base_hip + r.randint(-5, 5),
            "height_cm": base_height + r.randint(-5, 5),
            "survey_date": g.date_between(-365, 0)
        }
        anthropometric.append(measurement)

    # Product size charts
    categories = ["womenswear", "menswear"]
    sizes = ["XS", "S", "M", "L", "XL", "XXL"]

    size_charts = []
    for i, category in enumerate(categories):
        for j, size in enumerate(sizes):
            # Size progresses with chest/waist/hip
            base_chest = 76 + (j * 4)
            base_waist = 61 + (j * 4)
            base_hip = 86 + (j * 4)
            base_length = 60 + (j * 2)

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

    # Market data
    countries = ["Poland", "Czechia", "Spain", "Japan", "USA", "Germany", "France"]
    categories_list = ["home", "outdoor clothing", "small kitchen appliances", "bedding", "footwear"]
    pack_formats = [
        "single unit; carton; multipack",
        "bulk; individual",
        "gift set; standard pack",
        "economy pack; premium pack",
        "value pack; single"
    ]

    market_data = []
    for i, country in enumerate(countries):
        for j, category in enumerate(categories_list):
            market_size = r.randint(50_000_000, 500_000_000)
            growth = r.randint(-5, 15)
            margin = r.randint(25, 50)

            market = {
                "market_id": f"MKT-{i * 5 + j + 1:06d}",
                "country": country,
                "category": category,
                "market_size_gbp": market_size,
                "growth_pct_yoy": growth,
                "typical_pack_formats": r.choice(pack_formats),
                "typical_retail_margin_pct": margin,
                "consumer_preference_notes": g.fake.sentence(nb_words=8),
                "currency": "GBP" if country == "UK" else "EUR" if country in ["Poland", "Czechia", "Germany", "France", "Spain"] else "JPY",
                "data_date": g.date_between(-90, 0)
            }
            market_data.append(market)

    # Local competitors
    stores = ["ST214", "ST001", "ST050", "ST100", "ST150"]
    competitor_names = ["CompetitorA", "CompetitorB", "Local Discount Store", "Premium Retailer", "Online Only"]
    categories_comp = ["premium", "discount", "online", "grocery focus", "fashion focus"]
    activities = ["price reduction", "new opening", "expansion", "temporary closure", "rebranding"]

    local_competitors = []
    for i, store in enumerate(stores):
        for j in range(4):  # 4 competitors per store
            comp = {
                "competitor_id": f"LC-{i * 4 + j + 1:06d}",
                "site_id": store,
                "competitor_name": f"{r.choice(competitor_names)} {j}",
                "category_focus": r.choice(categories_comp),
                "distance_m": r.randint(50, 2000),
                "last_observed_activity": r.choice(activities),
                "last_observed_date": g.date_between(-60, 0)
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
                "event_type": r.choice(event_types),
                "event_date": g.date_between(0, 60),  # Future events
                "expected_visitor_impact": r.choice(impacts)
            }
            local_events.append(event)

    # Road works
    location_desc = ["main access road", "nearby junction", "adjacent street", "parking area access"]
    impacts_road = ["access disruption", "parking reduction", "minor delays", "significant congestion"]

    road_works = []
    for i, store in enumerate(stores):
        for j in range(2):  # 2 road works per store
            start = g.date_between(-30, 30)
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

    # Market launches
    launch_countries = ["Spain", "Poland", "Czechia", "Japan"]
    launch_categories = ["home", "outdoor clothing", "small kitchen appliances"]

    market_launches = []
    for i, country in enumerate(launch_countries):
        for j, category in enumerate(launch_categories):
            launch_date = g.date_between(-365, -180)
            units = r.randint(5_000, 100_000)
            revenue = units * r.randint(10, 50)
            weeks_to_breakeven = r.randint(4, 26)

            launch = {
                "launch_id": f"LNC-{i * 3 + j + 1:06d}",
                "country": country,
                "category": category,
                "launch_date": launch_date,
                "total_units_sold": units,
                "total_revenue_gbp": revenue,
                "breakeven_weeks": weeks_to_breakeven
            }
            market_launches.append(launch)

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
