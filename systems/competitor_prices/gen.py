"""Competitor pricing and promotion data.

Story products (kettles, bottles, jackets, lunch boxes, athleisure, women's outerwear, wellness) are defined
once in STORY below; weekly prices AND promotions are both derived from the same spec, so they always agree.
Background products sit in unrelated categories so they never mix with a story category.
"""
from datetime import timedelta

COMPETITORS = [
    ("CMPD-001", "HomeShop Direct", "online", "GB", "UK", "web_scrape", "2026-10-05 14:00"),
    ("CMPD-002", "John Lewis", "high_street", "GB", "UK", "manual", "2026-10-05 09:00"),
    ("CMPD-003", "Carrefour", "hypermarket", "FR", "EU Central", "agency", "2026-10-04 16:30"),
    ("CMPD-004", "Currys", "electronics", "GB", "UK", "web_scrape", "2026-10-05 12:00"),
    ("CMPD-005", "Argos", "online", "GB", "UK", "manual", "2026-10-05 10:15"),
    ("CMPD-006", "JD Sports", "high_street", "GB", "UK", "web_scrape", "2026-10-05 11:30"),
]

# Master SKUs the competitor products are matched to (the style is resolved in SQL, so any size/colour works).
K1700 = "K-1700"            # 1.7L Glass Kettle, 77.99
TOASTER = "SKU-101309"      # Small Appliances style STY-4789, 79.99
COFFEE = "SKU-100532"       # Small Appliances style STY-4301, 99.99
COFFEE_PRO = "SKU-104732"   # Small Appliances style STY-8598, 334.99 (priced well above its category)
BOTTLE = "SKU-106307"       # Drinkware style STY-9501, 15.99 (our new 750ml insulated bottle)
JACKET = "SKU-100161"       # Menswear Outerwear style STY-4102, 66.99 (the jacket on 30% markdown)
LUNCH = "SKU-106314"     # Kitchenware style STY-9502, 13.99 (our new insulated lunch box)
WOOL_COAT = "SKU-106321"    # Womenswear Outerwear style STY-9503, 128.99 (our new wool coat)
ATH_TOP = "SKU-100070"      # Womenswear Tops style STY-4056 (athleisure), 63.99

# Promotion tuple: (first_week_ago, last_week_ago, type, pct, description); last_week_ago 0 = still running.
# Product tuple keys: comp, code, sku, cat, sub, dept, name, brand, feat, list, plus optional
# promos, chg=(week_ago, new_list_price), dq, colour, material, sil, status, launch (weeks ago), last_k (last observed week).
S = []


def add(comp, code, sku, cat, sub, dept, name, brand, feat, lst, **kw):
    S.append(dict(comp=comp, code=code, sku=sku, cat=cat, sub=sub, dept=dept, name=name, brand=brand, feat=feat,
                  list=lst, **kw))


# ---- Small appliances ----
SA = ("Small appliances", "Electricals")
add(1, "K01", K1700, *SA[:1], "Kettles", SA[1], "1.7L Glass Electric Kettle", "HomeShop Value", "Fast boil 3000W; cordless; glass body with blue light", 69.99,
    promos=[(1, 0, "percentage", 15, "Black Friday Early Bird - 15% off kettles")])
add(2, "K01", K1700, SA[0], "Kettles", SA[1], "John Lewis Glass Kettle 1.7L", "John Lewis", "Premium borosilicate glass; temperature presets", 89.99)
add(3, "K01", K1700, SA[0], "Kettles", SA[1], "Bouilloire verre 1.7L", "Carrefour Brand", "Durable glass and plastic; auto shut-off", 59.99, dq="estimated")
add(4, "K01", K1700, SA[0], "Kettles", SA[1], "Currys Pro Glass Kettle 1.7L", "Currys Own", "Digital temperature control; keep-warm", 74.99)
add(5, "K01", K1700, SA[0], "Kettles", SA[1], "Argos 1.7L Glass Kettle", "Argos Brand", "Lightweight cordless; illuminated glass", 64.99,
    promos=[(4, 3, "percentage", 20, "Super Savings Week")])
add(2, "T01", TOASTER, SA[0], "Toasters", SA[1], "John Lewis 4-Slice Toaster", "John Lewis", "Wide slots; browning control", 69.99)
add(4, "T01", TOASTER, SA[0], "Toasters", SA[1], "Currys Essentials 4-Slice Toaster", "Currys Own", "Defrost and reheat", 44.99)
add(5, "T01", TOASTER, SA[0], "Toasters", SA[1], "Argos 4-Slice Toaster", "Argos Brand", "Variable browning", 39.99)
add(1, "T01", TOASTER, SA[0], "Toasters", SA[1], "HomeShop 4-Slice Toaster", "HomeShop Value", "Stainless steel; crumb tray", 49.99)
add(2, "C01", COFFEE, SA[0], "Coffee machines", SA[1], "John Lewis Bean-to-Cup Coffee Machine", "John Lewis", "Built-in grinder; milk frother", 109.00)
add(4, "C01", COFFEE, SA[0], "Coffee machines", SA[1], "Currys Pod Coffee Machine", "Currys Own", "Compatible with major pod brands", 89.99)
add(5, "C01", COFFEE, SA[0], "Coffee machines", SA[1], "Argos Filter Coffee Machine", "Argos Brand", "12-cup glass jug; keep-warm plate", 79.99)
add(3, "C01", COFFEE, SA[0], "Coffee machines", SA[1], "Machine a cafe expresso", "Carrefour Brand", "15 bar pump; steam wand", 94.99, dq="estimated")
# premium bean-to-cup machine: our SKU-104732 at 334.99 is the small appliance priced furthest above market (pricing flags it too)
add(2, "C02", COFFEE_PRO, SA[0], "Coffee machines", SA[1], "John Lewis Pro Espresso Machine", "John Lewis", "15 bar pump; steam wand; built-in grinder", 189.00)
add(4, "C02", COFFEE_PRO, SA[0], "Coffee machines", SA[1], "Currys Smart Bean-to-Cup Machine", "Currys Own", "App control; milk system", 199.99)
add(5, "C02", COFFEE_PRO, SA[0], "Coffee machines", SA[1], "Argos Espresso Machine", "Argos Brand", "Manual frother; 19 bar", 149.99)
add(1, "C02", COFFEE_PRO, SA[0], "Coffee machines", SA[1], "HomeShop Barista Machine", "HomeShop Premium", "Built-in grinder; touch screen", 169.99)
add(4, "A01", None, SA[0], "Air fryers", SA[1], "Currys Air Fryer 4L", "Currys Own", "Digital display; 8 presets", 69.99)
add(5, "A01", None, SA[0], "Air fryers", SA[1], "Argos 4.5L Air Fryer", "Argos Brand", "Rapid air technology", 59.99)
add(1, "A01", None, SA[0], "Air fryers", SA[1], "HomeShop Dual Air Fryer 7L", "HomeShop Premium", "Two independent baskets", 89.99)
add(2, "A01", None, SA[0], "Air fryers", SA[1], "John Lewis Air Fryer 5L", "John Lewis", "Window; dishwasher-safe basket", 99.00)
add(3, "A01", None, SA[0], "Air fryers", SA[1], "Friteuse sans huile 4L", "Carrefour Brand", "Timer and auto-off", 54.99, dq="estimated")
add(2, "BL1", None, SA[0], "Blenders", SA[1], "John Lewis Jug Blender 1.5L", "John Lewis", "1000W motor; glass jug", 79.00)
add(4, "BL1", None, SA[0], "Blenders", SA[1], "Currys Blender 1.5L", "Currys Own", "Ice crushing", 39.99)
add(5, "BL1", None, SA[0], "Blenders", SA[1], "Argos Smoothie Blender", "Argos Brand", "Two travel cups", 29.99)
# multi cookers, countertop ovens and sandwich/waffle makers: the other segments of the small kitchen appliance whitespace (as in range_planning)
add(4, "MC1", None, SA[0], "Multi cookers", SA[1], "Currys 6L Multi Cooker", "Currys Own", "14 programmes; pressure and slow cook", 89.99)
add(5, "MC1", None, SA[0], "Multi cookers", SA[1], "Argos 5L Pressure Multi Cooker", "Argos Brand", "Pressure cook, steam, saute", 79.99)
add(2, "MC1", None, SA[0], "Multi cookers", SA[1], "John Lewis 6L Multi Cooker", "John Lewis", "Ceramic pot; app recipes", 119.00)
add(1, "MC1", None, SA[0], "Multi cookers", SA[1], "HomeShop 8-in-1 Multi Cooker", "HomeShop Value", "Eight functions; delay start", 69.99)
add(4, "CO1", None, SA[0], "Countertop ovens", SA[1], "Currys 20L Mini Oven", "Currys Own", "Double glass door; convection", 79.99)
add(5, "CO1", None, SA[0], "Countertop ovens", SA[1], "Argos 22L Mini Oven", "Argos Brand", "Two racks; timer", 69.99)
add(2, "CO1", None, SA[0], "Countertop ovens", SA[1], "John Lewis 30L Mini Oven", "John Lewis", "Rotisserie; convection", 129.00)
add(1, "CO1", None, SA[0], "Countertop ovens", SA[1], "HomeShop 25L Mini Oven", "HomeShop Value", "Compact; four heat settings", 74.99)
add(3, "CO1", None, SA[0], "Countertop ovens", SA[1], "Mini four 20L", "Carrefour Brand", "Chaleur tournante", 64.99, dq="estimated")
add(5, "SW1", None, SA[0], "Sandwich and waffle makers", SA[1], "Argos 2-Slice Sandwich Toaster", "Argos Brand", "Non-stick plates", 19.99)
add(1, "SW1", None, SA[0], "Sandwich and waffle makers", SA[1], "HomeShop Waffle Maker", "HomeShop Value", "Belgian waffles; non-stick", 24.99)
add(5, "S01", None, SA[0], "Soup makers", SA[1], "Argos 1.6L Soup Maker", "Argos Brand", "Heats and blends; 4 programmes", 49.99)
add(4, "V01", None, SA[0], "Sous vide cookers", SA[1], "Currys Sous Vide Stick", "Currys Own", "App control; 1100W", 79.99)

# ---- Insulated bottles (750ml): our new SKU-106307 at 15.99 ----
IB = "Insulated bottles"
add(1, "BT1", BOTTLE, IB, "750ml bottles", "Home", "Premium Insulated Bottle 750ml", "HomeShop Premium", "Keeps cold 24 hours, hot 12; double-wall stainless steel", 12.99, chg=(7, 13.99))
add(2, "BT1", BOTTLE, IB, "750ml bottles", "Home", "John Lewis Insulated Travel Bottle 750ml", "John Lewis", "Stainless steel double wall; leakproof lid", 17.95,
    promos=[(4, 3, "percentage", 10, "Back to School Special")])
add(3, "BT1", BOTTLE, IB, "750ml bottles", "Home", "Bouteille isotherme 750 ml", "Carrefour", "Durable design; vacuum insulated", 12.99, dq="estimated")
add(5, "BT1", BOTTLE, IB, "750ml bottles", "Home", "Argos Premium Insulated Bottle 750ml", "Argos Brand", "Sleek design keeps drinks hot or cold", 14.99,
    promos=[(2, 0, "clearance", 30, "Summer Clearance Event")])
add(6, "BT1", BOTTLE, IB, "750ml bottles", "Home", "JD Insulated Steel Bottle 750ml", "JD Sports", "Gym-friendly sports cap; vacuum insulated", 10.99, dq="partial")

# ---- Men's jackets: our STY-4102 at 66.99, on 30% markdown since early September ----
MJ = "Men's jackets"
add(1, "J01", JACKET, MJ, "Padded jackets", "Menswear", "Men's Winter Jacket Premium", "HomeShop Premium", "Water-resistant with hood; padded", 70.00,
    promos=[(1, 0, "percentage", 30, "Winter Collection 30% Off")])
add(2, "J01", JACKET, MJ, "Padded jackets", "Menswear", "John Lewis Men's Padded Jacket", "John Lewis", "Quilted; recycled fill", 85.00)
add(3, "J01", JACKET, MJ, "Padded jackets", "Menswear", "Veste Homme Premium", "Carrefour", "Winter ready design", 54.99, dq="estimated",
    promos=[(0, 0, "percentage", 15, "October Sale")])
add(5, "J01", JACKET, MJ, "Padded jackets", "Menswear", "Argos Men's Winter Jacket", "Argos Brand", "Classic style padded jacket", 65.00,
    promos=[(5, 0, "clearance", 50, "Total Clearance - Up to 50% Off Jackets")])
add(6, "J01", JACKET, MJ, "Padded jackets", "Menswear", "JD Men's Padded Jacket", "JD Sports", "Lightweight padded sports jacket", 75.00,
    promos=[(2, 0, "clearance", 40, "Winter Clearance 40% Off")])

# ---- Athleisure: our new STY-4056 tops at 63.99 ----
AT = "Athleisure"
add(6, "AT1", ATH_TOP, AT, "Tops", "Womenswear", "JD Seamless Gym Top", "JD Sports", "Seamless; moisture-wicking", 34.00,
    promos=[(3, 0, "percentage", 25, "Autumn Active 25% Off")])
add(6, "AT2", None, AT, "Leggings", "Womenswear", "JD High-Waist Leggings", "JD Sports", "High waist; squat-proof", 38.00,
    promos=[(3, 0, "percentage", 25, "Autumn Active 25% Off")])
add(6, "AT3", None, AT, "Hoodies", "Womenswear", "JD Zip Hoodie", "JD Sports", "Brushed fleece; zip pockets", 45.00)
add(2, "AT1", ATH_TOP, AT, "Tops", "Womenswear", "John Lewis Studio Seamless Top", "John Lewis", "Recycled yarn; seamless", 45.00)
add(2, "AT2", None, AT, "Leggings", "Womenswear", "John Lewis Studio Leggings", "John Lewis", "Four-way stretch", 55.00)
add(2, "AT3", None, AT, "Hoodies", "Womenswear", "John Lewis Studio Zip Hoodie", "John Lewis", "Organic cotton blend", 69.00)
add(5, "AT1", ATH_TOP, AT, "Tops", "Womenswear", "Argos Active Training Top", "Argos Brand", "Quick-dry fabric", 22.00,
    promos=[(2, 0, "percentage", 20, "Active Wear Event")])
add(5, "AT2", None, AT, "Leggings", "Womenswear", "Argos Active Leggings", "Argos Brand", "Elastic waistband", 25.00)
add(1, "AT1", ATH_TOP, AT, "Tops", "Womenswear", "HomeShop Performance Top", "HomeShop Value", "Breathable mesh panels", 29.99,
    promos=[(1, 0, "percentage", 20, "Autumn Active")])
add(1, "AT2", None, AT, "Leggings", "Womenswear", "HomeShop Performance Leggings", "HomeShop Value", "Pocketed; high waist", 32.00)

# ---- Insulated lunch boxes ----
LB = "Lunch boxes"
add(1, "L01", LUNCH, LB, "Insulated lunch boxes", "Home", "HomeShop Insulated Lunch Bag 5L", "HomeShop Value", "Compact portable design; foil lined; zip closure", 14.99)
add(2, "L01", LUNCH, LB, "Insulated lunch boxes", "Home", "John Lewis Premium Insulated Lunch Box", "John Lewis", "Leakproof compartments; stainless steel inner; BPA-free", 34.00)
add(3, "L01", LUNCH, LB, "Insulated lunch boxes", "Home", "Boite isotherme dejeuner", "Carrefour", "Lightweight and durable; single compartment", 11.99, dq="estimated")
add(5, "L01", LUNCH, LB, "Insulated lunch boxes", "Home", "Argos Thermal Lunch Box", "Argos Brand", "Space-saving design; two compartments; cutlery included", 16.50,
    promos=[(2, 0, "percentage", 20, "Back to School Lunch Deal")])
add(6, "L01", LUNCH, LB, "Insulated lunch boxes", "Home", "JD Gym Meal Prep Insulated Bag", "JD Sports", "Multiple containers; ice pack included; shoulder strap", 24.99)

# ---- Women's outerwear (AW27 trend: oversized silhouettes, recycled materials) ----
WO = "Women's outerwear"
add(2, "W01", WOOL_COAT, WO, "Coats", "Womenswear", "John Lewis Oversized Wool-Blend Coat", "John Lewis", "Dropped shoulder; wool-blend; double breasted", 159.00,
    colour="Chocolate brown", material="Recycled wool", sil="Oversized", launch=3)
add(2, "W02", None, WO, "Coats", "Womenswear", "John Lewis Belted Trench Coat", "John Lewis", "Classic belted trench", 125.00,
    colour="Camel", material="Cotton gabardine", sil="Tailored", launch=40)
add(1, "W01", None, WO, "Jackets", "Womenswear", "HomeShop Oversized Fleece Jacket", "HomeShop Premium", "Teddy fleece; roomy fit", 49.99,
    colour="Sage green", material="Recycled polyester", sil="Oversized", launch=5)
add(1, "W02", None, WO, "Jackets", "Womenswear", "HomeShop Boxy Quilted Jacket", "HomeShop Premium", "Quilted; boxy cut", 59.99,
    colour="Black", material="Recycled polyester", sil="Boxy", launch=20)
add(6, "W01", None, WO, "Jackets", "Womenswear", "JD Oversized Puffer Jacket", "JD Sports", "Glossy finish; padded; oversized hood", 89.99,
    colour="Black", material="Recycled nylon", sil="Oversized", launch=4)
add(6, "W02", None, WO, "Jackets", "Womenswear", "JD Cropped Shell Jacket", "JD Sports", "Lightweight; cropped length", 54.99,
    colour="Sand", material="Nylon", sil="Cropped", launch=30)
add(5, "W01", None, WO, "Coats", "Womenswear", "Argos Padded Longline Coat", "Argos Brand", "Longline padded coat", 79.99,
    colour="Black", material="Polyester", sil="Longline", launch=25)
add(3, "W01", WOOL_COAT, WO, "Coats", "Womenswear", "Manteau femme laine", "Carrefour", "Straight cut wool coat", 74.99, dq="estimated",
    colour="Navy", material="Wool", sil="Straight", launch=26)

# ---- Wellness and recovery ----
WR = "Wellness & recovery"
add(6, "R01", None, WR, "Massage guns", "Home", "JD Percussion Massage Gun", "JD Sports", "6 speeds; 5 attachments", 89.99, status="bestseller", launch=30)
add(6, "R02", None, WR, "Foam rollers", "Home", "JD Vibrating Foam Roller", "JD Sports", "Three vibration levels", 34.99, status="active", launch=26)
add(6, "R03", None, WR, "Compression boots", "Home", "JD Compression Recovery Boots", "JD Sports", "Air compression for legs", 199.99, status="discontinued", launch=48,
    promos=[(11, 8, "clearance", 60, "Final Clearance")], last_k=8)
add(2, "R01", None, WR, "Weighted blankets", "Home", "John Lewis Weighted Blanket 6kg", "John Lewis", "Glass bead fill; cotton cover", 79.00, status="bestseller", launch=40)
add(2, "R02", None, WR, "Aroma diffusers", "Home", "John Lewis Ultrasonic Aroma Diffuser", "John Lewis", "Colour-changing light; timer", 35.00, status="bestseller", launch=36)
add(2, "R03", None, WR, "Bath soaks", "Home", "John Lewis Magnesium Bath Soak Set", "John Lewis", "Magnesium flakes; three scents", 18.00, status="active", launch=15)
add(1, "R01", None, WR, "Cold plunge tubs", "Home", "HomeShop Cold Plunge Tub 100L", "HomeShop Premium", "Inflatable ice bath with lid", 199.99, status="discontinued", launch=22,
    promos=[(9, 6, "clearance", 50, "Cold Plunge Clearance")], last_k=6)
add(4, "R01", None, WR, "Sauna blankets", "Home", "Currys Infrared Sauna Blanket", "Currys Own", "Infrared heating; 3 heat settings", 249.99, status="discontinued", launch=24,
    promos=[(10, 7, "clearance", 40, "Clearance")], last_k=7)
add(5, "R01", None, WR, "Foam rollers", "Home", "Argos Foam Roller 33cm", "Argos Brand", "High density EVA foam", 12.99, status="active", launch=50)
add(5, "R02", None, WR, "Massage guns", "Home", "Argos Mini Massage Gun", "Argos Brand", "Pocket size; 3 speeds", 49.99, status="active", launch=12)

# ---- Home & kitchen, matched to our Home SKUs (price-gap story): pans overpriced, storage overpriced, bedding cheap ----
PP = "Pots and pans"
# Cookware sets matched to the two lines pricing flags: SKU-103612 Ivory Cookware (132.99, about 14% above the market average)
# and SKU-100819 Ochre Cookware (114.99, about 12% above), the same gaps the pricing system works from.
add(5, "P01", "SKU-103612", PP, "Cookware sets", "Home", "Argos Home Stainless Steel Cookware Set 8pc", "Argos Brand", "Eight piece induction-ready set", 110.00)
add(1, "P01", "SKU-103612", PP, "Cookware sets", "Home", "HomeShop Ceramic Cookware Set 8pc", "HomeShop Value", "Ceramic coating; stay-cool handles", 117.00)
add(2, "P01", "SKU-103612", PP, "Cookware sets", "Home", "John Lewis Essentials Cookware Set 8pc", "John Lewis", "Aluminium; PFOA-free coating", 122.95)
add(5, "P02", "SKU-100819", PP, "Cookware sets", "Home", "Argos Home Hard Anodised Cookware Set", "Argos Brand", "Hard anodised; five pieces", 96.99)
add(1, "P02", "SKU-100819", PP, "Cookware sets", "Home", "HomeShop Cast Aluminium Cookware Set", "HomeShop Value", "Cast aluminium; glass lids", 104.99)
add(2, "P02", "SKU-100819", PP, "Cookware sets", "Home", "John Lewis Cook Cookware Set 5pc", "John Lewis", "Tri-ply base; oven safe", 106.03)
ST = "Storage boxes"
add(5, "ST1", "SKU-104564", ST, "Storage boxes", "Home", "Argos Home Stackable Storage Set", "Argos Brand", "Set of 3 stackable boxes with lids", 36.99)
add(2, "ST1", "SKU-104564", ST, "Storage boxes", "Home", "John Lewis Stackable Storage Boxes", "John Lewis", "Set of 3; recycled plastic", 41.99)
add(1, "ST1", "SKU-104564", ST, "Storage boxes", "Home", "HomeShop Lidded Storage Set", "HomeShop Value", "Set of 4 lidded boxes", 34.99)
# ---- New storage launch (SKU-100595 Sage Storage, 23.99): food storage benchmark; not matched to a SKU so it stays out of the gap report ----
FS = "Food storage"
add(5, "FS1", None, FS, "Storage containers", "Home", "Argos Home 10pc Plastic Food Storage Set", "Argos Brand", "Ten piece set; clip lids; microwave safe", 19.99)
add(1, "FS1", None, FS, "Storage containers", "Home", "HomeShop Stackable Food Storage Tubs", "HomeShop Value", "Six stackable tubs with lids", 21.99)
add(2, "FS1", None, FS, "Storage containers", "Home", "John Lewis Glass Food Storage Set", "John Lewis", "Borosilicate glass; airtight lids", 27.99)
add(3, "FS1", None, FS, "Storage containers", "Home", "Boites de conservation 6 pieces", "Carrefour Brand", "Six piece set; BPA-free", 17.99, dq="estimated")
BD = "Bed linen"
add(2, "BD1", "SKU-105866", BD, "Duvet sets", "Home", "John Lewis Cotton Duvet Set Double", "John Lewis", "Percale cotton; 200 thread count", 46.00)
add(5, "BD1", "SKU-105866", BD, "Duvet sets", "Home", "Argos Home Cotton Duvet Set Double", "Argos Brand", "Easy care poly-cotton", 39.99)
add(1, "BD1", "SKU-105866", BD, "Duvet sets", "Home", "HomeShop Soft Touch Duvet Set Double", "HomeShop Value", "Brushed microfibre", 41.99)

# ---- Our top sellers by revenue over the last 90 days (the same lines the e-commerce system ranks first) ----
# SKU-104032 / SKU-104025 (style STY-8220, 231.99), SKU-105075 (STY-8766 shirt, 175.99), SKU-102261 (STY-5713 audio, 165.99), SKU-100630 (STY-4345 audio, 187.99)
FP = "Food preparation"
add(4, "M01", "SKU-104032", FP, "Stand mixers", "Electricals", "Currys Pro 5L Stand Mixer", "Currys Own", "1000W; 5L bowl; three attachments", 249.99)
add(5, "M01", "SKU-104032", FP, "Stand mixers", "Electricals", "Argos 4.8L Stand Mixer", "Argos Brand", "800W; tilt-head; splash guard", 199.99)
add(2, "M01", "SKU-104032", FP, "Stand mixers", "Electricals", "John Lewis 5L Stand Mixer", "John Lewis", "1200W; planetary mixing; 10 speeds", 279.00)
add(1, "M01", "SKU-104032", FP, "Stand mixers", "Electricals", "HomeShop Tilt-head Stand Mixer 5L", "HomeShop Premium", "1000W; dough hook and whisk", 214.99,
    promos=[(2, 0, "percentage", 10, "Weekend Offer - 10% off kitchen machines")])
HP = "Headphones"
add(4, "H01", "SKU-102261", HP, "Wireless headphones", "Electricals", "Currys Pro Wireless Headphones", "Currys Own", "Active noise cancelling; 30 hour battery", 149.99)
add(5, "H01", "SKU-102261", HP, "Wireless headphones", "Electricals", "Argos Wireless Over-ear Headphones", "Argos Brand", "Bluetooth 5; 25 hour battery", 129.99)
add(2, "H01", "SKU-102261", HP, "Wireless headphones", "Electricals", "John Lewis Studio Wireless Headphones", "John Lewis", "Noise cancelling; multipoint", 179.00)
add(1, "H01", "SKU-102261", HP, "Wireless headphones", "Electricals", "HomeShop Wireless Headphones", "HomeShop Value", "Bluetooth; foldable", 139.99)
SB = "Soundbars"
add(4, "SB1", "SKU-100630", SB, "Soundbars", "Electricals", "Currys Pro 3.1 Soundbar", "Currys Own", "Wireless sub; Dolby Atmos", 169.99)
add(5, "SB1", "SKU-100630", SB, "Soundbars", "Electricals", "Argos 2.1 Soundbar with Subwoofer", "Argos Brand", "Bluetooth; HDMI ARC", 159.99)
add(2, "SB1", "SKU-100630", SB, "Soundbars", "Electricals", "John Lewis 3.1 Soundbar", "John Lewis", "Dolby Atmos; app control", 199.00)
add(3, "SB1", "SKU-100630", SB, "Soundbars", "Electricals", "Barre de son 2.1", "Carrefour Brand", "Bluetooth; remote", 149.99, dq="estimated")
MS = "Men's shirts"
add(2, "SH1", "SKU-105075", MS, "Formal shirts", "Menswear", "John Lewis Premium Oxford Shirt", "John Lewis", "Cotton oxford; button-down collar", 139.00)
add(1, "SH1", "SKU-105075", MS, "Formal shirts", "Menswear", "HomeShop Easy Iron Shirt", "HomeShop Value", "Easy iron cotton blend", 104.99)
add(5, "SH1", "SKU-105075", MS, "Formal shirts", "Menswear", "Argos Collection Cotton Shirt", "Argos Brand", "Regular fit; non-iron", 94.99)
add(6, "SH1", "SKU-105075", MS, "Formal shirts", "Menswear", "JD Smart Shirt", "JD Sports", "Slim fit; stretch cotton", 124.99)

# ---- Sage green in home ranges (colour trend for next year's home range) ----
HT = "Home textiles"
add(2, "HT1", None, HT, "Duvet sets", "Home", "John Lewis Washed Linen Duvet Set King", "John Lewis", "Stonewashed linen; breathable", 149.00,
    colour="Sage green", material="Washed linen", launch=10)
add(5, "HT1", None, HT, "Duvet sets", "Home", "Argos Home Sage Cotton Duvet Set King", "Argos Brand", "Soft cotton; reversible", 34.00,
    colour="Sage green", material="Cotton", launch=8)
add(1, "HT2", None, HT, "Towels", "Home", "HomeShop Sage Bath Towel Bundle", "HomeShop Value", "Six piece cotton towel bundle", 42.00,
    colour="Sage green", material="Cotton", launch=6)
add(2, "HT3", None, HT, "Throws", "Home", "John Lewis Chunky Knit Throw", "John Lewis", "Chunky knit; recycled yarn", 79.00,
    colour="Terracotta", material="Recycled cotton", launch=12)
add(5, "HT3", None, HT, "Throws", "Home", "Argos Home Faux Fur Throw", "Argos Brand", "Soft faux fur", 24.99,
    colour="Cream", material="Polyester", launch=30)
add(1, "HT4", None, HT, "Cushions", "Home", "HomeShop Velvet Cushion Pair", "HomeShop Value", "Velvet; feather-effect pads", 29.00,
    colour="Chocolate brown", material="Velvet", launch=14)

BACKGROUND = {
    "Cookware": ("Home", ["Non-stick Frying Pan 28cm", "Cast Iron Casserole 24cm", "Stainless Steel Saucepan Set"], (20, 110)),
    "Bedding": ("Home", ["Cotton Duvet Cover Set King", "Memory Foam Pillow", "Microfibre Duvet 10.5 tog"], (18, 90)),
    "Towels": ("Home", ["Egyptian Cotton Bath Towel", "Hand Towel Pack of 4", "Bath Sheet"], (8, 45)),
    "Lighting": ("Home", ["LED Floor Lamp", "Table Lamp with Shade", "Smart Bulb Pack of 3"], (12, 80)),
}


def generate(g):
    r = g.rng
    base = len(S)
    from_weeks = lambda k: g.as_of - timedelta(days=7 * k)  # noqa: E731

    competitors = [{"competitor_id": c[0], "name": c[1], "format": c[2], "country": c[3], "region": c[4],
                    "data_source": c[5], "last_updated": c[6], "coverage_status": "active"} for c in COMPETITORS]

    # random background products (no story category, no matched SKU)
    for cat, (dept, names, (lo, hi)) in BACKGROUND.items():
        for n in names:
            for comp in r.sample([1, 2, 3, 4, 5, 6], 3):
                promos = []
                if r.random() < 0.0:  # no random background promotions: keeps period tools free of unrelated noise
                    k0 = r.randint(2, 11)
                    promos = [(k0, max(0, k0 - r.randint(1, 3)), r.choice(["percentage", "clearance"]), r.choice([10, 20, 30, 40]), "Seasonal offer")]
                add(comp, "N%02d" % len(S), None, cat, cat, dept, n, "Own brand", "Everyday range", round(r.uniform(lo, hi), 2), promos=promos)

    products, prices, promotions = [], [], []
    story_promo_n = bg_promo_n = 0
    for sp in S:
        cid = f"CMPD-{sp['comp']:03d}"
        pid = f"{cid}-{sp['code']}"
        sku = sp["sku"]
        products.append({
            "competitor_product_id": pid, "competitor_id": cid, "sku": sku, "their_sku": f"{cid[-3:]}-{sp['code']}",
            "their_name": sp["name"], "category": sp["cat"], "subcategory": sp["sub"], "department": sp["dept"],
            "brand": sp["brand"], "features": sp["feat"], "colour": sp.get("colour", ""), "material": sp.get("material", ""),
            "silhouette": sp.get("sil", ""), "status": sp.get("status", "active"),
            "launch_date": from_weeks(sp.get("launch", 52)), "matched_product": bool(sku),
        })
        last_k = sp.get("last_k", 0)
        promos = sp.get("promos", [])
        for k in range(12, last_k - 1, -1):
            lst = sp["list"]
            if sp.get("chg") and k < sp["chg"][0]:
                lst = sp["chg"][1]
            ptype, pct, desc, clear = "none", 0.0, "", False
            for (k0, k1, t, p, d) in promos:
                if k1 <= k <= k0:
                    ptype, pct, desc, clear = t, float(p), d, t == "clearance"
            prices.append({
                "competitor_product_id": pid, "competitor_id": cid, "sku": sku, "price_date": from_weeks(k),
                "price_gbp": round(lst * (1 - pct / 100), 2), "list_price_gbp": lst, "promotion_type": ptype,
                "discount_pct": pct, "promotion_desc": desc, "in_clearance": clear, "data_quality": sp.get("dq", "confirmed"),
            })
        story = sp["cat"] not in BACKGROUND
        for (k0, k1, t, p, d) in promos:
            ongoing = k1 == 0
            start = from_weeks(k0)
            end = g.as_of + timedelta(days=14) if ongoing else from_weeks(k1) + timedelta(days=6)
            if story:
                story_promo_n += 1
                pr_id = f"PRMO-9{story_promo_n:05d}"
            else:
                bg_promo_n += 1
                pr_id = f"PRMO-{bg_promo_n:06d}"
            promotions.append({
                "promotion_id": pr_id, "competitor_id": cid, "competitor_product_id": pid, "sku": sku,
                "promo_start": start, "promo_end": end, "promo_type": t, "discount_pct": float(p), "discount_gbp": 0,
                "promo_description": d, "duration_days": (end - start).days + 1, "status": "active" if ongoing else "completed",
            })

    # Competitor stores (UK stores only; seed holds the Store 214 story)
    competitor_stores = []
    stores_per = {"CMPD-001": 0, "CMPD-002": 8, "CMPD-003": 0, "CMPD-004": 12, "CMPD-005": 15, "CMPD-006": 6}
    locs = ["ST001", "ST002", "ST003", "ST004", "ST005", "ST010", "ST050", "ST100", "ST150", "ST200", "ST210", "ST212", "ST215", "ST220"]
    fmt = {c[0]: c[2] for c in COMPETITORS}
    n = 0
    for cid, cnt in stores_per.items():
        for i in range(cnt):
            n += 1
            opening = g.as_of - timedelta(days=r.randint(30, 1000))
            closed, status = None, "open"
            if r.random() < 0.1:
                closed, status = g.as_of - timedelta(days=r.randint(1, 100)), "closed"
            competitor_stores.append({
                "store_id": f"CSTD-{cid[-3:]}-{n:04d}", "competitor_id": cid, "site_id": locs[i % len(locs)],
                "opening_date": opening, "closing_date": closed, "status": status, "store_format": fmt[cid],
            })

    del S[base:]  # background products are rebuilt on every call

    # returns policies and delivery practices come from seed/ (small hand-written reference tables)
    return {
        "competitors": competitors,
        "competitor_products": products,
        "competitor_prices": prices,
        "competitor_promotions": promotions,
        "competitor_stores": competitor_stores,
        "competitor_returns_policies": [],
        "competitor_delivery_practices": [],
    }
