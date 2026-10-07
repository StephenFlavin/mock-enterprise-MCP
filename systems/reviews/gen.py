"""Customer reviews and feedback for products, stores and competitors."""
from datetime import datetime, timedelta


def generate(g):
    r = g.rng
    fake = g.fake

    # Get sample SKUs from master data
    products = g.master("products")[:100]  # Use first 100 products to keep volume reasonable
    suppliers = g.master("suppliers")[:50]
    stores = [s for s in g.master("sites") if s["type"] == "store"][:30]

    themes = ["sizing", "quality", "durability", "fit", "comfort", "value", "color", "packaging"]
    segments = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+", "outdoor_enthusiast", "professional", "budget_conscious"]

    # Generate reviews
    reviews = []
    review_templates = {
        "sizing": [
            "Runs small, recommend ordering a size up",
            "Perfect fit, true to size",
            "Much larger than expected, had to return",
            "Narrow fit, not suitable for wide feet",
            "Great sizing, exactly as described"
        ],
        "quality": [
            "Excellent quality, will last years",
            "Seams started coming apart after a month",
            "Good value for money but not premium",
            "Superior craftsmanship throughout",
            "Quality issues - zipper broke immediately"
        ],
        "durability": [
            "Used daily for 3 months, still holding up well",
            "Started falling apart after light use",
            "Incredibly durable, worth the investment",
            "Material faded quickly in sunlight",
            "Proven design that lasts"
        ],
        "fit": [
            "Flattering cut, perfect silhouette",
            "Too loose around the middle",
            "Hugs the body nicely without restricting movement",
            "Awkward fit, doesn't work with my body shape",
            "Just right for active wear"
        ],
        "comfort": [
            "So comfortable I want to wear it all day",
            "Scratchy material, irritates skin",
            "Perfect comfort level for extended wear",
            "Too stiff, needs breaking in",
            "Soft and breathable"
        ],
        "value": [
            "Excellent value, better than competitors",
            "Overpriced for what you get",
            "Worth every penny",
            "Could find similar for much less elsewhere",
            "Fair price for the quality"
        ],
        "color": [
            "Color is exactly as shown online",
            "Much darker/lighter in person than pictures",
            "Vibrant and long-lasting color",
            "Color faded after first wash",
            "Beautiful shade, matches description"
        ],
        "packaging": [
            "Arrived in perfect condition",
            "Packaging was torn, item slightly damaged",
            "Nice presentation in packaging",
            "Arrived squashed and creased",
            "Protected well during shipping"
        ]
    }

    # Create reviews for each product
    review_id = 1
    for product in products:
        sku = product["sku"]
        style_id = product.get("style_id", "STY-0000")
        supplier_id = product.get("supplier_id", "SUP-0001")

        # Generate 20-50 reviews per product
        num_reviews = r.randint(20, 50)
        for _ in range(num_reviews):
            theme = r.choice(themes)
            segment = r.choice(segments)

            # Rating is influenced by theme (some themes more negative than others)
            if theme in ["quality", "durability"]:
                rating = r.choices([1, 2, 3, 4, 5], weights=[5, 10, 20, 35, 30])[0]
            elif theme in ["fit", "sizing"]:
                rating = r.choices([1, 2, 3, 4, 5], weights=[8, 12, 20, 30, 30])[0]
            else:
                rating = r.choices([1, 2, 3, 4, 5], weights=[5, 8, 15, 35, 37])[0]

            # Random date in the past 180 days
            days_ago = r.randint(0, 180)
            created_at = g.as_of - timedelta(days=days_ago)

            # Store feedback is less common (maybe 10% of reviews)
            store_id = r.choice(stores)["site_id"] if r.random() < 0.1 else None

            review_text = r.choice(review_templates[theme])

            reviews.append({
                "review_id": f"REV-{review_id:06d}",
                "sku": sku,
                "style_id": style_id,
                "store_id": store_id,
                "customer_segment": segment,
                "rating": rating,
                "review_text": review_text,
                "theme": theme,
                "created_at": created_at
            })
            review_id += 1

    # Generate competitor products with ratings
    competitors = ["SportGear Co", "ActiveWear Inc", "OutdoorMax", "PerformanceGear", "EcoOutfitters"]
    categories = ["insulated bottle", "shoes", "jeans", "outerwear", "technical clothing", "lunch box", "athletic wear"]

    competitor_products = []
    comp_id = 1
    for _ in range(150):
        competitor_name = r.choice(competitors)
        category = r.choice(categories)
        avg_rating = round(r.uniform(2.5, 4.8), 1)
        review_count = r.randint(50, 1000)
        price_gbp = round(r.uniform(15, 200), 2)

        competitor_products.append({
            "competitor_product_id": f"COMP-{comp_id:06d}",
            "competitor_name": competitor_name,
            "category": category,
            "product_name": f"{category.title()} #{comp_id}",
            "price_gbp": price_gbp,
            "avg_rating": avg_rating,
            "review_count": review_count,
            "collected_at": g.as_of - timedelta(days=r.randint(1, 30))
        })
        comp_id += 1

    return {"reviews": reviews, "competitor_products": competitor_products}
