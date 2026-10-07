"""Customer Data Platform: segment profiles and behavioral metrics."""


def generate(g):
    # Define segments with realistic characteristics
    segments_data = [
        {
            "segment_id": "SEG-001",
            "segment_name": "Premium Loyalists",
            "description": "Affluent, established customers who prioritize quality and service",
            "primary_region": "UK South",
            "profile_age_min": 45,
            "profile_age_max": 65,
            "profile_spend_tier": "high",
            "customer_count": 12500,
            "avg_annual_spend_gbp": 850.0,
        },
        {
            "segment_id": "SEG-002",
            "segment_name": "Fast Fashion Hunters",
            "description": "Price-conscious, trend-aware younger shoppers who shop frequently",
            "primary_region": "UK North",
            "profile_age_min": 18,
            "profile_age_max": 35,
            "profile_spend_tier": "medium",
            "customer_count": 45000,
            "avg_annual_spend_gbp": 420.0,
        },
        {
            "segment_id": "SEG-003",
            "segment_name": "Conscious Shoppers",
            "description": "Sustainability-focused customers interested in circular economy",
            "primary_region": "EU Central",
            "profile_age_min": 25,
            "profile_age_max": 50,
            "profile_spend_tier": "medium",
            "customer_count": 8200,
            "avg_annual_spend_gbp": 540.0,
        },
        {
            "segment_id": "SEG-004",
            "segment_name": "Essential Buyers",
            "description": "Value-focused customers buying basics and essentials only",
            "primary_region": "UK",
            "profile_age_min": 35,
            "profile_age_max": 60,
            "profile_spend_tier": "low",
            "customer_count": 28000,
            "avg_annual_spend_gbp": 280.0,
        },
        {
            "segment_id": "SEG-005",
            "segment_name": "Trend Followers",
            "description": "Young, fashion-forward customers highly engaged with trends",
            "primary_region": "UK South",
            "profile_age_min": 16,
            "profile_age_max": 28,
            "profile_spend_tier": "medium",
            "customer_count": 35000,
            "avg_annual_spend_gbp": 380.0,
        },
    ]

    # Behavioral metrics for each segment
    behaviors_data = [
        {
            "segment_id": "SEG-001",
            "return_rate_pct": 8.5,
            "return_refund_sensitivity_pct": 25.0,  # 25% reduce spend if charges introduced
            "markdown_wait_propensity_pct": 12.0,
            "markdown_conversion_elasticity": 1.15,
            "stockout_sensitivity_pct": 15.0,
            "resale_participation_pct": 5.0,
            "resale_barrier": "price",
            "repeat_purchase_rate_pct": 72.0,
            "avg_basket_size_gbp": 142.0,
        },
        {
            "segment_id": "SEG-002",
            "return_rate_pct": 24.5,
            "return_refund_sensitivity_pct": 55.0,  # Very sensitive to charges
            "markdown_wait_propensity_pct": 68.0,  # High propensity to wait
            "markdown_conversion_elasticity": 2.1,  # High elasticity
            "stockout_sensitivity_pct": 22.0,
            "resale_participation_pct": 12.0,
            "resale_barrier": "effort",
            "repeat_purchase_rate_pct": 48.0,
            "avg_basket_size_gbp": 65.0,
        },
        {
            "segment_id": "SEG-003",
            "return_rate_pct": 14.2,
            "return_refund_sensitivity_pct": 35.0,
            "markdown_wait_propensity_pct": 32.0,
            "markdown_conversion_elasticity": 1.55,
            "stockout_sensitivity_pct": 18.0,
            "resale_participation_pct": 62.0,  # High resale participation
            "resale_barrier": "none",
            "repeat_purchase_rate_pct": 65.0,
            "avg_basket_size_gbp": 92.0,
        },
        {
            "segment_id": "SEG-004",
            "return_rate_pct": 11.8,
            "return_refund_sensitivity_pct": 62.0,  # Very sensitive to charges
            "markdown_wait_propensity_pct": 42.0,
            "markdown_conversion_elasticity": 1.45,
            "stockout_sensitivity_pct": 58.0,  # Highly sensitive to stockouts
            "resale_participation_pct": 3.0,
            "resale_barrier": "awareness",
            "repeat_purchase_rate_pct": 52.0,
            "avg_basket_size_gbp": 48.0,
        },
        {
            "segment_id": "SEG-005",
            "return_rate_pct": 28.3,
            "return_refund_sensitivity_pct": 40.0,
            "markdown_wait_propensity_pct": 55.0,
            "markdown_conversion_elasticity": 1.95,
            "stockout_sensitivity_pct": 25.0,
            "resale_participation_pct": 22.0,
            "resale_barrier": "effort",
            "repeat_purchase_rate_pct": 44.0,
            "avg_basket_size_gbp": 72.0,
        },
    ]

    return {"segments": segments_data, "segment_behaviors": behaviors_data}
