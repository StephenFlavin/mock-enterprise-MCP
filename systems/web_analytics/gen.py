"""Web analytics data: search trends, traffic, conversions, marketing, and forecasts."""
from datetime import datetime, timedelta


def generate(g):
    """Generate web analytics data."""
    r = g.rng

    search_trends = []
    traffic_by_channel = []
    conversion_metrics = []
    marketing_activities = []
    campaign_creatives = []
    resale_funnel = []
    traffic_forecast = []

    # Generate search trends (last 90 days)
    keywords = [
        ("backpack", "Bags"), ("recycled polyester", "Bags"),
        ("athleisure", "Womenswear"), ("yoga pants", "Womenswear"),
        ("home decor", "Home"), ("bedding", "Home"),
        ("sustainable fashion", "Womenswear"), ("eco-friendly", "All"),
    ]
    trend_id = 1
    for keyword, category in keywords:
        for days_ago in range(0, 91, 7):  # Weekly data
            trend_date = g.days_ago(days_ago)
            # Create realistic trend: baseline with some noise and occasional spikes
            base_volume = r.randint(5000, 25000)
            if days_ago < 28:  # Recent weeks - upward trend
                volume = int(base_volume * (1.0 + (28 - days_ago) * 0.02))
            else:
                volume = base_volume
            volume = int(volume * r.uniform(0.8, 1.2))  # Add noise

            trend_dir = "up" if volume > base_volume * 1.05 else ("down" if volume < base_volume * 0.95 else "stable")

            search_trends.append({
                "trend_id": f"ST-{trend_id:06d}",
                "search_term": keyword,
                "date": trend_date,
                "volume": max(1000, volume),
                "trend_direction": trend_dir,
                "category": category,
            })
            trend_id += 1

    # Generate daily traffic by channel (last 21 days)
    channels = ["organic", "paid", "direct", "social", "email", "referral"]
    devices = ["mobile", "desktop", "tablet"]
    for days_ago in range(21):
        date = g.days_ago(days_ago)
        for channel in channels:
            for device in devices:
                # Realistic traffic patterns: organic high, paid medium, social low, etc.
                base_sessions = {"organic": 8000, "paid": 4000, "direct": 2000,
                                 "social": 1500, "email": 1000, "referral": 800}[channel]
                # Mobile gets more traffic
                sessions = int(base_sessions * {"mobile": 0.6, "desktop": 0.35, "tablet": 0.05}[device])
                sessions = int(sessions * r.uniform(0.7, 1.3))  # Daily variance

                # Conversion varies by channel
                conv_rates = {"organic": 0.025, "paid": 0.015, "direct": 0.020,
                              "social": 0.008, "email": 0.030, "referral": 0.012}
                conversions = int(sessions * conv_rates[channel])
                # Some noise
                conversions = int(conversions * r.uniform(0.8, 1.2))

                revenue = conversions * r.uniform(50, 150)  # Average order value

                traffic_by_channel.append({
                    "date": date,
                    "channel": channel,
                    "device": device,
                    "sessions": sessions,
                    "conversions": conversions,
                    "revenue_gbp": round(revenue, 2),
                })

    # Generate conversion metrics by device and delivery option (last 21 days)
    delivery_options = ["standard", "next_day"]
    for days_ago in range(21):
        date = g.days_ago(days_ago)
        for device in devices:
            for channel in channels:
                for delivery in delivery_options:
                    # Conversion rates vary by device (mobile typically lower)
                    base_rate = {"mobile": 1.8, "desktop": 3.2, "tablet": 2.5}[device]
                    # Next-day delivery slightly increases conversion
                    base_rate += 0.3 if delivery == "next_day" else 0

                    conversion_rate = base_rate * r.uniform(0.9, 1.1)

                    # Orders from this combination
                    orders = r.randint(20, 200)
                    conversions = int(orders * conversion_rate / 100)

                    # Calculate revenue based on orders and average order value
                    aov = r.uniform(50, 150)
                    revenue = orders * aov

                    conversion_metrics.append({
                        "date": date,
                        "channel": channel,
                        "device": device,
                        "delivery_option": delivery,
                        "conversion_rate": round(conversion_rate, 2),
                        "conversions": conversions,
                        "orders": orders,
                        "revenue_gbp": round(revenue, 2),
                    })

    # Generate marketing activities for various ranges
    styles = ["STY-5520", "STY-7731", "STY-T-4410", "SKU-PF-220", "K-1700"]
    activity_id = 1
    for style in styles:
        for _ in range(r.randint(2, 4)):
            start = g.date_between(60, 7)
            end = start + timedelta(days=r.randint(7, 30))

            campaign = f"Campaign {activity_id}"
            channel = r.choice(channels)
            impressions = r.randint(50000, 500000)
            ctr = {"organic": 0.02, "paid": 0.015, "direct": 0.05,
                   "social": 0.03, "email": 0.08, "referral": 0.02}[channel]
            clicks = int(impressions * ctr)
            conversions = int(clicks * r.uniform(0.01, 0.05))
            revenue = conversions * r.uniform(50, 150)

            marketing_activities.append({
                "activity_id": f"MA-{activity_id:06d}",
                "range_id": style,
                "campaign_name": campaign,
                "channel": channel,
                "start_date": start,
                "end_date": end,
                "impressions": impressions,
                "clicks": clicks,
                "conversions": conversions,
                "revenue_gbp": round(revenue, 2),
            })
            activity_id += 1

    # Generate campaign creatives for recent campaigns
    creative_id = 1
    creative_types = ["image", "video", "text", "carousel"]
    variants = ["variant_a", "variant_b", "variant_c"]
    campaigns = ["Home Event 20pct off", "Campaign 1", "Campaign 2", "Campaign 3"]
    for campaign in campaigns:
        for creative_type in creative_types:
            for variant in r.sample(variants, min(2, len(variants))):
                impressions = r.randint(10000, 100000)
                ctr = r.uniform(0.01, 0.05)
                clicks = int(impressions * ctr)
                conversions = int(clicks * r.uniform(0.01, 0.08))
                revenue = conversions * r.uniform(50, 150)
                engagement = r.uniform(2.0, 8.0)  # Percent

                campaign_creatives.append({
                    "creative_id": f"CC-{creative_id:06d}",
                    "campaign_name": campaign,
                    "creative_type": creative_type,
                    "test_variant": variant,
                    "impressions": impressions,
                    "clicks": clicks,
                    "conversions": conversions,
                    "revenue_gbp": round(revenue, 2),
                    "engagement_rate_pct": round(engagement, 2),
                })
                creative_id += 1

    # Generate resale funnel (last 90 days, weekly)
    funnel_stages = ["views", "item_added", "checkout", "purchase"]
    for days_ago in range(0, 91, 7):
        date = g.days_ago(days_ago)
        # Funnel conversion: views -> item_added -> checkout -> purchase
        base_views = r.randint(5000, 15000)
        for i, stage in enumerate(funnel_stages):
            # Drop-off at each stage
            users = int(base_views * (1.0 - i * 0.35))
            transactions = int(users * 0.3)
            items_listed = int(users * r.uniform(1, 3))
            items_sold = int(users * 0.15)
            gmv = items_sold * r.uniform(20, 80)

            resale_funnel.append({
                "date": date,
                "funnel_stage": stage,
                "user_count": users,
                "transaction_count": transactions,
                "items_listed": items_listed,
                "items_sold": items_sold,
                "gmv_gbp": round(gmv, 2),
            })

    # Generate traffic forecast for peak season (Black Friday to Christmas Eve)
    bf_date = g.as_of.replace(month=11, day=25)  # Approximate Black Friday
    xmas_date = g.as_of.replace(month=12, day=24)
    current_date = bf_date
    while current_date <= xmas_date:
        # Get day of week for realistic patterns
        dow = current_date.weekday()
        # Weekends get more traffic
        day_factor = 1.5 if dow >= 4 else 1.0  # Friday-Sunday get 50% boost
        # Closer to Christmas gets more traffic
        days_until_xmas = (xmas_date - current_date).days
        xmas_factor = 1.0 + (25 - days_until_xmas) * 0.02 if days_until_xmas <= 25 else 1.0

        for channel in channels:
            base_volume = {"organic": 12000, "paid": 8000, "direct": 4000,
                          "social": 3000, "email": 2000, "referral": 1500}[channel]
            volume = int(base_volume * day_factor * xmas_factor * r.uniform(0.9, 1.1))
            revenue = volume * r.uniform(0.04, 0.08) * r.uniform(50, 150)  # Conv rate * AOV

            traffic_forecast.append({
                "date": current_date,
                "channel": channel,
                "forecast_volume": volume,
                "forecast_revenue_gbp": round(revenue, 2),
                "confidence_pct": round(r.uniform(70, 95), 1),
            })

        current_date += timedelta(days=1)

    return {
        "search_trends": search_trends,
        "traffic_by_channel": traffic_by_channel,
        "conversion_metrics": conversion_metrics,
        "marketing_activities": marketing_activities,
        "campaign_creatives": campaign_creatives,
        "resale_funnel": resale_funnel,
        "traffic_forecast": traffic_forecast,
    }
