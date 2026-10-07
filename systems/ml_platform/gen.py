"""ML Platform: model registry, daily performance metrics, alerts, retraining, backtests, feature store.

Registry, datasets, alerts, jobs, backtests and the feature store are hand-written in seed/*.csv.
Only the daily performance history is generated here (120 days per model), as clean trend lines
with small noise, so the planted story is easy to find:
  MOD-demand held ~85% accuracy and ~5 drift until about 13 weeks ago, then degraded steadily
  to ~76% accuracy and ~29 drift today. The other models are stable.
"""
from datetime import datetime, timedelta

DAYS = 120
STORY_START = 90  # days ago when MOD-demand starts to degrade

# model -> (accuracy today, accuracy before, drift today, drift before, freshness hours, daily predictions)
MODELS = {
    "MOD-demand": (76.4, 85.2, 28.6, 5.0, 24, 45000),
    "MOD-pricing": (86.5, 86.0, 5.2, 5.0, 16, 52000),
    "MOD-supplier-delay": (82.3, 81.8, 6.8, 7.0, 24, 38000),
    "MOD-churn": (75.8, 76.0, 12.1, 12.0, 30, 28000),
    "MOD-inventory": (88.2, 88.0, 4.1, 4.3, 12, 61000),
}


def generate(g):
    r = g.rng
    metrics = []
    for model_id, (acc_now, acc_before, drift_now, drift_before, fresh, preds) in MODELS.items():
        for i in range(DAYS):
            d = g.as_of - timedelta(days=i)
            if model_id == "MOD-demand":
                if i >= STORY_START:
                    acc, drift = acc_before, drift_before
                else:
                    frac = i / STORY_START  # 0 today .. 1 at the start of the decline
                    acc = acc_now + frac * (acc_before - acc_now)
                    drift = drift_now - frac * (drift_now - drift_before)
            else:
                acc = acc_now + (acc_before - acc_now) * min(1, i / 60)
                drift = drift_now + (drift_before - drift_now) * min(1, i / 60)
            acc = acc + r.gauss(0, 0.35)
            drift = max(0.5, drift + r.gauss(0, 0.4))
            metrics.append({
                "model_id": model_id,
                "metric_date": d,
                "accuracy": round(acc, 1),
                "precision": round(acc + 0.8 + r.gauss(0, 0.3), 1),
                "recall": round(acc - 0.7 + r.gauss(0, 0.3), 1),
                "feature_drift_score": round(drift, 1),
                "data_freshness_hours": max(1, int(fresh + r.gauss(0, 3))),
                "prediction_count": int(preds * (1 + r.gauss(0, 0.04))),
                "updated_at": datetime.combine(d, datetime.min.time()) + timedelta(hours=23),
            })
    return {
        "registered_models": [],
        "model_performance_metrics": metrics,
        "model_training_datasets": [],
        "feature_store_entries": [],
        "model_alert_rules": [],
        "retraining_jobs": [],
        "model_backtest_results": [],
    }
