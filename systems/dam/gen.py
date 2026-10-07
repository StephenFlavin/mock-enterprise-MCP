"""Background DAM data: trend assets and mood boards for design team."""
from datetime import datetime, timedelta


def generate(g):
    r = g.rng
    employees = g.master("employees")
    design_team = [e for e in employees if "design" in e["department"].lower() or "merchant" in e["department"].lower()]
    if not design_team:
        design_team = employees[:10]  # fallback

    # Generate assets
    asset_topics = [
        ("Earthy Tones", "colour"),
        ("Bold Patterns", "pattern"),
        ("Natural Materials", "material"),
        ("Minimalist Silhouettes", "silhouette"),
        ("Oversized Proportions", "silhouette"),
        ("Sustainable Fabrics", "material"),
        ("Jewel Tones", "colour"),
        ("Maxi Length", "silhouette"),
    ]

    assets = []
    for i, (title, asset_type_val) in enumerate(asset_topics * 3):
        asset_id = f"AST-{i+1:05d}"
        created = g.as_of - timedelta(days=r.randint(60, 180))
        assets.append({
            "asset_id": asset_id,
            "title": f"{title} Reference {i % len(asset_topics) + 1}",
            "asset_type": "reference",
            "url": f"/dam/assets/{asset_id}.jpg",
            "created_at": created,
            "created_by": r.choice(design_team)["employee_id"],
            "metadata": title,
            "status": "active"
        })

    # Generate mood boards
    boards = []
    seasons = ["SS27", "AW27", "SS26", "AW26"]
    categories = ["women", "menswear", "home"]

    for idx, season in enumerate(seasons):
        for cat_idx, category in enumerate(categories):
            board_id = f"MB-{idx * len(categories) + cat_idx + 1:06d}"
            created = g.as_of - timedelta(days=r.randint(20, 90))
            boards.append({
                "board_id": board_id,
                "title": f"{season} {category.title()} Trends",
                "description": f"Key trends for {season} {category} collection",
                "season": season,
                "category": category,
                "created_at": created,
                "created_by": r.choice(design_team)["employee_id"],
                "updated_at": created + timedelta(days=r.randint(1, 30)),
                "status": "published"
            })

    # Generate board items
    board_items = []
    item_no = 1
    for board in boards:
        # Add 3-7 assets to each board
        num_items = r.randint(3, 7)
        selected_assets = r.sample(assets, num_items)
        for asset in selected_assets:
            board_items.append({
                "board_id": board["board_id"],
                "item_no": item_no,
                "asset_id": asset["asset_id"],
                "added_at": board["created_at"] + timedelta(days=r.randint(0, 5)),
                "added_by": board["created_by"]
            })
            item_no += 1

    return {
        "dam_assets": assets,
        "mood_boards": boards,
        "board_items": board_items
    }
