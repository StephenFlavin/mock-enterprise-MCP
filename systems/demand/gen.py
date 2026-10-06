"""Demand planning system: forecasts, demand history, accuracy metrics, overrides."""
from datetime import datetime, timedelta


def generate(g):
    r = g.rng

    # Get all active products and SKUs from master
    products = g.master("products")
    skus = [p["sku"] for p in products if p["status"] in ("active", "new")][:300]
    categories = list(set(p["category"] for p in products if p["sku"] in skus))

    demand_history = []
    forecasts = []
    forecast_configs = []
    forecast_accuracy = []
    forecast_errors = []
    forecast_bias = []
    early_sales_data = []
    early_sales_alerts = []
    pipeline_products = []
    promotion_effects = []
    daily_orders = []
    forecast_overrides = []
    demand_history_adjustments = []

    # Forecast configurations
    configs = [
        ("CFG-000001", "52-week baseline", 52, "exponential_smoothing", "fast_mover", "active"),
        ("CFG-000002", "26-week fashion", 26, "exponential_smoothing", "fast_mover", "test"),
        ("CFG-000003", "104-week slow movers", 104, "moving_average", "slow_mover", "active"),
        ("CFG-000004", "New product benchmark", 0, "comparable_products", "new_product", "active"),
    ]

    for cfg_id, name, window, method, item_type, status in configs:
        forecast_configs.append({
            "config_id": cfg_id,
            "config_name": name,
            "history_window_weeks": window,
            "method_type": method,
            "item_type": item_type,
            "status": status,
            "created_at": g.as_of - timedelta(days=r.randint(30, 180)),
            "notes": f"Configuration for {item_type} using {method}"
        })

    # Demand history - weekly data for the past year
    for sku in skus[:150]:
        prod = next((p for p in products if p["sku"] == sku), None)
        if not prod:
            continue
        category = prod["category"]

        for week_offset in range(-52, 0):
            week_date = g.as_of + timedelta(weeks=week_offset)
            week_date = week_date - timedelta(days=week_date.weekday())  # Monday

            base_demand = r.randint(20, 500)
            # Add some seasonality
            week_num = week_date.isocalendar()[1]
            seasonal_factor = 1.2 if week_num >= 45 or week_num <= 2 else 1.0  # Peak season

            units = int(base_demand * seasonal_factor * r.gauss(1.0, 0.2))
            units = max(0, units)

            demand_history.append({
                "history_id": f"DH-{len(demand_history) + 1:06d}",
                "sku": sku,
                "category": category,
                "period_date": week_date,
                "units_sold": units,
                "revenue_gbp": round(units * r.uniform(15, 80), 2),
                "demand_type": "actual",
                "correction_reason": None,
                "updated_at": g.as_of
            })

    # Forecasts for next 12 weeks
    for sku in skus[:150]:
        prod = next((p for p in products if p["sku"] == sku), None)
        if not prod:
            continue
        category = prod["category"]

        for week_offset in range(1, 13):
            week_date = g.as_of + timedelta(weeks=week_offset)
            week_date = week_date - timedelta(days=week_date.weekday())  # Monday

            base_forecast = r.randint(30, 400)

            for forecast_type, multiplier in [("base", 1.0), ("upside", 1.2), ("downside", 0.8)]:
                units = int(base_forecast * multiplier * r.gauss(1.0, 0.15))
                units = max(0, units)

                forecasts.append({
                    "forecast_id": f"FC-{len(forecasts) + 1:06d}",
                    "config_id": "CFG-000001" if base_forecast > 100 else "CFG-000003",
                    "sku": sku,
                    "category": category,
                    "forecast_week": week_date,
                    "units_forecast": units,
                    "forecast_type": forecast_type,
                    "created_at": g.as_of
                })

    # Forecast accuracy - historical performance
    for cfg_id in ["CFG-000001", "CFG-000002", "CFG-000003"]:
        for cat in categories[:30]:
            for week_offset in range(-12, 0):
                period_end = g.as_of + timedelta(weeks=week_offset)

                forecast_accuracy.append({
                    "accuracy_id": f"ACC-{len(forecast_accuracy) + 1:06d}",
                    "config_id": cfg_id,
                    "period_start": period_end - timedelta(days=6),
                    "period_end": period_end,
                    "sku": None,
                    "category": cat,
                    "forecast_level": "category",
                    "mape_pct": round(r.gauss(12, 8), 1),
                    "bias_pct": round(r.gauss(2, 5), 1),
                    "rmse": r.randint(50, 200)
                })

    # Forecast errors - decomposition
    for cat in categories[:40]:
        for week_offset in range(-12, 0):
            period_end = g.as_of + timedelta(weeks=week_offset)

            error_drivers = ["weather", "promotion", "pricing", "new_launch", "store_cluster"]
            for driver in r.sample(error_drivers, k=r.randint(1, 3)):
                forecast_errors.append({
                    "error_id": f"ERR-{len(forecast_errors) + 1:06d}",
                    "sku": None,
                    "category": cat,
                    "period_start": period_end - timedelta(days=6),
                    "period_end": period_end,
                    "error_driver": driver,
                    "error_units": r.randint(-200, 200),
                    "error_pct": round(r.gauss(0, 5), 1),
                    "explanation": f"{driver} impact on {cat}"
                })

    # Forecast bias by market
    markets = ["UK North", "UK South", "London", "Midlands", "Ireland"]
    for cat in categories[:30]:
        for market in r.sample(markets, k=r.randint(2, 4)):
            for week_offset in range(-12, 0):
                period_end = g.as_of + timedelta(weeks=week_offset)

                forecast_bias.append({
                    "bias_id": f"BI-{len(forecast_bias) + 1:06d}",
                    "sku": None,
                    "category": cat,
                    "market": market,
                    "period_start": period_end - timedelta(days=6),
                    "period_end": period_end,
                    "bias_pct": round(r.gauss(5, 12), 1),
                    "primary_driver": r.choice(["promotion", "weather", "pricing"])
                })

    # Early sales data - new products tracking
    new_products = [p for p in products if p["status"] == "new"][:30]
    for prod in new_products:
        launch_str = prod.get("launch_date")
        if isinstance(launch_str, str):
            launch_date = datetime.fromisoformat(launch_str).date()
        else:
            launch_date = g.as_of - timedelta(days=r.randint(0, 60))

        for week_offset in range(1, 6):
            week_date = launch_date + timedelta(weeks=week_offset - 1)
            if week_date > g.as_of:
                break

            forecast_units = r.randint(100, 800)
            actual_units = int(forecast_units * r.gauss(0.9, 0.3))
            actual_units = max(0, actual_units)

            early_sales_data.append({
                "sales_id": f"ES-{len(early_sales_data) + 1:06d}",
                "sku": prod["sku"],
                "product_name": prod["name"],
                "launch_date": launch_date,
                "week_in_launch": week_offset,
                "units_sold": actual_units,
                "units_forecast": forecast_units,
                "velocity_index": round(actual_units / forecast_units, 2) if forecast_units > 0 else 0
            })

    # Early sales alerts
    for i, prod in enumerate(new_products[:10]):
        early_sales_alerts.append({
            "alert_id": f"ALR-{len(early_sales_alerts) + 1:06d}",
            "sku": prod["sku"],
            "product_name": prod["name"],
            "alert_type": r.choice(["chase", "cancel"]),
            "trigger_threshold_pct": r.choice([40, 50, 60, 70]),
            "status": r.choice(["active", "inactive"]),
            "created_at": g.as_of - timedelta(days=r.randint(7, 30))
        })

    # Pipeline products
    for i, prod in enumerate(products[300:330]):
        season = prod.get("season", f"AW{g.as_of.year}")
        pipeline_products.append({
            "pipeline_id": f"PL-{len(pipeline_products) + 1:06d}",
            "sku": prod["sku"],
            "product_name": prod["name"],
            "launch_date": g.as_of + timedelta(days=r.randint(0, 120)),
            "season": season,
            "category": prod["category"],
            "supply_risk": r.choice(["low", "medium", "high"]),
            "demand_risk": r.choice(["low", "medium", "high"]),
            "risk_score": round(r.gauss(45, 20), 0),
            "status": r.choice(["draft", "approved", "in_production"])
        })

    # Promotion effects - historical
    for cat in categories[:50]:
        for promo_offset in range(-52, 0, 4):  # Promotions every 4 weeks
            promo_start = g.as_of + timedelta(weeks=promo_offset)
            promo_end = promo_start + timedelta(days=6)

            mechanic = r.choice(["percentage_off", "bundle", "buy_one_get_one"])
            uplift = r.randint(20, 80)
            cannib = uplift * r.uniform(0.3, 0.6)
            pull_forward = uplift * r.uniform(0.2, 0.4)

            promotion_effects.append({
                "promo_id": f"PRM-{len(promotion_effects) + 1:06d}",
                "sku": None,
                "category": cat,
                "promo_mechanic": mechanic,
                "period_start": promo_start,
                "period_end": promo_end,
                "uplift_pct": round(uplift, 1),
                "cannibalisation_pct": round(cannib, 1),
                "pull_forward_pct": round(pull_forward, 1)
            })

    # Daily orders - for the past 30 days and next 60 days
    channels = ["web", "app", "click_collect", "marketplace"]
    regions = ["UK North", "UK South", "London", "Midlands", "Ireland"]

    for day_offset in range(-30, 60):
        order_date = g.as_of + timedelta(days=day_offset)

        for channel in r.sample(channels, k=r.randint(2, 4)):
            for region in r.sample(regions, k=r.randint(2, 3)):
                base_units = r.randint(500, 3000)
                # Add weekend uplift
                is_weekend = order_date.weekday() >= 5
                units = int(base_units * (1.5 if is_weekend else 1.0) * r.gauss(1.0, 0.3))
                units = max(100, units)

                daily_orders.append({
                    "order_date": order_date,
                    "channel": channel,
                    "region": region,
                    "units": units,
                    "value_gbp": round(units * r.uniform(25, 60), 2)
                })

    # Forecast overrides
    for cat in categories[:20]:
        week_start = g.as_of + timedelta(weeks=1)
        week_start = week_start - timedelta(days=week_start.weekday())  # Monday

        forecast_overrides.append({
            "override_id": f"OVR-{len(forecast_overrides) + 1:06d}",
            "sku": None,
            "category": cat,
            "week_start": week_start,
            "week_end": week_start + timedelta(days=6),
            "override_pct": r.choice([10, 15, 20, 25, -10, -15]),
            "override_type": r.choice(["uplift", "downside"]),
            "reason": r.choice(["Promotion planned", "Seasonal adjustment", "Market event"]),
            "created_at": g.as_of
        })

    # Demand history adjustments - for stockout corrections
    for sku in skus[:50]:
        if r.random() < 0.3:  # 30% have adjustments
            period_start = g.as_of - timedelta(weeks=r.randint(4, 26))
            period_end = period_start + timedelta(weeks=r.randint(1, 4))

            demand_history_adjustments.append({
                "adjustment_id": f"ADJ-{len(demand_history_adjustments) + 1:06d}",
                "sku": sku,
                "period_start": period_start,
                "period_end": period_end,
                "stockout_cause": r.choice(["supply delay", "DC allocation", "forecast miss"]),
                "units_lost": r.randint(50, 500),
                "correction_method": "use average of pre/post"
            })

    return {
        "demand_history": demand_history,
        "forecasts": forecasts,
        "forecast_configs": forecast_configs,
        "forecast_accuracy": forecast_accuracy,
        "forecast_errors": forecast_errors,
        "forecast_bias": forecast_bias,
        "early_sales_data": early_sales_data,
        "early_sales_alerts": early_sales_alerts,
        "pipeline_products": pipeline_products,
        "promotion_effects": promotion_effects,
        "daily_orders": daily_orders,
        "forecast_overrides": forecast_overrides,
        "demand_history_adjustments": demand_history_adjustments,
    }
