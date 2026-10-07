"""ML Platform: models, performance metrics, alerts and retraining schedule."""
from datetime import datetime, timedelta


def generate(g):
    r = g.rng

    # Get some employees to use as model owners
    employees = g.master("employees")[:10]

    # Define models
    models = [
        {"model_id": "MOD-demand", "name": "Demand Forecast", "purpose": "Predict weekly demand by SKU", "owner": employees[0]},
        {"model_id": "MOD-pricing", "name": "Price Optimization", "purpose": "Recommend optimal selling prices", "owner": employees[1]},
        {"model_id": "MOD-supplier-delay", "name": "Supplier Delay Risk", "purpose": "Predict PO delivery delays", "owner": employees[2]},
        {"model_id": "MOD-churn", "name": "Customer Churn", "purpose": "Identify at-risk customers", "owner": employees[3]},
        {"model_id": "MOD-inventory", "name": "Inventory Optimizer", "purpose": "Optimize DC stock levels", "owner": employees[4]},
    ]

    # Features in the feature store
    features = [
        {"feature_id": "FEAT-daily-demand", "name": "Daily sales volume", "data_source": "OMS", "freshness": 24, "models": "MOD-demand,MOD-churn"},
        {"feature_id": "FEAT-price-history", "name": "Historical price changes", "data_source": "PIM", "freshness": 24, "models": "MOD-pricing"},
        {"feature_id": "FEAT-supplier-delivery-rate", "name": "Supplier on-time delivery %", "data_source": "PO", "freshness": 168, "models": "MOD-supplier-delay"},
        {"feature_id": "FEAT-weather-impact", "name": "Local weather events", "data_source": "External", "freshness": 12, "models": "MOD-demand"},
        {"feature_id": "FEAT-customer-lifecycle", "name": "Customer tenure and RFM", "data_source": "CRM", "freshness": 48, "models": "MOD-churn,MOD-demand"},
        {"feature_id": "FEAT-carrier-performance", "name": "Carrier delivery consistency", "data_source": "YMS", "freshness": 168, "models": "MOD-supplier-delay"},
        {"feature_id": "FEAT-port-congestion", "name": "Port delay indicators", "data_source": "External", "freshness": 48, "models": "MOD-supplier-delay"},
        {"feature_id": "FEAT-dc-stock-levels", "name": "DC inventory by site", "data_source": "WMS", "freshness": 6, "models": "MOD-inventory,MOD-demand"},
        {"feature_id": "FEAT-competitor-pricing", "name": "Competitor price intelligence", "data_source": "External", "freshness": 96, "models": "MOD-pricing"},
        {"feature_id": "FEAT-promotional-calendar", "name": "Planned promotions", "data_source": "Merchandising", "freshness": 168, "models": "MOD-demand,MOD-pricing"},
    ]

    registered_models = []
    metrics_data = []
    training_data = []
    alert_rules = []
    retraining_jobs = []
    backtest_results = []
    feature_store = []

    # Generate registered models
    for model in models:
        last_retrain = g.as_of - timedelta(days=r.randint(10, 60))
        next_retrain = g.as_of + timedelta(days=r.randint(5, 45))

        registered_models.append({
            "model_id": model["model_id"],
            "name": model["name"],
            "owner_id": model["owner"]["employee_id"],
            "purpose": model["purpose"],
            "status": r.choices(["active", "archived", "in_review"], [85, 10, 5])[0],
            "current_version": f"v{r.randint(1, 4)}.{r.randint(0, 9)}",
            "last_retrained": last_retrain,
            "next_scheduled_retrain": next_retrain,
            "created_at": g.as_of - timedelta(days=r.randint(180, 600)),
            "updated_at": g.as_of - timedelta(days=r.randint(0, 30)),
        })

    # Generate performance metrics (daily for last 90 days)
    for model in models:
        model_id = model["model_id"]
        # Generate degrading accuracy for MOD-demand (story for Q2)
        for i in range(90):
            metric_date = g.as_of - timedelta(days=i)

            # MOD-demand accuracy degrades over time (3 months ago worse, simulating drift)
            if model_id == "MOD-demand":
                # Start worse 90 days ago, gradually improve towards today
                accuracy_base = 76 + (i / 90) * 8  # Goes from 76 to 84 as we go back (reverse)
                if i < 30:  # Last month is stable at ~84
                    accuracy = 84 + r.gauss(0, 0.5)
                elif i < 60:
                    accuracy = 82 + r.gauss(0, 1)
                else:
                    accuracy = 78 + r.gauss(0, 1.5)

                # Drift increases going back
                drift = 12 + (i / 90) * 25
            else:
                accuracy = r.gauss(85, 3) if model_id != "MOD-churn" else r.gauss(76, 4)
                drift = r.gauss(8, 4) if i < 30 else r.gauss(5, 3)

            metrics_data.append({
                "model_id": model_id,
                "metric_date": metric_date,
                "accuracy": round(max(65, min(95, accuracy)), 2),
                "precision": round(max(60, min(98, r.gauss(accuracy - 2, 2))), 2) if accuracy > 70 else None,
                "recall": round(max(60, min(98, r.gauss(accuracy - 3, 2))), 2) if accuracy > 70 else None,
                "feature_drift_score": round(max(0, min(100, drift)), 1),
                "data_freshness_hours": r.randint(1, 48) if r.random() > 0.1 else r.randint(48, 168),
                "prediction_count": r.randint(1000, 50000),
                "updated_at": datetime.combine(metric_date, datetime.min.time()),
            })

    # Generate training datasets
    for model in models:
        model_id = model["model_id"]
        # Current and one previous version
        for v_idx, version in enumerate(["v2.1", "v2.2"]):
            training_end = g.as_of - timedelta(days=v_idx * 45)
            training_start = training_end - timedelta(days=365)

            training_data.append({
                "model_id": model_id,
                "dataset_version": version,
                "training_start_date": training_start,
                "training_end_date": training_end,
                "row_count": r.randint(50000, 500000),
                "feature_count": r.randint(15, 60),
                "target_coverage_pct": round(r.gauss(92, 4), 1),
                "created_at": training_end + timedelta(days=1),
            })

    # Generate alert rules
    rule_id = 0
    for model in models:
        model_id = model["model_id"]
        # Most models have drift alerts, some have accuracy alerts
        if r.random() > 0.3:
            rule_id += 1
            alert_rules.append({
                "alert_rule_id": f"RULE-{rule_id:06d}",
                "model_id": model_id,
                "rule_type": "drift",
                "threshold": r.choice([10, 15, 20, 25]),
                "enabled": r.choices([True, False], [90, 10])[0],
                "created_at": g.as_of - timedelta(days=r.randint(30, 180)),
                "updated_at": g.as_of - timedelta(days=r.randint(0, 30)),
            })

        if r.random() > 0.5:
            rule_id += 1
            alert_rules.append({
                "alert_rule_id": f"RULE-{rule_id:06d}",
                "model_id": model_id,
                "rule_type": "accuracy",
                "threshold": round(r.gauss(80, 3), 1),
                "enabled": r.choices([True, False], [95, 5])[0],
                "created_at": g.as_of - timedelta(days=r.randint(30, 180)),
                "updated_at": g.as_of - timedelta(days=r.randint(0, 30)),
            })

    # Generate retraining jobs
    job_id = 0
    for model in models:
        model_id = model["model_id"]
        # Completed job
        job_id += 1
        completed_date = g.as_of - timedelta(days=r.randint(15, 60))
        retraining_jobs.append({
            "job_id": f"RET-{job_id:06d}",
            "model_id": model_id,
            "dataset_version": "v2.1",
            "status": "completed",
            "scheduled_date": completed_date - timedelta(days=2),
            "started_at": completed_date - timedelta(days=1),
            "completed_at": completed_date,
            "new_accuracy": round(r.gauss(84, 3), 2),
            "improvement_vs_current": round(r.gauss(2.5, 1.5), 2),
            "created_at": completed_date,
        })

        # Scheduled or running job
        if r.random() > 0.6:
            job_id += 1
            scheduled = g.as_of + timedelta(days=r.randint(5, 30))
            status = "scheduled" if scheduled > g.as_of else "running"
            retraining_jobs.append({
                "job_id": f"RET-{job_id:06d}",
                "model_id": model_id,
                "dataset_version": "v2.2",
                "status": status,
                "scheduled_date": scheduled,
                "started_at": scheduled if status == "running" else None,
                "completed_at": None,
                "new_accuracy": None,
                "improvement_vs_current": None,
                "created_at": g.as_of,
            })

    # Generate backtest results
    bt_id = 0
    candidate_models = ["MOD-demand-v3", "MOD-pricing-v3"]
    for candidate in candidate_models:
        # Get the base model name
        base = "-".join(candidate.split("-")[:-1]) if "-" in candidate else candidate
        current_model = base  # Use base as current

        for model in models:
            if model["model_id"] in [base, "MOD-demand", "MOD-pricing"]:
                if r.random() > 0.7:
                    bt_id += 1
                    candidate_acc = round(r.gauss(87, 2), 2)
                    current_acc = round(r.gauss(82, 2), 2)
                    uplift = round((candidate_acc - current_acc) / current_acc * 100, 2)

                    backtest_results.append({
                        "backtest_id": f"BT-{bt_id:06d}",
                        "candidate_model_id": candidate,
                        "current_model_id": model["model_id"],
                        "test_period_start": g.as_of - timedelta(days=60),
                        "test_period_end": g.as_of - timedelta(days=1),
                        "candidate_accuracy": candidate_acc,
                        "current_accuracy": current_acc,
                        "uplift_pct": uplift,
                        "estimated_benefit_gbp": round(r.gauss(50000, 20000), 2),
                        "recommendation": "deploy" if uplift > 2 else "hold",
                        "created_at": g.as_of - timedelta(days=r.randint(1, 14)),
                    })

    # Generate feature store
    for feature in features:
        feature_store.append({
            "feature_id": feature["feature_id"],
            "name": feature["name"],
            "description": f"Calculated from {feature['data_source']} feeds. Updated every {feature['freshness']} hours.",
            "data_source": feature["data_source"],
            "freshness_hours": feature["freshness"],
            "used_by_models": feature["models"],
            "last_updated": g.as_of - timedelta(hours=r.randint(0, feature["freshness"])),
            "created_at": g.as_of - timedelta(days=r.randint(60, 300)),
        })

    return {
        "registered_models": registered_models,
        "model_performance_metrics": metrics_data,
        "model_training_datasets": training_data,
        "feature_store_entries": feature_store,
        "model_alert_rules": alert_rules,
        "retraining_jobs": retraining_jobs,
        "model_backtest_results": backtest_results,
    }
