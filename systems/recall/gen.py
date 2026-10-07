"""Background recall data: low-level incident noise. The recall stories (PF-220 battery, kids' products,
past battery recalls and their costs) are planted in seed/*.csv."""
from datetime import timedelta

STORY_SKUS = {"PF-220", "K-1700", "SKU-100112"}
# categories whose history is planted in seed/incident_history.csv: no random noise there
STORY_CATEGORIES = {"Babywear", "Schoolwear", "Nightwear", "Personal Care", "Small Appliances", "Smart Home", "Audio"}
ISSUES = {
    "Fragrance": ["Bottle cap leaking", "Skin irritation reported"],
    "Haircare": ["Aerosol valve leaking", "Skin irritation reported"],
    "Bodycare": ["Skin irritation reported", "Pump dispenser failure"],
    "Skincare": ["Skin irritation reported"],
    "Lighting": ["Cord damaged at base", "Bulb holder loose"],
    "Cookware": ["Handle loose", "Coating flaking"],
    "Drinkware": ["Glass chipped on arrival", "Lid seal failure"],
    "Footwear": ["Sole separation", "Buckle failure"],
    "Jewellery": ["Skin reaction reported", "Clasp failure"],
}
DEFAULT_ISSUES = ["Seam failure", "Zip failure", "Colour transfer", "Button detached"]
DESCRIPTIONS = ["Customer says the item failed after a few uses", "Item arrived damaged and was returned",
                "Customer reports a rash after use", "Part came loose in normal use", "Customer reports a strong smell"]


def generate(g):
    r = g.rng
    products = [p for p in g.master("products") if p["sku"] not in STORY_SKUS]
    customers = g.master("customers")

    incidents = []
    for _ in range(8):
        p = r.choice(products)
        incidents.append({
            "incident_id": f"INC-{len(incidents) + 1:06d}",
            "sku": p["sku"],
            "reported_at": g.days_ago(r.randint(20, 170)),
            "customer_id": r.choice(customers)["customer_id"],
            "batch_id": "",
            "description": r.choice(DESCRIPTIONS),
            "severity": r.choices(["minor", "moderate"], [70, 30])[0],
            "injury_reported": "none",
            "status": r.choices(["resolved", "investigating"], [80, 20])[0],
        })

    history = []
    by_cat = {}
    for p in g.master("products"):
        if p["category"] not in STORY_CATEGORIES:
            by_cat.setdefault(p["category"], []).append(p)
    for cat in sorted(by_cat):
        for _ in range(r.choice([0, 0, 1, 1, 2])):
            p = r.choice(by_cat[cat])
            history.append({
                "history_id": f"HIST-{1000 + len(history) + 1:04d}",
                "sku": p["sku"],
                "reported_at": g.days_ago(r.randint(60, 1300)),
                "issue": r.choice(ISSUES.get(cat, DEFAULT_ISSUES)),
                "severity": r.choices(["minor", "moderate"], [65, 35])[0],
                "units_sold": 0,
                "outcome": "no_action",
                "recall_id": "",
                "reputational_outcome": "",
                "comms_lessons": "",
            })

    return {
        "incidents": incidents,
        "recall_cases": [],
        "recall_costs": [],
        "regulator_formats": [],
        "regulatory_notifications": [],
        "store_instructions": [],
        "draft_communications": [],
        "incident_history": history,
    }
