"""Test lab data: test requests, results, methods, and wear trials."""
from datetime import datetime, timedelta


def generate(g):
    r = g.rng
    fake = g.fake
    as_of = g.as_of

    # Products, styles and lots that carry planted stories (see seed/): background noise must never touch them
    story_skus = {"SKU-100007", "SKU-100014", "SKU-100021", "SKU-100091", "SKU-100651", "SKU-100658", "SKU-101813",
                  "SKU-103164", "SKU-103199", "SKU-103745", "SKU-103808", "SKU-104123", "SKU-104795", "SKU-104809",
                  "SKU-105551", "SKU-102590", "K-1700", "PF-220"}
    story_styles = {"STY-4012", "STY-7731", "STY-8110", "STY-4420", "STY-4066"}
    products = g.master("products")
    skus = [p["sku"] for p in products[:60] if p["sku"] not in story_skus][:30]
    suppliers = [s["supplier_id"] for s in g.master("suppliers")[:20]]
    styles = sorted({p["style_id"] for p in products[:60] if p["style_id"] not in story_styles})[:10]
    # lab technicians = Quality department
    employees = [e["employee_id"] for e in g.master("employees") if e["department"] == "Quality"][:6]

    # Test methods - define standard test procedures
    all_markets = "UK,EU,US,AU"
    test_methods = [
        {"test_method_id": "TMT-0001", "name": "Colourfastness to Rubbing", "category": "fabric",
         "standard": "ISO 105-X12", "description": "Dry and wet rubbing colourfastness, graded 1 (poor) to 5 (excellent) on the grey scale",
         "specimen_size": "5x5cm", "duration_minutes": 30, "lead_time_days": 3,
         "cost_gbp": 45.0, "applicable_materials": "cotton,polyester,nylon,wool,blended",
         "requires_retest_on_fail": True, "markets": all_markets, "applies_to": "fabric colour, dyed fabric, garments"},
        {"test_method_id": "TMT-0002", "name": "Shrinkage Test", "category": "fabric",
         "standard": "ISO 6330 / ISO 5077", "description": "Dimensional change (length and width) after domestic washing and drying",
         "specimen_size": "50x50cm", "duration_minutes": 120, "lead_time_days": 5,
         "cost_gbp": 55.0, "applicable_materials": "cotton,polyester,nylon,wool,silk,blended",
         "requires_retest_on_fail": True, "markets": all_markets, "applies_to": "fabric, knitwear, garments"},
        {"test_method_id": "TMT-0003", "name": "Abrasion Resistance", "category": "fabric",
         "standard": "ISO 12947-2", "description": "Martindale abrasion: cycles to specimen breakdown",
         "specimen_size": "140mm circle", "duration_minutes": 240, "lead_time_days": 7,
         "cost_gbp": 85.0, "applicable_materials": "all",
         "requires_retest_on_fail": True, "markets": all_markets, "applies_to": "fabric durability"},
        {"test_method_id": "TMT-0004", "name": "Tear Strength", "category": "fabric",
         "standard": "ISO 13937-1", "description": "Tear strength using the pendulum (Elmendorf) method",
         "specimen_size": "7.5x10cm", "duration_minutes": 45, "lead_time_days": 3,
         "cost_gbp": 50.0, "applicable_materials": "fabric",
         "requires_retest_on_fail": True, "markets": all_markets, "applies_to": "fabric durability"},
        {"test_method_id": "TMT-0005", "name": "Zip Strength Test", "category": "sample",
         "standard": "ASTM D2061", "description": "Zip pull strength: force to detach puller, slider and tape from the chain",
         "specimen_size": "zip assembly", "duration_minutes": 30, "lead_time_days": 2,
         "cost_gbp": 35.0, "applicable_materials": "sample",
         "requires_retest_on_fail": True, "markets": all_markets, "applies_to": "zips, trims, bags, garments"},
        {"test_method_id": "TMT-0006", "name": "Seam Strength", "category": "sample",
         "standard": "ISO 13935-2", "description": "Seam strength and seam slippage under tension (grab method)",
         "specimen_size": "seam strip 5x25cm", "duration_minutes": 30, "lead_time_days": 2,
         "cost_gbp": 40.0, "applicable_materials": "sample",
         "requires_retest_on_fail": True, "markets": all_markets, "applies_to": "seams, garments, outerwear"},
        {"test_method_id": "TMT-0007", "name": "Water Resistance Spray Test", "category": "fabric",
         "standard": "ISO 4920", "description": "Spray test for surface wetting resistance, rated 0 to 100",
         "specimen_size": "18x18cm", "duration_minutes": 30, "lead_time_days": 2,
         "cost_gbp": 45.0, "applicable_materials": "fabric,finish",
         "requires_retest_on_fail": True, "markets": all_markets, "applies_to": "water repellency, outerwear, DWR finish"},
        {"test_method_id": "TMT-0008", "name": "DWR Wash Durability", "category": "finish",
         "standard": "ISO 4920 after ISO 6330 washes", "description": "Spray rating after repeated domestic washing",
         "specimen_size": "18x18cm", "duration_minutes": 180, "lead_time_days": 10,
         "cost_gbp": 120.0, "applicable_materials": "DWR,finish",
         "requires_retest_on_fail": True, "markets": all_markets, "applies_to": "water repellency, DWR finish"},
        {"test_method_id": "TMT-0009", "name": "Hydrostatic Head", "category": "fabric",
         "standard": "ISO 811", "description": "Water penetration pressure (mm water column), including seams",
         "specimen_size": "20x20cm or seam", "duration_minutes": 45, "lead_time_days": 3,
         "cost_gbp": 65.0, "applicable_materials": "fabric,sample",
         "requires_retest_on_fail": True, "markets": all_markets, "applies_to": "waterproofing, seams, outerwear"},
        {"test_method_id": "TMT-0010", "name": "Drop Test - 1.2m", "category": "pack",
         "standard": "ISTA 3A", "description": "Drop test from 1.2m height on faces, edges and corners",
         "specimen_size": "full carton", "duration_minutes": 60, "lead_time_days": 3,
         "cost_gbp": 75.0, "applicable_materials": "pack,product",
         "requires_retest_on_fail": True, "markets": all_markets, "applies_to": "packaging, cartons, trays, glass items"},
        {"test_method_id": "TMT-0011", "name": "Crush Test", "category": "pack",
         "standard": "ASTM D642", "description": "Compression test for package crushing",
         "specimen_size": "full carton", "duration_minutes": 90, "lead_time_days": 3,
         "cost_gbp": 85.0, "applicable_materials": "pack,carton",
         "requires_retest_on_fail": True, "markets": all_markets, "applies_to": "packaging, cartons, pallets"},
        {"test_method_id": "TMT-0012", "name": "Drop and Crush", "category": "pack",
         "standard": "ISTA 3A", "description": "Combined drop and crush test",
         "specimen_size": "full carton", "duration_minutes": 120, "lead_time_days": 5,
         "cost_gbp": 130.0, "applicable_materials": "pack,carton",
         "requires_retest_on_fail": True, "markets": all_markets, "applies_to": "packaging, cartons"},
        {"test_method_id": "TMT-0013", "name": "Chromium VI Test", "category": "safety",
         "standard": "ISO 17075-1", "description": "Hexavalent chromium (Cr VI) in leather, mg/kg; limit 3 mg/kg",
         "specimen_size": "leather sample", "duration_minutes": 240, "lead_time_days": 14,
         "cost_gbp": 250.0, "applicable_materials": "leather",
         "requires_retest_on_fail": True, "markets": "UK,EU,US", "applies_to": "leather, bags, footwear, restricted substances"},
        {"test_method_id": "TMT-0014", "name": "Heavy Metals Test", "category": "safety",
         "standard": "EN 71-3 / ASTM F963 / AS/NZS ISO 8124.3", "description": "Migration of lead, cadmium, chromium and other heavy metals",
         "specimen_size": "product sample", "duration_minutes": 240, "lead_time_days": 14,
         "cost_gbp": 350.0, "applicable_materials": "all",
         "requires_retest_on_fail": True, "markets": all_markets,
         "applies_to": "children's products, bottles, drinkware, toys, painted surfaces, heavy metals"},
        {"test_method_id": "TMT-0015", "name": "Food Contact Migration", "category": "safety",
         "standard": "EU 10/2011 / BS EN 13130 / FDA 21 CFR 177", "description": "Overall and specific migration from food-contact stainless steel, silicone and plastics",
         "specimen_size": "complete item", "duration_minutes": 480, "lead_time_days": 10,
         "cost_gbp": 420.0, "applicable_materials": "stainless steel,silicone,plastic",
         "requires_retest_on_fail": True, "markets": all_markets,
         "applies_to": "food contact, children's bottles, drinkware, straws, silicone, stainless steel"},
        {"test_method_id": "TMT-0016", "name": "Small Parts and Use-and-Abuse", "category": "safety",
         "standard": "EN 71-1 / 16 CFR 1501 / AS/NZS ISO 8124.1", "description": "Small parts cylinder, torque and tension tests for choking hazards, e.g. removable straw tips",
         "specimen_size": "complete item", "duration_minutes": 90, "lead_time_days": 7,
         "cost_gbp": 280.0, "applicable_materials": "all",
         "requires_retest_on_fail": True, "markets": all_markets,
         "applies_to": "children's products, small parts, choking hazard, bottles, straw tip"},
        {"test_method_id": "TMT-0017", "name": "Lead in Surface Coatings", "category": "safety",
         "standard": "CPSIA 16 CFR 1303", "description": "Total lead in paint and surface coatings of children's products",
         "specimen_size": "coated item", "duration_minutes": 120, "lead_time_days": 7,
         "cost_gbp": 180.0, "applicable_materials": "all",
         "requires_retest_on_fail": True, "markets": "US",
         "applies_to": "children's products, painted surfaces, bottles, lead"},
        {"test_method_id": "TMT-0018", "name": "Labelling and Age Warning Review", "category": "safety",
         "standard": "EN 71-1 clause 7 / 16 CFR 1500.19", "description": "Check of labels, age grading, warnings and traceability marks",
         "specimen_size": "label and packaging", "duration_minutes": 60, "lead_time_days": 3,
         "cost_gbp": 150.0, "applicable_materials": "all",
         "requires_retest_on_fail": False, "markets": all_markets,
         "applies_to": "labelling, age warnings, children's products, bottles"},
        {"test_method_id": "TMT-0019", "name": "Battery Safety (Li-ion)", "category": "safety",
         "standard": "IEC 62133-2", "description": "Safety of lithium cells and batteries: overcharge, short circuit, thermal abuse",
         "specimen_size": "battery pack, 10 units", "duration_minutes": 960, "lead_time_days": 25,
         "cost_gbp": 1850.0, "applicable_materials": "all",
         "requires_retest_on_fail": True, "markets": "UK,EU,US",
         "applies_to": "battery, lithium, smart bottle, rechargeable products"},
        {"test_method_id": "TMT-0020", "name": "UN 38.3 Transport Test", "category": "safety",
         "standard": "UN 38.3", "description": "Lithium battery transport tests: altitude, thermal, vibration, shock, short circuit",
         "specimen_size": "battery pack, 20 units", "duration_minutes": 1200, "lead_time_days": 28,
         "cost_gbp": 2400.0, "applicable_materials": "all",
         "requires_retest_on_fail": True, "markets": all_markets,
         "applies_to": "battery, lithium, smart bottle, transport"},
        {"test_method_id": "TMT-0021", "name": "Radio Equipment (Bluetooth)", "category": "safety",
         "standard": "EN 300 328 (RED) / UK Radio Equipment Regs", "description": "Radio spectrum tests for 2.4 GHz Bluetooth modules (CE RED and UKCA)",
         "specimen_size": "2 working units", "duration_minutes": 480, "lead_time_days": 20,
         "cost_gbp": 2200.0, "applicable_materials": "all",
         "requires_retest_on_fail": True, "markets": "UK,EU",
         "applies_to": "radio, Bluetooth, smart bottle, connected products, CE, UKCA"},
        {"test_method_id": "TMT-0022", "name": "EMC Test", "category": "safety",
         "standard": "EN 301 489-1 / EN 55032", "description": "Electromagnetic emissions and immunity",
         "specimen_size": "2 working units", "duration_minutes": 360, "lead_time_days": 15,
         "cost_gbp": 1600.0, "applicable_materials": "all",
         "requires_retest_on_fail": True, "markets": "UK,EU",
         "applies_to": "EMC, electrical, smart bottle, connected products, CE, UKCA"},
        {"test_method_id": "TMT-0023", "name": "Electrical Safety", "category": "safety",
         "standard": "EN IEC 62368-1", "description": "Electrical and fire safety of USB-charged electronic products",
         "specimen_size": "3 working units", "duration_minutes": 600, "lead_time_days": 18,
         "cost_gbp": 2000.0, "applicable_materials": "all",
         "requires_retest_on_fail": True, "markets": "UK,EU",
         "applies_to": "electrical, USB-C charging, smart bottle, connected products, CE, UKCA"},
        {"test_method_id": "TMT-0024", "name": "Tensile Strength", "category": "fabric",
         "standard": "ISO 13934-1", "description": "Breaking force of fabric strips",
         "specimen_size": "5x20cm", "duration_minutes": 30, "lead_time_days": 3,
         "cost_gbp": 50.0, "applicable_materials": "fabric",
         "requires_retest_on_fail": True, "markets": all_markets, "applies_to": "fabric durability"},
        {"test_method_id": "TMT-0025", "name": "Pilling Resistance", "category": "fabric",
         "standard": "ISO 12945-2", "description": "Martindale pilling grade 1 (severe) to 5 (none) after 2000 revolutions",
         "specimen_size": "140mm circle", "duration_minutes": 120, "lead_time_days": 5,
         "cost_gbp": 60.0, "applicable_materials": "all",
         "requires_retest_on_fail": True, "markets": all_markets, "applies_to": "fabric appearance retention, knitwear"},
    ]

    # Reference fabrics - for comparison
    reference_fabrics = [
        {"reference_fabric_id": "REF-0001", "reference_name": "Cotton Control Fabric",
         "material_composition": "100% cotton", "construction": "plain weave",
         "abrasion_cycles": 25000, "shrinkage_pct": 2.5, "dwr_spray_rating": 0,
         "dwr_wash_durability": 0, "comments": "Standard cotton baseline"},
        {"reference_fabric_id": "REF-0002", "reference_name": "Polyester Control Fabric",
         "material_composition": "100% polyester", "construction": "plain weave",
         "abrasion_cycles": 35000, "shrinkage_pct": 1.2, "dwr_spray_rating": 0,
         "dwr_wash_durability": 0, "comments": "Standard polyester baseline"},
        {"reference_fabric_id": "REF-0003", "reference_name": "Recycled Nylon Reference",
         "material_composition": "100% recycled nylon", "construction": "plain weave",
         "abrasion_cycles": 28000, "shrinkage_pct": 2.0, "dwr_spray_rating": 0,
         "dwr_wash_durability": 0, "comments": "Recycled nylon typical performance"},
        {"reference_fabric_id": "REF-0004", "reference_name": "Premium DWR Cotton",
         "material_composition": "100% cotton DWR", "construction": "plain weave",
         "abrasion_cycles": 24000, "shrinkage_pct": 2.3, "dwr_spray_rating": 80,
         "dwr_wash_durability": 30, "comments": "Standard PFAS-based DWR control"},
    ]

    # DWR alternatives
    dwr_alternatives = [
        {"dwr_alternative_id": "DWR-0001", "product_name": "SilverFlex 300",
         "chemical_base": "silicone", "pfas_free": True, "spray_rating": 75.0,
         "wash_durability_cycles": 25, "cost_per_metre": 3.50,
         "availability": "available", "supplier_id": suppliers[0] if suppliers else "SUP-0001",
         "regulatory_status_uk": "approved", "regulatory_status_eu": "approved",
         "regulatory_status_us": "approved", "test_data_available": True,
         "comments": "Good performance, premium cost"},
        {"dwr_alternative_id": "DWR-0002", "product_name": "EcoWater Pro",
         "chemical_base": "polyurethane", "pfas_free": True, "spray_rating": 70.0,
         "wash_durability_cycles": 20, "cost_per_metre": 2.80,
         "availability": "available", "supplier_id": suppliers[1] if len(suppliers) > 1 else "SUP-0002",
         "regulatory_status_uk": "approved", "regulatory_status_eu": "approved",
         "regulatory_status_us": "pending", "test_data_available": True,
         "comments": "Cost-effective, adequate durability"},
        {"dwr_alternative_id": "DWR-0003", "product_name": "BioRepel Pure",
         "chemical_base": "bio-based", "pfas_free": True, "spray_rating": 65.0,
         "wash_durability_cycles": 15, "cost_per_metre": 4.20,
         "availability": "limited", "supplier_id": suppliers[2] if len(suppliers) > 2 else "SUP-0003",
         "regulatory_status_uk": "approved", "regulatory_status_eu": "approved",
         "regulatory_status_us": "approved", "test_data_available": False,
         "comments": "Sustainable but limited evidence"},
    ]

    # Standard test plans
    standard_test_plans = [
        {"plan_id": "PLN-0001", "material_type": "polyester", "purpose": "AW27 trial evaluation",
         "test_methods": "TMT-0001,TMT-0002,TMT-0003", "pass_fail_criteria": "All tests pass required minimums",
         "typical_cost_gbp": 185.0, "typical_duration_days": 14,
         "notes": "Standard protocol for polyester blends"},
        {"plan_id": "PLN-0002", "material_type": "cotton", "purpose": "Supplier qualification",
         "test_methods": "TMT-0001,TMT-0002,TMT-0004", "pass_fail_criteria": "All tests pass",
         "typical_cost_gbp": 150.0, "typical_duration_days": 12,
         "notes": "For new cotton suppliers"},
        {"plan_id": "PLN-0003", "material_type": "nylon", "purpose": "Durability assessment",
         "test_methods": "TMT-0003,TMT-0004,TMT-0008", "pass_fail_criteria": "Abrasion >25000 cycles",
         "typical_cost_gbp": 240.0, "typical_duration_days": 18,
         "notes": "For technical fabrics"},
        {"plan_id": "PLN-0004", "material_type": "blended", "purpose": "New material evaluation",
         "test_methods": "TMT-0001,TMT-0002,TMT-0003,TMT-0004,TMT-0007",
         "pass_fail_criteria": "Meet all test minimums for category",
         "typical_cost_gbp": 275.0, "typical_duration_days": 21,
         "notes": "Comprehensive protocol for blends"},
    ]

    # Generate test requests
    test_requests = []
    # Pre-generate valid IDs so we can reference them
    sample_ids_for_requests = [f"SMU-{i+1:06d}" for i in range(30)]
    lot_ids_for_requests = [f"LOT-{i+1:06d}" for i in range(40)]

    for i in range(40):
        test_req_id = f"TST-{i+1:06d}"
        test_type = r.choice(["fabric", "material", "sample", "lot", "pack"])
        target_date = as_of + timedelta(days=r.randint(5, 30))
        test_methods_list = r.sample(
            ["TMT-0001", "TMT-0002", "TMT-0003", "TMT-0004", "TMT-0005", "TMT-0006", "TMT-0007"],
            k=r.randint(1, 3)
        )

        test_requests.append({
            "test_request_id": test_req_id,
            "test_type": test_type,
            "sku": r.choice(skus) if test_type in ["pack", "product"] else None,
            "sample_id": r.choice(sample_ids_for_requests) if test_type == "sample" else None,
            "lot_id": r.choice(lot_ids_for_requests) if test_type == "lot" else None,
            "material_name": r.choice(["cotton", "polyester", "nylon", "recycled nylon", "wool", "silk"])
                            if test_type == "material" else None,
            "test_methods": ",".join(test_methods_list),
            "requested_by": r.choice(employees),
            "requested_at": as_of - timedelta(days=r.randint(1, 15)),
            "target_completion": target_date,
            "status": r.choice(["submitted", "in_progress", "completed", "cancelled"]),
            "priority": r.choice(["standard", "expedited"]) if r.random() > 0.7 else "standard",
            "notes": fake.sentence()[:100] if r.random() > 0.5 else None,
            "updated_at": as_of - timedelta(days=r.randint(0, 7))
        })

    # Generate test results
    test_results = []
    failure_modes = ["colourfastness", "brittleness", "poor adhesion", "shrinkage", "pilling",
                     "seam failure", "zip failure", "water penetration", "abrasion damage", "tear"]

    # Track valid IDs - we'll generate 30 samples, so only reference those
    sample_ids_to_use = [f"SMU-{i+1:06d}" for i in range(30)]
    lot_ids_to_use = [f"LOT-{i+1:06d}" for i in range(40)]

    for i in range(200):
        test_result_id = f"RES-{i+1:06d}"
        test_method = r.choice(test_methods)
        sku = r.choice(skus) if r.random() > 0.3 else None
        sample_id = r.choice(sample_ids_to_use) if r.random() > 0.4 else None
        lot_id = r.choice(lot_ids_to_use) if r.random() > 0.3 else None
        material_name = r.choice(["cotton", "polyester", "nylon", "recycled nylon", "wool", "silk"]) \
                       if r.random() > 0.4 else None

        # Determine pass/fail
        pass_fail = r.choices(["pass", "fail", "conditional"], [0.80, 0.15, 0.05])[0]
        failure_mode = r.choice(failure_modes) if pass_fail == "fail" else None

        # Generate appropriate test values
        if test_method["test_method_id"] == "TMT-0002":  # Shrinkage
            test_value = f"{round(r.gauss(2.5, 1.0), 1)}%"
            spec_min = "1.0"
            spec_max = "4.0"
            spec_value = "≤3.0%"
        elif test_method["test_method_id"] in ["TMT-0003", "TMT-0004"]:  # Strength tests
            test_value = str(r.randint(20000, 40000))
            spec_min = "25000"
            spec_max = "50000"
            spec_value = "≥25000 cycles"
        elif test_method["test_method_id"] in ["TMT-0007", "TMT-0008"]:  # DWR
            test_value = str(r.randint(60, 100))
            spec_min = "70"
            spec_max = "100"
            spec_value = "≥70"
        elif test_method["test_method_id"] in ["TMT-0005", "TMT-0006"]:  # Strength
            test_value = f"{round(r.gauss(50, 10), 1)} N"
            spec_min = "40"
            spec_max = "100"
            spec_value = "≥40N"
        elif test_method["test_method_id"] in ["TMT-0010", "TMT-0011", "TMT-0012"]:  # Drop/crush
            test_value = "Pass" if pass_fail == "pass" else "Fail - fracture"
            spec_min = None
            spec_max = None
            spec_value = "No damage"
        else:
            test_value = "Pass" if pass_fail == "pass" else "Fail"
            spec_min = None
            spec_max = None
            spec_value = "Pass"

        test_results.append({
            "test_result_id": test_result_id,
            "test_request_id": f"TST-{r.randint(1, 40):06d}",
            "test_method_id": test_method["test_method_id"],
            "test_method_name": test_method["name"],
            "sku": sku,
            "sample_id": sample_id,
            "lot_id": lot_id,
            "material_name": material_name,
            "test_value": test_value,
            "spec_min": spec_min,
            "spec_max": spec_max,
            "spec_value": spec_value,
            "pass_fail": pass_fail,
            "failure_mode": failure_mode,
            "test_date": as_of - timedelta(days=r.randint(1, 180)),
            "tested_by": r.choice(employees),
            "report_id": f"RPT-{r.randint(1, 50):06d}" if r.random() > 0.3 else None,
            "notes": fake.sentence()[:100] if r.random() > 0.5 else None,
            "updated_at": as_of - timedelta(days=r.randint(0, 7))
        })

    # Generate wear trials
    wear_trials = []
    for i in range(15):
        wear_trial_id = f"WTR-{i+1:06d}"
        material = r.choice(["cotton", "polyester", "nylon", "recycled nylon", "wool"])
        trial_start = as_of - timedelta(days=r.randint(60, 180))
        trial_end = trial_start + timedelta(days=r.randint(30, 90))
        perf_rating = r.choices(["excellent", "good", "adequate", "poor", "failed"],
                               [0.20, 0.35, 0.30, 0.10, 0.05])[0]
        wear_patterns = ["pilling", "abrasion", "fading", "seam stress", "water penetration", "general wear"]

        wear_trials.append({
            "wear_trial_id": wear_trial_id,
            "material_name": material,
            "finish_type": r.choice(["DWR", "enzyme wash", "no finish"]),
            "trial_start_date": trial_start,
            "trial_end_date": trial_end,
            "trial_environment": r.choice(["field wear", "accelerated lab", "controlled climate"]),
            "performance_rating": perf_rating,
            "key_findings": f"Material showed {r.choice(wear_patterns)} after {r.randint(30, 90)} days",
            "compared_to_lab_method": f"TMT-{r.randint(1, 8):04d}",
            "wear_pattern": r.choice(wear_patterns),
            "updated_at": as_of
        })

    # Generate sample submissions
    sample_submissions = []
    for i in range(30):
        sample_id = f"SMU-{i+1:06d}"
        sample_submissions.append({
            "sample_id": sample_id,
            "style_id": r.choice(styles),
            "sku": r.choice(skus),
            "supplier_id": r.choice(suppliers),
            "round_number": r.randint(1, 4),
            "submission_date": as_of - timedelta(days=r.randint(5, 120)),
            "status": r.choice(["received", "in_testing", "testing_complete", "rejected", "approved"]),
            "retest_reason": r.choice(["zip failure", "seam issue", "material quality", None]),
            "updated_at": as_of - timedelta(days=r.randint(0, 7))
        })

    # Generate retest requests
    retest_requests = []
    for i in range(10):
        retest_id = f"RET-{i+1:06d}"
        retest_requests.append({
            "retest_id": retest_id,
            "original_result_id": f"RES-{r.randint(1, 200):06d}",
            "sample_id": f"SMU-{r.randint(1, 30):06d}" if r.random() > 0.3 else None,
            "lot_id": f"LOT-{r.randint(1, 40):06d}" if r.random() > 0.3 else None,
            "reason": r.choice(["suspected false positive", "calibration error", "customer concern",
                               "improvement verification", "process change validation"]),
            "test_methods": ",".join(r.sample(["TMT-0001", "TMT-0002", "TMT-0003"], k=r.randint(1, 3))),
            "requested_at": as_of - timedelta(days=r.randint(1, 30)),
            "target_date": as_of + timedelta(days=r.randint(5, 21)),
            "status": r.choice(["submitted", "in_progress", "completed", "cancelled"]),
            "updated_at": as_of
        })

    return {
        "test_requests": test_requests,
        "test_results": test_results,
        "test_methods": test_methods,
        "wear_trials": wear_trials,
        "reference_fabrics": reference_fabrics,
        "dwr_alternatives": dwr_alternatives,
        "standard_test_plans": standard_test_plans,
        "sample_submissions": sample_submissions,
        "retest_requests": retest_requests
    }
