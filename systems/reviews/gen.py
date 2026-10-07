"""Customer reviews, ratings and feedback themes for own products, stores and competitor products.

Background: every launched style gets a modest number of reviews on one primary SKU (stable ratings, no planted trend),
so planted stories stand out. Stories (all dated relative to as_of, weekly grain):
  K-1700            ratings fall for eight weeks; lid-seal leaks dominate the complaints (quality, not perception)
  SKU-100301        sole separation complaints climb over the last three months (shoe, sole batches from July)
  SKU-100637        best-selling jeans: waistband gapes at the back; comfort is what customers praise
  STY-4056          athleisure tops: product rated well, complaints are about size 14 availability
  SKU-100014 / PF-220 / SKU-100007   range-review outliers; packaging complaints (torn polybag, crushed carton)
  SKU-106307        new 750ml insulated bottle (STY-9501): early-access customers rave about insulation and leakproof lid
  Outerwear         25-34s want light, packable, pocketed, sustainable jackets (UK) / warm, sustainable (DE);
                    PT/TR outerwear suppliers have distinct customer ratings
  competitors       lunch boxes (leaking is the top complaint) and wellness (cold plunge, compression boots,
                    sauna blanket flopped) with review text
"""
import random
from datetime import datetime, timedelta

APPAREL = {
    "sizing": (["Perfect fit, true to size", "Great sizing, exactly as described", "Sized just right, no need to swap"],
               ["Runs small, recommend ordering a size up", "Much larger than expected, had to return",
                "Sizing is all over the place, had to send it back"]),
    "fit": (["Flattering cut, perfect silhouette", "Hugs the body nicely without restricting movement",
             "Just right for active wear"],
            ["Too loose around the middle", "Awkward fit, doesn't work with my body shape", "Boxy and unflattering"]),
    "quality": (["Excellent quality, will last years", "Superior craftsmanship throughout", "Good quality for the price"],
                ["Seams started coming apart after a month", "Quality issues - zip broke immediately",
                 "Stitching came loose after a few washes"]),
    "durability": (["Used daily for 3 months, still holding up well", "Incredibly durable, worth the investment",
                    "Proven design that lasts"],
                   ["Started falling apart after light use", "Fabric wore thin after a few weeks",
                    "Did not survive the first season"]),
    "comfort": (["So comfortable I want to wear it all day", "Soft and breathable", "Perfect comfort for extended wear"],
                ["Scratchy material, irritates skin", "Too stiff, needs breaking in", "Uncomfortable after an hour"]),
    "value": (["Excellent value, better than competitors", "Worth every penny", "Fair price for the quality"],
              ["Overpriced for what you get", "Could find similar for much less elsewhere", "Not worth the money"]),
    "colour": (["Colour is exactly as shown online", "Vibrant and long-lasting colour", "Beautiful shade, matches description"],
               ["Much darker in person than the pictures", "Colour faded after first wash", "Colour is nothing like the photos"]),
    "packaging": (["Arrived in perfect condition", "Nice presentation in packaging", "Protected well during shipping"],
                  ["Packaging was torn, item slightly damaged", "Arrived squashed and creased",
                   "Bag split open in the post"]),
}
HARD = {
    "quality": (["Solid build quality", "Feels well made", "Great quality for the price"],
                ["Feels flimsy and cheap", "Stopped working after a month", "Arrived faulty"]),
    "durability": (["Still going strong after six months", "Has survived daily use"],
                   ["Started to fall apart after light use", "Cracked within weeks"]),
    "performance": (["Works brilliantly", "Does exactly what it says"],
                    ["Does not perform as advertised", "Underpowered, disappointing"]),
    "design": (["Looks great and compact", "Lovely design"], ["Awkward design", "Looks cheaper in person"]),
    "value": (["Excellent value", "Worth every penny"], ["Overpriced for what you get", "Cheaper alternatives are just as good"]),
    "ease_of_use": (["Easy to use straight out of the box", "Simple controls"],
                    ["Instructions are confusing", "Fiddly to set up"]),
    "packaging": (["Arrived in perfect condition", "Well protected in the box"],
                  ["Box was dented and the item scuffed", "Poor packaging, arrived damaged"]),
}
BEAUTY = {
    "quality": (["Lovely product, really effective", "Does what it promises"], ["Did nothing for me, disappointing", "Not as effective as the old formula"]),
    "scent": (["Gorgeous scent that lasts", "Lovely fresh fragrance"], ["Scent is too strong and chemical", "Fragrance faded within an hour"]),
    "skin_feel": (["Feels lovely on the skin", "Absorbs quickly, no residue"], ["Left my skin dry and irritated", "Sticky and heavy on the skin"]),
    "value": (["Great value for the size", "Lasts for ages"], ["Too expensive for such a small bottle", "Not worth the price"]),
    "packaging": (["Beautiful packaging, arrived intact", "Well wrapped"], ["Pump broke in transit", "Lid leaked in the parcel"]),
}
TEXTILE = {
    "quality": (["Thick, good quality", "Feels premium"], ["Thin and rough after washing", "Poor quality for the price"]),
    "comfort": (["So soft and cosy", "Lovely feel"], ["Scratchy and stiff", "Not very soft"]),
    "colour": (["Colour exactly as pictured", "Rich colour, no fading"], ["Colour bled in the first wash", "Duller than the photos"]),
    "value": (["Great value", "Worth the money"], ["Overpriced", "Cheaper elsewhere"]),
    "durability": (["Washes well, no pilling", "Still looks new"], ["Pilled after a few washes", "Frayed quickly"]),
    "size": (["Generous size", "Fits perfectly"], ["Smaller than described", "Too small for the bed"]),
    "packaging": (["Arrived neatly folded", "Well packaged"], ["Arrived crumpled and dirty", "Torn bag"]),
}
OUTER = {
    "waterproofing": (["Kept me dry through a proper downpour", "Properly waterproof, taped seams hold up"],
                      ["Soaked through in light rain", "Not waterproof, the fabric wets out quickly"]),
    "warmth": (["Warm without being bulky", "Really warm on cold mornings"],
               ["Not warm enough for winter", "Cold in the wind, needs a proper lining"]),
    "lightweight": (["Light and packs down small into its own pocket", "Easy to carry in a bag, barely notice the weight"],
                    ["Heavier than I expected", "Too bulky to pack away"]),
    "pockets": (["Plenty of zipped pockets for phone and keys", "Great pockets, a deep inner one fits my phone"],
                ["Pockets too small for a phone", "No zip on the pockets, things fall out"]),
    "fit": (["Good fit with room for a layer underneath", "True to size, flattering cut"],
            ["Sleeves too short", "Boxy and awkward fit"]),
    "durability": (["Zips and fabric still like new after a season", "Tough fabric that has survived a lot"],
                   ["Zip broke within weeks", "Fabric snagged and ripped on the first walk"]),
    "value": (["Good value compared with the big outdoor brands", "Worth the price"], ["Overpriced for what it is", "Not worth the money"]),
    "sustainability": (["Love that it is made from recycled fabric", "Good to see recycled materials and a PFC-free coating"],
                       ["Claims to be sustainable but there is no detail", "Recycled claim feels like greenwashing"]),
    "packaging": (["Arrived in perfect condition", "Well protected in the bag"], ["Bag split open in the post", "Arrived creased and damp"]),
}
NEUTRAL = ["It's fine, does the job", "Average, nothing special", "OK but I expected a little more", "Decent enough for the price"]

GROUP = {}
for c in ["Knitwear", "Babywear", "Trousers", "Scarves", "Schoolwear", "Nightwear", "Dresses", "Shirts", "Blouses", "Tops",
          "T-Shirts", "Footwear", "Bags", "Jewellery"]:
    GROUP[c] = APPAREL
for c in ["Small Appliances", "Smart Home", "Lighting", "Audio", "Personal Care", "Cookware", "Storage", "Drinkware"]:
    GROUP[c] = HARD
for c in ["Haircare", "Bodycare", "Fragrance", "Skincare"]:
    GROUP[c] = BEAUTY
for c in ["Towels", "Bedding"]:
    GROUP[c] = TEXTILE
GROUP["Outerwear"] = OUTER

SEGMENTS = ["25-34", "35-44", "18-24", "45-54", "55-64", "65+", "outdoor_enthusiast", "professional", "budget_conscious"]
SEG_W = [22, 18, 10, 14, 8, 4, 8, 8, 8]
COUNTRIES = ["GB", "DE", "FR", "IE", "NL"]
COUNTRY_W = [82, 8, 4, 3, 3]

# outerwear theme weights by (is 25-34, is Germany)
OUTER_W = {
    (False, False): {"waterproofing": 18, "warmth": 16, "lightweight": 8, "pockets": 8, "fit": 14, "durability": 14, "value": 10, "sustainability": 6, "packaging": 6},
    (True, False): {"waterproofing": 11, "warmth": 3, "lightweight": 28, "pockets": 24, "fit": 5, "durability": 3, "value": 5, "sustainability": 17, "packaging": 4},
    (False, True): {"waterproofing": 14, "warmth": 24, "lightweight": 6, "pockets": 6, "fit": 10, "durability": 12, "value": 8, "sustainability": 16, "packaging": 4},
    (True, True): {"waterproofing": 9, "warmth": 22, "lightweight": 6, "pockets": 4, "fit": 5, "durability": 5, "value": 5, "sustainability": 40, "packaging": 4},
}


def ratings_for(r, n, mean, sd=1.2):
    """n integer ratings 1..5 whose sum is exactly round(mean * n)."""
    vals = [min(5, max(1, round(mean + r.gauss(0, sd)))) for _ in range(n)]
    target = max(n, min(5 * n, round(mean * n)))
    guard = 0
    while sum(vals) != target and guard < 1000:
        guard += 1
        i = r.randrange(n)
        if sum(vals) < target and vals[i] < 5:
            vals[i] += 1
        elif sum(vals) > target and vals[i] > 1:
            vals[i] -= 1
    return vals


def generate(g):
    r = g.rng
    as_of = g.as_of
    products = g.master("products")
    stores = [s["site_id"] for s in g.master("sites") if s["type"] == "store"]
    by_style = {}
    for p in products:
        by_style.setdefault(p["style_id"], []).append(p)
    cat_of = {p["sku"]: p["category"] for p in products}

    reviews = []

    def when(k=None, days=None):
        if days is None:
            days = 7 * k - r.randint(0, 6)  # inside week k (k=1: the 7 days before as_of)
        d = as_of - timedelta(days=days)
        return datetime(d.year, d.month, d.day, r.randint(7, 22), r.randint(0, 59))

    def add(sku, style, rating, theme, text, ts, seg=None, country=None, store=None):
        reviews.append({
            "review_id": f"REV-{len(reviews) + 1:06d}", "sku": sku, "style_id": style, "store_id": store,
            "customer_segment": seg or r.choices(SEGMENTS, SEG_W)[0],
            "country": country or r.choices(COUNTRIES, COUNTRY_W)[0],
            "rating": rating, "review_text": text, "theme": theme, "created_at": ts})

    def pick(pool):
        return r.choice(pool)

    def pooltext(grp, rating, theme):
        pos, neg = grp[theme]
        if rating >= 4:
            return r.choice(pos)
        if rating <= 2:
            return r.choice(neg)
        return r.choice(NEUTRAL) if r.random() < 0.5 else r.choice(neg)

    def story(sku, style, plan, texter, pack=None):
        """plan: [(k, n, mean)]; texter(rating, k) -> (theme, text); pack: (weeks, pool) forces one packaging complaint a week."""
        for k, n, mean in plan:
            rows = [(rt,) + tuple(texter(rt, k)) for rt in ratings_for(r, n, mean + r.uniform(-0.1, 0.1))]
            rows.sort(key=lambda x: x[0])
            if pack and k in pack[0]:
                i = next((i for i, x in enumerate(rows) if 2 <= x[0] <= 4), None)
                if i is not None:
                    rows[i] = (rows[i][0],) + tuple(r.choice(pack[1]))
            for rt, theme, text in rows:
                add(sku, style, rt, theme, text, when(k), country="GB" if r.random() < 0.9 else None)

    def weighted(pairs):
        return r.choices([p[0] for p in pairs], [p[1] for p in pairs])[0]

    def pooled(pos, neg, mid=None, negw=None):
        def f(rt, k):
            if rt >= 4:
                return r.choice(pos)
            if rt <= 2:
                return weighted(negw) if negw else r.choice(neg)
            m = mid or neg
            return r.choice(m)
        return f

    # ---------------- stories ----------------
    r = random.Random("reviews-k1700")
    # K-1700 1.7L kettle: ratings fall over the last eight weeks, lid seal leaks dominate
    k_pos = [("performance", "Boils fast and quiet"), ("design", "Looks great on the worktop"),
             ("ease_of_use", "Easy to pour, no drips"), ("value", "Good value for a glass kettle"),
             ("quality", "Solid build, lid fits well"), ("performance", "Boils a full jug in no time")]
    k_leak = [("quality", "Lid started leaking after three weeks"), ("quality", "Water leaks from the lid seal when pouring"),
              ("quality", "Seal around the lid is defective, drips every time"), ("quality", "Leaks from the lid when I pour, returning it"),
              ("quality", "Lid seal failed within a month, water everywhere"), ("quality", "Kettle leaks from under the lid, faulty seal")]
    k_neg = [(x, 8) for x in k_leak] + [(("value", "Price keeps going up and the kettle is not worth it now"), 2),
                                         (("performance", "Takes ages to boil these days"), 1)]
    k_mid = [("quality", "Heats quickly but the lid drips a little"), ("quality", "OK kettle, wish the lid sealed better"),
             ("value", "Does the job but a bit pricey now"), ("performance", "Fine, though the lid seems loose")]
    k_pack = [("packaging", "Arrived with the glass jug smashed, the box was crushed"),
              ("packaging", "Carton crushed in transit and the jug cracked"),
              ("packaging", "Box arrived crushed at one corner, glass chipped")]
    plan = [(k, 9, m) for k, m in [(1, 2.7), (2, 2.9), (3, 3.0), (4, 3.3), (5, 3.6), (6, 3.9), (7, 4.1), (8, 4.3)]]
    plan += [(k, 9, 4.4) for k in range(9, 14)] + [(k, 5, 4.4) for k in range(14, 27)]
    story("K-1700", "STY-K-1700", plan, pooled(k_pos, None, k_mid, k_neg), pack=(set(range(1, 11)), k_pack))

    r = random.Random("reviews-pf220")
    # PF-220 desk fan: gentle decline (outlier vs plan)
    f_pos = [("performance", "Great airflow for a desk fan"), ("design", "Compact and looks smart"),
             ("value", "Good value, quiet on low"), ("ease_of_use", "Charges quickly and easy to use")]
    f_neg = [("performance", "Battery only lasts an hour on low"), ("quality", "Stopped charging after a month"),
             ("performance", "Too noisy on the highest setting"), ("quality", "Battery drains even when switched off")]
    plan = [(k, 5, 3.8) for k in range(1, 5)] + [(k, 5, 4.2) for k in range(5, 14)] + [(k, 3, 4.2) for k in range(14, 27)]
    story("PF-220", "STY-PF-220", plan, pooled(f_pos, f_neg, f_neg))

    r = random.Random("reviews-shoe")
    # SKU-100301 shoe: sole separation climbing over the last 13 weeks
    sole = ["Sole separation after only three weeks of wear", "Sole separation at the toe, the glue has given way",
            "The sole is separating from the upper after a month", "Sole separation on both shoes within weeks, very poor",
            "Sole came away from the upper on the first wet day", "Sole separation again - second pair I have had to return",
            "Sole peeling away from the shoe at the heel"]
    foot = APPAREL
    mentions = {13: 0, 12: 0, 11: 0, 10: 1, 9: 1, 8: 2, 7: 2, 6: 3, 5: 4, 4: 5, 3: 6, 2: 7, 1: 8}
    for k in range(1, 27):
        base_n = 4
        m = mentions.get(k, 0)
        for rt in ratings_for(r, base_n, 4.3 if k > 4 else 4.1):
            theme = r.choices(["sizing", "comfort", "quality", "value", "fit"], [3, 4, 2, 2, 3])[0]
            add("SKU-100301", "STY-4171", rt, theme, pooltext(foot, rt, theme), when(k), country="GB")
        for i in range(m):
            add("SKU-100301", "STY-4171", 1 + (i % 2), "durability", r.choice(sole), when(k), country="GB")

    r = random.Random("reviews-jeans")
    # SKU-100637 jeans (style STY-T-4410): waistband gapes at the back; comfort praised
    j_neg = [(("fit", "Waistband gapes at the back, I have to wear a belt"), 5),
             (("fit", "Gap at the back of the waistband whenever I sit down"), 4),
             (("fit", "Love the skinny fit on the legs but the waistband gapes at the back"), 4),
             (("fit", "Back of the waistband stands away from my body"), 3),
             (("sizing", "Runs a little small in the leg"), 2),
             (("quality", "Button came loose after a few weeks"), 2)]
    j_pos = [(("comfort", "So comfortable, the stretch denim moves with me"), 6),
             (("comfort", "Soft stretch denim, comfortable all day"), 5),
             (("fit", "Skinny fit looks great, flattering on the legs"), 4),
             (("quality", "Good quality denim, holds its shape in the wash"), 3),
             (("durability", "Still looking new after many washes"), 2),
             (("value", "Good value for jeans this good"), 1)]
    j_mid = [("fit", "Great on the legs but a slight gap at the back of the waist"), ("comfort", "Comfortable but the waistband gapes a bit")]

    def jeans(rt, k):
        if rt >= 4:
            return weighted(j_pos)
        if rt <= 2:
            return weighted(j_neg)
        return r.choice(j_mid)
    for k in range(1, 27):
        n = 6 if k <= 13 else 4
        for rt in ratings_for(r, n, 4.0):
            sku = r.choices(["SKU-100637", "SKU-100644", "SKU-100651"], [60, 20, 20])[0]
            th, tx = jeans(rt, k)
            add(sku, "STY-T-4410", rt, th, tx, when(k), country="GB")

    r = random.Random("reviews-athleisure")
    # STY-4056 athleisure tops: product liked, size 14 hard to find
    a_pos = [("quality", "Lovely soft fabric and the stitching is neat"), ("comfort", "Comfortable to train in, moves well"),
             ("fit", "Great fit, flattering and stays put"), ("value", "Good value for a gym top"),
             ("colour", "Sage colour is gorgeous and has not faded")]
    a_avail = [("availability", "Love the top but size 14 has been sold out for weeks"),
               ("availability", "Only size 10 left in my local store, nothing in 14"),
               ("availability", "Great product, shame I could not get a 14 anywhere"),
               ("availability", "Had to wait for size 14 to come back in stock")]
    a_size = [("sizing", "Runs a little small, size up"), ("sizing", "Smaller than expected across the chest")]
    for k in range(1, 27):
        n = 4 if k <= 13 else 3
        for rt in ratings_for(r, n, 4.4):
            th, tx = r.choice(a_pos)
            sku = r.choices(["SKU-100070", "SKU-100077", "SKU-100084"], [40, 35, 25])[0]
            add(sku, "STY-4056", rt, th, tx, when(k), country="GB")
        if k <= 13:
            for i in range(2):
                th, tx = r.choice(a_avail)
                add("SKU-100084", "STY-4056", 3 if r.random() < 0.7 else 4, th, tx, when(k), country="GB")
            if k % 3 == 0:
                th, tx = r.choice(a_size)
                add(r.choice(["SKU-100070", "SKU-100077"]), "STY-4056", 3, th, tx, when(k), country="GB")

    r = random.Random("reviews-blouses")
    # SKU-100014 / SKU-100007 / SKU-100021 blouses (STY-4012): 100014 is the outlier; polybag tears
    b_pos = [("quality", "Lovely soft blouse, looks smart"), ("colour", "Blush colour is lovely"),
             ("fit", "Flattering fit, true to size"), ("value", "Good value for a work blouse")]
    b_neg = [(("colour", "Colour faded after the first wash"), 4), (("quality", "Fabric is thinner than it looks online"), 3),
             (("sizing", "Runs small, had to return for a bigger size"), 3), (("durability", "Seam split after two wears"), 2)]
    b_pack = [("packaging", "Polybag arrived torn and the blouse was dirty"), ("packaging", "Bag split open in the post, blouse creased"),
              ("packaging", "Torn polybag, item grubby")]
    plan14 = [(k, 6, 3.5) for k in range(1, 6)] + [(k, 6, 4.1) for k in range(6, 14)] + [(k, 4, 4.1) for k in range(14, 27)]
    story("SKU-100014", "STY-4012", plan14, pooled(b_pos, None, [("quality", "Okay blouse, fabric a bit thin")], b_neg),
          pack=(set(range(1, 12)), b_pack))
    plan07 = [(k, 4, 4.2) for k in range(1, 14)] + [(k, 3, 4.2) for k in range(14, 27)]
    story("SKU-100007", "STY-4012", plan07, pooled(b_pos, None, [("quality", "Okay blouse, fabric a bit thin")], b_neg),
          pack=(set(range(1, 10)), b_pack))
    plan21 = [(k, 3, 4.2) for k in range(1, 27)]
    story("SKU-100021", "STY-4012", plan21, pooled(b_pos, None, [("quality", "Okay blouse, fabric a bit thin")], b_neg))

    r = random.Random("reviews-bottle")
    # SKU-106307 new 750ml insulated bottle (style STY-9501, Supplier A SUP-0004): insulation and leakproof lid are what customers value
    bt_pos = [(("insulation", "Keeps drinks ice cold for a full day, genuinely impressive"), 7),
              (("insulation", "Hot coffee still hot after 12 hours"), 5),
              (("lid", "Leakproof lid, I carry it in my bag with no spills"), 5),
              (("size", "750ml is the right size and fits the car cup holder"), 2),
              (("value", "Cheaper than the big brands and just as good"), 3),
              (("design", "Looks great and feels solid in the hand"), 2)]
    bt_neg = [(("finish", "Powder coat finish chipped within weeks"), 4), (("finish", "Paint scratches off very easily"), 3),
              (("lid", "Lid seal started to drip after a few months"), 2), (("quality", "Dented easily when dropped"), 2)]
    bt_mid = [("finish", "Keeps drinks cold but the finish scratches"), ("value", "Good bottle, a bit pricey")]
    plan = [(k, 5, 4.3) for k in range(1, 14)] + [(k, 3, 4.3) for k in range(14, 27)]
    story("SKU-106307", "STY-9501", plan, lambda rt, k: (weighted(bt_pos) if rt >= 4 else weighted(bt_neg) if rt <= 2 else r.choice(bt_mid)),
          pack=(set(range(1, 6)), [("packaging", "Bottle arrived dented, no outer box"), ("packaging", "Arrived scuffed, thin packaging")]))

    r = random.Random("reviews-suppliers")
    # Outerwear suppliers in Portugal / Turkey: SUP-0058 (STY-4102), SUP-0030 (STY-4605), SUP-0079 (STY-6070, STY-9089),
    # SUP-0065 (STY-8880), SUP-0037 (STY-5613, STY-9100)
    sup_story = {
        "STY-4102": (4.6, [("waterproofing", "Fully seam-sealed, stayed dry in heavy rain"), ("waterproofing", "Taped seams are excellent, no leaks at all"),
                           ("durability", "Superb build, zips and seams are first class"), ("warmth", "Warm and fully waterproof, great jacket")], None),
        "STY-4605": (4.3, [("waterproofing", "Keeps the rain out, seams hold up"), ("fit", "Good fit, comfortable"), ("value", "Good value")], None),
        "STY-6070": (4.1, [("lightweight", "Light shell, packs away well"), ("waterproofing", "Fine in showers"), ("fit", "True to size")], None),
        "STY-9089": (4.0, [("lightweight", "Light and easy to carry"), ("pockets", "Good pockets"), ("fit", "Decent fit")], None),
        "STY-8880": (3.9, [("warmth", "Warm enough for autumn"), ("fit", "Fits well"), ("value", "Fair for the clearance price")], None),
        "STY-5613": (3.3, [("waterproofing", "Looks great but fine in drizzle only")], [("waterproofing", "Seams leaked in the first rain, not properly sealed"),
                                                                                              ("waterproofing", "Taped seams lifting after a few wears, water gets in"),
                                                                                              ("durability", "Zip failed after a month"), ("waterproofing", "Not waterproof despite the label, seams let water through")]),
        "STY-9100": (3.4, [("fit", "Nice colour and cut")], [("waterproofing", "Seam tape peeled off, jacket leaks at the shoulders"),
                                                             ("durability", "Zip broke within weeks"), ("waterproofing", "Water comes through the seams in heavy rain")]),
    }
    for style, (mean, pos, neg) in sup_story.items():
        prods = by_style[style]
        skus = [p["sku"] for p in prods if p["status"] in ("active", "clearance")] or [prods[0]["sku"]]
        for half, (lo, hi) in enumerate([(1, 12), (14, 26)]):
            for k in range(lo, hi + 1):
                if k % (1 if half == 0 else 2):
                    continue
                for rt in ratings_for(r, 2, mean):
                    if rt >= 4 or not neg:
                        th, tx = r.choice(pos)
                    elif rt <= 2:
                        th, tx = r.choice(neg or pos)
                    else:
                        th, tx = r.choice(neg) if neg else ("fit", "Okay jacket, nothing special")
                    seg = r.choices(SEGMENTS[1:], SEG_W[1:])[0]
                    add(r.choice(skus), style, rt, th, tx, when(k), seg=seg)

    r = random.Random("reviews-returns")
    # Top returned styles that have launched: dominant complaint theme
    ret_story = {
        "STY-8683": ("expectation", 3.2, ["Not as described, nothing like the product page", "Looks completely different to the photos", "Texture and scent are not what the listing promised", "Smaller than the picture suggests, not as advertised"],
                     [("quality", "Lovely product, does what it says"), ("scent", "Pleasant fragrance")]),
        "STY-5094": ("quality", 3.0, ["Strap snapped within a month", "Zip failed after two weeks", "Stitching on the handle came apart", "Lining ripped on first use"],
                     [("value", "Good value for the price"), ("design", "Roomy and looks smart")]),
        "STY-4123": ("sizing", 3.1, ["Runs very small, had to return", "Sizing is nothing like the chart, far too tight", "Ordered my usual size and it was too small", "Much smaller than the age on the label"],
                     [("value", "Good value for school"), ("comfort", "Comfortable for school days")]),
        "STY-8908": ("sizing", 2.9, ["Runs a full size small", "Narrow and too tight, had to send them back", "Sizing is off, ordered two sizes to compare", "Too small even in my usual size"],
                     [("comfort", "Comfortable once worn in"), ("value", "Nice shoes for the price")]),
    }
    for style, (th, mean, negs, poss) in ret_story.items():
        prods = by_style[style]
        sku = next((p["sku"] for p in prods if p["status"] == "active"), prods[0]["sku"])
        for k in range(1, 27):
            if k > 13 and k % 2:
                continue
            for rt in ratings_for(r, 2, mean if k <= 13 else 4.1, 1.5):
                if rt <= 3:
                    add(sku, style, rt, th, r.choice(negs), when(k), country="GB")
                else:
                    pt, px = r.choice(poss)
                    add(sku, style, rt, pt, px, when(k), country="GB")

    story_styles = {"STY-K-1700", "STY-PF-220", "STY-4171", "STY-T-4410", "STY-4056", "STY-4012", "STY-5905"} | set(sup_story) | set(ret_story)

    r = random.Random("reviews-background")
    # ---------------- background: every launched style, one primary SKU ----------------
    cutoff = (as_of - timedelta(days=21)).isoformat()
    for style in sorted(by_style):
        if style in story_styles:
            continue
        prods = [p for p in by_style[style] if p["launch_date"] <= cutoff]
        if not prods:
            continue
        prods.sort(key=lambda p: (p["status"] == "discontinued", p["sku"]))
        prim = prods[0]
        cat = prim["category"]
        grp = GROUP.get(cat, APPAREL)
        base = r.choice([3.9, 4.0, 4.1, 4.2, 4.3, 4.4])
        for lo, hi in [(1, 89), (91, 180)]:
            n = r.randint(7, 12) if grp is OUTER else r.randint(4, 8)
            mean = max(3.0, min(4.8, base + r.uniform(-0.1, 0.1)))
            for rt in ratings_for(r, n, mean, 0.9):
                seg = r.choices(SEGMENTS, [35, 14, 8, 10, 6, 3, 8, 8, 8] if grp is OUTER else SEG_W)[0]
                country = r.choices(COUNTRIES, [68, 20, 5, 4, 3] if grp is OUTER else COUNTRY_W)[0]
                if grp is OUTER:
                    w = OUTER_W[(seg == "25-34", country == "DE")]
                    theme = r.choices(list(w), list(w.values()))[0]
                else:
                    theme = r.choice(list(grp))
                text = pooltext(grp, rt, theme)
                store = r.choice(stores) if r.random() < 0.08 else None
                add(prim["sku"], style, rt, theme, text, when(days=r.randint(lo, hi)), seg=seg, country=country, store=store)

    r = random.Random("reviews-competitors")
    # ---------------- competitor products and their reviews ----------------
    comp = [
        # id, competitor, category, name, price, status, features, our sku, avg rating, review count
        ("CMPD-001-L01", "HomeShop Direct", "Lunch boxes", "HomeShop Insulated Lunch Bag 5L", 14.99, "active", "Compact portable design; foil lined; zip closure", None, 3.6, 1240),
        ("CMPD-002-L01", "John Lewis", "Lunch boxes", "John Lewis Premium Insulated Lunch Box", 34.0, "active", "Leakproof compartments; stainless steel inner; BPA-free", None, 4.4, 860),
        ("CMPD-003-L01", "Carrefour", "Lunch boxes", "Boite isotherme dejeuner", 11.99, "active", "Lightweight and durable; single compartment", None, 3.4, 410),
        ("CMPD-005-L01", "Argos", "Lunch boxes", "Argos Thermal Lunch Box", 13.2, "active", "Space-saving design; two compartments; cutlery included", None, 3.9, 2150),
        ("CMPD-006-L01", "JD Sports", "Lunch boxes", "JD Gym Meal Prep Insulated Bag", 24.99, "active", "Multiple containers; ice pack included; shoulder strap", None, 4.1, 720),
        ("CMPD-006-R01", "JD Sports", "Wellness & recovery", "JD Percussion Massage Gun", 89.99, "bestseller", "6 speeds; 5 attachments", None, 4.5, 3120),
        ("CMPD-006-R02", "JD Sports", "Wellness & recovery", "JD Vibrating Foam Roller", 34.99, "active", "Three vibration levels", None, 3.9, 640),
        ("CMPD-006-R03", "JD Sports", "Wellness & recovery", "JD Compression Recovery Boots", 80.0, "discontinued", "Air compression for legs", None, 3.0, 380),
        ("CMPD-002-R01", "John Lewis", "Wellness & recovery", "John Lewis Weighted Blanket 6kg", 79.0, "bestseller", "Glass bead fill; cotton cover", None, 4.6, 2480),
        ("CMPD-002-R02", "John Lewis", "Wellness & recovery", "John Lewis Ultrasonic Aroma Diffuser", 35.0, "bestseller", "Colour-changing light; timer", None, 4.4, 1760),
        ("CMPD-002-R03", "John Lewis", "Wellness & recovery", "John Lewis Magnesium Bath Soak Set", 18.0, "active", "Magnesium flakes; three scents", None, 4.3, 540),
        ("CMPD-001-R01", "HomeShop Direct", "Wellness & recovery", "HomeShop Cold Plunge Tub 100L", 100.0, "discontinued", "Inflatable ice bath with lid", None, 2.8, 310),
        ("CMPD-004-R01", "Currys", "Wellness & recovery", "Currys Infrared Sauna Blanket", 149.99, "discontinued", "Infrared heating; 3 heat settings", None, 2.7, 240),
        ("CMPD-005-R01", "Argos", "Wellness & recovery", "Argos Foam Roller 33cm", 12.99, "active", "High density EVA foam", None, 4.2, 1900),
        ("CMPD-005-R02", "Argos", "Wellness & recovery", "Argos Mini Massage Gun", 49.99, "active", "Pocket size; 3 speeds", None, 3.8, 870),
        ("CMPD-001-BT1", "HomeShop Direct", "Insulated bottles", "Premium Insulated Bottle 750ml", 13.99, "active", "Keeps cold 24 hours, hot 12; double-wall stainless steel", "SKU-106307", 4.4, 980),
        ("CMPD-002-BT1", "John Lewis", "Insulated bottles", "John Lewis Insulated Travel Bottle 750ml", 17.95, "active", "Stainless steel double wall; leakproof lid", "SKU-106307", 4.6, 1320),
        ("CMPD-003-BT1", "Carrefour", "Insulated bottles", "Bouteille isotherme 750 ml", 12.99, "active", "Durable design; vacuum insulated", "SKU-106307", 4.0, 350),
        ("CMPD-005-BT1", "Argos", "Insulated bottles", "Argos Premium Insulated Bottle 750ml", 10.49, "active", "Sleek design keeps drinks hot or cold", "SKU-106307", 4.2, 1510),
        ("CMPD-006-BT1", "JD Sports", "Insulated bottles", "JD Insulated Steel Bottle 750ml", 10.99, "active", "Gym-friendly sports cap; vacuum insulated", "SKU-106307", 4.1, 690),
        ("CMPD-006-AT1", "JD Sports", "Athleisure", "JD Seamless Gym Top", 25.5, "active", "Seamless; moisture-wicking", "SKU-100070", 4.1, 910),
        ("CMPD-006-AT2", "JD Sports", "Athleisure", "JD High-Waist Leggings", 28.5, "active", "High waist; squat-proof", None, 4.2, 1450),
        ("CMPD-006-AT3", "JD Sports", "Athleisure", "JD Zip Hoodie", 45.0, "active", "Brushed fleece; zip pockets", None, 4.0, 760),
        ("CMPD-002-AT1", "John Lewis", "Athleisure", "John Lewis Studio Seamless Top", 45.0, "active", "Recycled yarn; seamless", "SKU-100070", 4.4, 520),
        ("CMPD-002-AT2", "John Lewis", "Athleisure", "John Lewis Studio Leggings", 55.0, "active", "Four-way stretch", None, 4.5, 880),
        ("CMPD-002-AT3", "John Lewis", "Athleisure", "John Lewis Studio Zip Hoodie", 69.0, "active", "Organic cotton blend", None, 4.3, 430),
        ("CMPD-005-AT1", "Argos", "Athleisure", "Argos Active Training Top", 17.6, "active", "Quick-dry fabric", "SKU-100070", 3.8, 1320),
        ("CMPD-005-AT2", "Argos", "Athleisure", "Argos Active Leggings", 25.0, "active", "Elastic waistband", None, 3.7, 1100),
        ("CMPD-001-AT1", "HomeShop Direct", "Athleisure", "HomeShop Performance Top", 23.99, "active", "Breathable mesh panels", "SKU-100070", 3.9, 640),
        ("CMPD-001-AT2", "HomeShop Direct", "Athleisure", "HomeShop Performance Leggings", 32.0, "active", "Pocketed; high waist", None, 4.0, 590),
        ("CMPD-001-K01", "HomeShop Direct", "Small appliances", "1.7L Glass Electric Kettle", 59.49, "active", "1.7L glass jug; blue LED", "K-1700", 4.2, 2210),
        ("CMPD-002-K01", "John Lewis", "Small appliances", "John Lewis Glass Kettle 1.7L", 89.99, "active", "1.7L glass; variable temperature", "K-1700", 4.6, 1480),
        ("CMPD-003-K01", "Carrefour", "Small appliances", "Bouilloire verre 1.7L", 59.99, "active", "1.7L glass; auto shut-off", "K-1700", 3.9, 420),
        ("CMPD-004-K01", "Currys", "Small appliances", "Currys Pro Glass Kettle 1.7L", 74.99, "active", "1.7L glass; keep-warm", "K-1700", 4.3, 1760),
        ("CMPD-005-K01", "Argos", "Small appliances", "Argos 1.7L Glass Kettle", 64.99, "active", "1.7L glass; rapid boil", "K-1700", 4.0, 3050),
        ("CMPD-005-T01", "Argos", "Small appliances", "Argos 4-Slice Toaster", 39.99, "active", "4 slices; 6 browning levels", "SKU-101309", 3.8, 2640),
        ("CMPD-004-T01", "Currys", "Small appliances", "Currys Essentials 4-Slice Toaster", 44.99, "active", "4 slices; defrost and reheat", "SKU-101309", 4.0, 1130),
        ("CMPD-001-T01", "HomeShop Direct", "Small appliances", "HomeShop 4-Slice Toaster", 49.99, "active", "4 slices; wide slots", "SKU-101309", 3.9, 970),
        ("CMPD-002-T01", "John Lewis", "Small appliances", "John Lewis 4-Slice Toaster", 69.99, "active", "4 slices; stainless steel; variable browning", "SKU-101309", 4.5, 760),
        # our top sellers by revenue (the e-commerce ranking): stand mixers (style STY-8220), shirt, headphones, soundbar; appended last so earlier random draws are unchanged
        ("CMPD-004-M01", "Currys", "Food preparation", "Currys Pro 5L Stand Mixer", 249.99, "active", "1000W; 5L bowl; three attachments", "SKU-104032", 4.2, 1380),
        ("CMPD-005-M01", "Argos", "Food preparation", "Argos 4.8L Stand Mixer", 199.99, "active", "800W; tilt-head; splash guard", "SKU-104032", 3.9, 2240),
        ("CMPD-002-M01", "John Lewis", "Food preparation", "John Lewis 5L Stand Mixer", 279.0, "active", "1200W; planetary mixing; 10 speeds", "SKU-104032", 4.7, 960),
        ("CMPD-001-M01", "HomeShop Direct", "Food preparation", "HomeShop Tilt-head Stand Mixer 5L", 214.99, "active", "1000W; dough hook and whisk", "SKU-104032", 4.0, 740),
        ("CMPD-002-SH1", "John Lewis", "Men's shirts", "John Lewis Premium Oxford Shirt", 139.0, "active", "Cotton oxford; button-down collar", "SKU-105075", 4.5, 820),
        ("CMPD-001-SH1", "HomeShop Direct", "Men's shirts", "HomeShop Easy Iron Shirt", 104.99, "active", "Easy iron cotton blend", "SKU-105075", 3.7, 1150),
        ("CMPD-005-SH1", "Argos", "Men's shirts", "Argos Collection Cotton Shirt", 94.99, "active", "Regular fit; non-iron", "SKU-105075", 3.6, 1640),
        ("CMPD-006-SH1", "JD Sports", "Men's shirts", "JD Smart Shirt", 124.99, "active", "Slim fit; stretch cotton", "SKU-105075", 4.0, 530),
        ("CMPD-004-H01", "Currys", "Headphones", "Currys Pro Wireless Headphones", 149.99, "active", "Active noise cancelling; 30 hour battery", "SKU-102261", 4.1, 1870),
        ("CMPD-005-H01", "Argos", "Headphones", "Argos Wireless Over-ear Headphones", 129.99, "active", "Bluetooth 5; 25 hour battery", "SKU-102261", 3.8, 2960),
        ("CMPD-002-H01", "John Lewis", "Headphones", "John Lewis Studio Wireless Headphones", 179.0, "active", "Noise cancelling; multipoint", "SKU-102261", 4.5, 1220),
        ("CMPD-001-H01", "HomeShop Direct", "Headphones", "HomeShop Wireless Headphones", 139.99, "active", "Bluetooth; foldable", "SKU-102261", 3.9, 880),
        ("CMPD-004-SB1", "Currys", "Soundbars", "Currys Pro 3.1 Soundbar", 169.99, "active", "Wireless sub; Dolby Atmos", "SKU-100630", 4.2, 1010),
        ("CMPD-005-SB1", "Argos", "Soundbars", "Argos 2.1 Soundbar with Subwoofer", 159.99, "active", "Bluetooth; HDMI ARC", "SKU-100630", 3.9, 1760),
        ("CMPD-002-SB1", "John Lewis", "Soundbars", "John Lewis 3.1 Soundbar", 199.0, "active", "Dolby Atmos; app control", "SKU-100630", 4.6, 690),
        ("CMPD-003-SB1", "Carrefour", "Soundbars", "Barre de son 2.1", 149.99, "active", "Bluetooth; remote", "SKU-100630", 3.5, 290),
    ]
    LB_NEG = [("leaking", "Leaked all over my bag in the first week"), ("leaking", "Lid does not seal, soup leaked everywhere"),
              ("leaking", "Not leakproof despite the claims"), ("leaking", "Liner seam leaks when it tips"), ("leaking", "Soup leaked out of the lid in my rucksack"),
              ("leaking", "Leaks from the seal every time I carry it"), ("leaking", "Lid is not watertight, dressing leaked everywhere"),
              ("insulation", "Food only stays cool for a couple of hours"), ("insulation", "Ice pack barely helps, lunch warm by noon"),
              ("durability", "Zip broke after a month"), ("durability", "Clasp snapped off"), ("size", "Too small for an adult lunch"),
              ("value", "Overpriced for the quality")]
    LB_POS = [("insulation", "Kept my lunch cool all morning"), ("design", "Compact design, fits in my work bag"),
              ("size", "Good size for a full meal"), ("value", "Great value for the price"), ("leaking", "Completely leakproof, even with soup")]
    pools = {
        "Lunch boxes": (LB_POS, LB_NEG),
        "Insulated bottles": ([("insulation", "Keeps drinks cold all day"), ("lid", "Leakproof lid, no spills in my bag"), ("design", "Sleek and sturdy"), ("value", "Good value")],
                              [("finish", "Paint chipped quickly"), ("lid", "Lid started to leak"), ("quality", "Dented easily"), ("value", "Too expensive")]),
        "Athleisure": ([("fit", "Great fit and stays put when training"), ("quality", "Good fabric, washes well"), ("comfort", "Comfortable and breathable"), ("value", "Good value")],
                       [("sizing", "Sizing runs small"), ("quality", "Pilled after a few washes"), ("fit", "Slips down while exercising"), ("value", "Poor value")]),
        "Food preparation": ([("performance", "Powerful motor, kneads dough easily"), ("design", "Looks great on the worktop"), ("value", "Good value")],
                             [("noise", "Very loud on high speed"), ("quality", "Bowl lock came loose"), ("value", "Too expensive for what it does")]),
        "Men's shirts": ([("fit", "True to size and smart"), ("quality", "Good cotton, irons well"), ("value", "Good value")],
                         [("quality", "Collar frayed after a few washes"), ("sizing", "Sleeves too long"), ("value", "Overpriced for the quality")]),
        "Headphones": ([("sound", "Clear sound and great bass"), ("battery", "Battery lasts all week"), ("comfort", "Comfortable for long sessions")],
                       [("connection", "Bluetooth drops out"), ("comfort", "Ear cups too tight"), ("value", "Pricey for the sound quality")]),
        "Soundbars": ([("sound", "Fills the room, dialogue is clear"), ("setup", "Easy to set up with the TV"), ("value", "Good value")],
                      [("connection", "HDMI ARC cuts out"), ("sound", "Subwoofer is boomy"), ("value", "Too expensive for the sound")]),
        "Small appliances": ([("performance", "Boils fast and quiet"), ("design", "Looks great"), ("value", "Good value")],
                             [("quality", "Lid leaked after a few weeks"), ("performance", "Slow to boil"), ("quality", "Stopped working after a few months")]),
    }
    special = {
        "CMPD-001-R01": ([("comfort", "Cold water recovery is great when it holds water")],
                         [("leaking", "Leaked within a week, flooded the garage"), ("setup", "Took an hour to set up and fill, then needed constant ice"),
                          ("size", "Too big to store in a flat"), ("value", "Way overpriced for an inflatable tub"), ("quality", "The lid zip failed")]),
        "CMPD-006-R03": ([("performance", "Legs feel better after a session")],
                         [("comfort", "Straps too tight, uncomfortable on the calves"), ("noise", "Pump is very loud"),
                          ("durability", "Stopped inflating after two months"), ("value", "Too expensive for how long it lasted")]),
        "CMPD-004-R01": ([("heat", "Warm and relaxing when it works")],
                         [("odour", "Strong plastic smell when heating"), ("heat", "Heats unevenly, cold at the feet"),
                          ("value", "Far too expensive for a blanket"), ("safety", "Controller overheated at the plug")]),
        "CMPD-002-R01": ([("comfort", "Sleep much better under this"), ("quality", "Beads evenly distributed, lovely cover"), ("value", "Worth every penny")],
                         [("heat", "Too warm in summer"), ("size", "Smaller than expected")]),
        "CMPD-006-R01": ([("performance", "Powerful and the attachments are useful"), ("battery", "Battery lasts a week of daily use"), ("value", "Great for the price")],
                         [("noise", "Quite loud on the top setting"), ("battery", "Battery drains faster than claimed")]),
        "CMPD-002-R02": ([("scent", "Lovely with essential oils, fills the room"), ("design", "Looks great on a shelf"), ("quality", "Quiet and reliable")],
                         [("quality", "Mist stopped after an hour"), ("leaking", "Leaked at the base")]),
        "CMPD-002-R03": ([("scent", "Lovely scents, relaxing soak"), ("quality", "Good quality flakes")], [("value", "Pricey for the amount")]),
        "CMPD-005-R01": ([("value", "Cheap and does the job"), ("quality", "Good firm foam")], [("comfort", "Too hard for sore muscles"), ("durability", "Dented after a month")]),
        "CMPD-006-R02": ([("performance", "Vibration really helps"), ("design", "Good size")], [("battery", "Battery weak"), ("noise", "Rattles at high speed")]),
        "CMPD-005-R02": ([("value", "Great little gun for the money"), ("design", "Pocket size is handy")], [("performance", "Not powerful enough"), ("battery", "Battery dies fast")]),
        "CMPD-002-L01": ([("leaking", "Completely leakproof compartments"), ("design", "Sturdy, stylish stainless steel inner"), ("insulation", "Keeps food cool for hours")],
                         [("value", "Expensive for a lunch box"), ("weight", "Heavy once you add food"), ("leaking", "Lid seal leaked once with soup")]),
    }
    comp_rows, creviews = [], []
    cn = 0
    for pid, cname, cat, pname, price, status, feat, sku, mean, cnt in comp:
        pos, neg = special.get(pid, pools.get(cat, pools["Lunch boxes"]))
        n = 30 if cat in ("Lunch boxes", "Wellness & recovery") else 12
        late = status == "discontinued"
        sample = ratings_for(r, n, mean, 1.5)
        for rt in sample:
            if rt >= 4:
                th, tx = r.choice(pos)
            elif rt <= 2:
                th, tx = r.choice(neg)
            else:
                th, tx = r.choice(neg) if r.random() < 0.5 else (r.choice(pos)[0], r.choice(NEUTRAL))
            cn += 1
            days = r.randint(50, 89) if late else r.randint(2, 89)
            d = as_of - timedelta(days=days)
            creviews.append({"competitor_review_id": f"CREV-{cn:06d}", "competitor_product_id": pid, "rating": rt, "review_text": tx,
                             "theme": th, "created_at": datetime(d.year, d.month, d.day, r.randint(7, 22), r.randint(0, 59))})
        comp_rows.append({"competitor_product_id": pid, "competitor_name": cname, "category": cat, "product_name": pname,
                          "price_gbp": price, "avg_rating": mean, "review_count": cnt, "status": status, "features": feat,
                          "sku": sku, "collected_at": as_of - timedelta(days=r.randint(0, 3))})

    # ---------------- 02:21:Q1: the returns system's top returned styles carry a dominant complaint theme ----------------
    # (STY-T-4410 fit, STY-4171 quality and STY-K-1700 quality are planted above.) Added last so no earlier review changes.
    r = random.Random("reviews-top-returns")
    top_story = {
        "STY-5520": ("sizing", 3.0, ["Runs very small, had to return", "Ordered my usual size and it was far too tight", "Sizing is nothing like the chart",
                                     "Too small across the bust, sent it back"],
                     [("design", "Lovely dress, lovely colour"), ("value", "Good value for the price")]),
        "STY-4042": ("expectation", 3.1, ["Not as described, the colour is nothing like the photos", "Looks completely different to the product page",
                                          "Thinner than the listing suggested, not as advertised", "Not what I expected from the description"],
                     [("comfort", "Soft and warm"), ("value", "Good value jumper")]),
    }
    for style, (th, mean, negs, poss) in top_story.items():
        prods = by_style[style]
        sku = next((p["sku"] for p in prods if p["status"] == "active"), prods[0]["sku"])
        for k in range(1, 13):
            for rt in ratings_for(r, 2, mean, 1.5):
                if rt <= 3:
                    add(sku, style, rt, th, r.choice(negs), when(k), country="GB")
                else:
                    pt, px = r.choice(poss)
                    add(sku, style, rt, pt, px, when(k), country="GB")

    return {"reviews": reviews, "competitor_products": comp_rows, "competitor_reviews": creviews}
