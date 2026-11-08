"""Astra AstroStore Dynamic Astrological Upsell & Remedy Recommender Engine.

Bridges the Vedic Astrology calculation engines (Lal Kitab 1-Year Varshphal,
Daily Horoscope Gochar, Sade Sati transits, Kundli & Milan Doshas) directly
with authentic, consecrated AstroStore remedy products.
"""

from typing import Any
from beanie.operators import In, Or, RegEx
from loguru import logger

from app.models.enums import ProductCategoryType
from app.models.shop import Product
from app.schemas.shop import ShopProductRecommendationOut

# ===========================================================================
# Canonical Vedic & Lal Kitab Association Maps
# ===========================================================================

PLANET_REMEDY_MAP: dict[str, dict[str, Any]] = {
    "saturn": {
        "keywords": ["saturn", "shani", "7-mukhi", "blue sapphire", "neelam", "horseshoe", "amethyst", "katela"],
        "sacred_reason_bn": "শনির সাড়ে সাতি, ধাইয়া ও কণ্টক শনি প্রশমন এবং কর্মক্ষেত্রের স্থিতিশীলতার জন্য শাস্ত্রমত প্রতিবিধান।",
        "sacred_reason_hi": "शनि की साढ़े साती, ढैय्या एवं करियर में स्थिरता हेतु शास्त्रसम्मत सिद्ध उपाय।",
        "sacred_reason_en": "Authentic consecrated remedy for Saturn Sade Sati, Kantaka Shani, and professional stability.",
    },
    "shani": {
        "keywords": ["saturn", "shani", "7-mukhi", "blue sapphire", "neelam", "horseshoe", "amethyst"],
        "sacred_reason_bn": "শনির সাড়ে সাতি, ধাইয়া ও কণ্টক শনি প্রশমন এবং কর্মক্ষেত্রের স্থিতিশীলতার জন্য শাস্ত্রমত প্রতিবিধান।",
        "sacred_reason_hi": "शनि की साढ़े साती, ढैय्या एवं करियर में स्थिरता हेतु शास्त्रसम्मत सिद्ध उपाय।",
        "sacred_reason_en": "Authentic consecrated remedy for Saturn Sade Sati, Kantaka Shani, and professional stability.",
    },
    "jupiter": {
        "keywords": ["jupiter", "guru", "brihaspati", "5-mukhi", "yellow sapphire", "pukhraj", "haldi mala"],
        "sacred_reason_bn": "বৃহস্পতির শুভত্ব বৃদ্ধি, জ্ঞান, উচ্চশিক্ষা, সন্তানসুখ ও আর্থিক সমৃদ্ধির জন্য দেবগুরু বিহিত প্রতিকার।",
        "sacred_reason_hi": "बृहस्पति ग्रह की शुभता, ज्ञान, संतान सुख एवं आर्थिक संपन्नता हेतु देवगुरु विहित उपाय।",
        "sacred_reason_en": "Auspicious Jupiter blessing for wisdom, financial growth, and divine grace.",
    },
    "guru": {
        "keywords": ["jupiter", "guru", "brihaspati", "5-mukhi", "yellow sapphire", "pukhraj", "haldi mala"],
        "sacred_reason_bn": "বৃহস্পতির শুভত্ব বৃদ্ধি, জ্ঞান, উচ্চশিক্ষা, সন্তানসুখ ও আর্থিক সমৃদ্ধির জন্য দেবগুরু বিহিত প্রতিকার।",
        "sacred_reason_hi": "बृहस्पति ग्रह की शुभता, ज्ञान, संतान सुख एवं आर्थिक संपन्नता हेतु देवगुरु विहित उपाय।",
        "sacred_reason_en": "Auspicious Jupiter blessing for wisdom, financial growth, and divine grace.",
    },
    "mars": {
        "keywords": ["mars", "mangal", "3-mukhi", "red coral", "moonga", "copper"],
        "sacred_reason_bn": "মাঙ্গলিক দোষ প্রশমন, রক্ত ও ভূমি সম্পর্কিত বাধার নিরসন এবং সাহস বৃদ্ধির জন্য ভৌমিক প্রতিবিধান।",
        "sacred_reason_hi": "मांगलिक दोष शांति, भूमि-संपत्ति विवाद निवारण एवं रक्त-ऊर्जा वृद्धि हेतु उपाय।",
        "sacred_reason_en": "Manglik Dosha pacification, vitality, and courage enhancement.",
    },
    "mangal": {
        "keywords": ["mars", "mangal", "3-mukhi", "red coral", "moonga", "copper"],
        "sacred_reason_bn": "মাঙ্গলিক দোষ প্রশমন, রক্ত ও ভূমি সম্পর্কিত বাধার নিরসন এবং সাহস বৃদ্ধির জন্য ভৌমিক প্রতিবিধান।",
        "sacred_reason_hi": "मांगलिक दोष शांति, भूमि-संपत्ति विवाद निवारण एवं रक्त-ऊर्जा वृद्धि हेतु उपाय।",
        "sacred_reason_en": "Manglik Dosha pacification, vitality, and courage enhancement.",
    },
    "sun": {
        "keywords": ["sun", "surya", "1-mukhi", "12-mukhi", "ruby", "manik", "copper coin"],
        "sacred_reason_bn": "সূর্য দেবের আশীর্বাদ, পিতৃসুখ, আত্মসম্মান, সরকারি চাকরি ও রাজকীয় সাফল্যের জন্য শাস্ত্রীয় প্রতিকার।",
        "sacred_reason_hi": "सूर्य देव कृपा, मान-सम्मान, सरकारी नौकरी एवं आत्मबल संवर्धन हेतु सूर्य उपाय।",
        "sacred_reason_en": "Royal Sun blessing for leadership, prestige, paternal vitality, and executive victory.",
    },
    "surya": {
        "keywords": ["sun", "surya", "1-mukhi", "12-mukhi", "ruby", "manik", "copper coin"],
        "sacred_reason_bn": "সূর্য দেবের আশীর্বাদ, পিতৃসুখ, আত্মসম্মান, সরকারি চাকরি ও রাজকীয় সাফল্যের জন্য শাস্ত্রীয় প্রতিকার।",
        "sacred_reason_hi": "सूर्य देव कृपा, मान-सम्मान, सरकारी नौकरी एवं आत्मबल संवर्धन हेतु सूर्य उपाय।",
        "sacred_reason_en": "Royal Sun blessing for leadership, prestige, paternal vitality, and executive victory.",
    },
    "moon": {
        "keywords": ["moon", "chandra", "2-mukhi", "pearl", "moti", "silver", "sphatik"],
        "sacred_reason_bn": "চন্দ্র দোষ ও মানসিক অস্থিরতা নিবারণ, মাতৃদোষ মুক্তি এবং মানসিক প্রশান্তির জন্য বিশুদ্ধ প্রতিকার।",
        "sacred_reason_hi": "चंद्र दोष, मानसिक तनाव निवारण एवं भावनात्मक संतुलन हेतु सिद्ध उपाय।",
        "sacred_reason_en": "Moon pacification for mental tranquility, emotional stability, and mother's blessing.",
    },
    "chandra": {
        "keywords": ["moon", "chandra", "2-mukhi", "pearl", "moti", "silver", "sphatik"],
        "sacred_reason_bn": "চন্দ্র দোষ ও মানসিক অস্থিরতা নিবারণ, মাতৃদোষ মুক্তি এবং মানসিক প্রশান্তির জন্য বিশুদ্ধ প্রতিকার।",
        "sacred_reason_hi": "चंद्र दोष, मानसिक तनाव निवारण एवं भावनात्मक संतुलन हेतु सिद्ध उपाय।",
        "sacred_reason_en": "Moon pacification for mental tranquility, emotional stability, and mother's blessing.",
    },
    "venus": {
        "keywords": ["venus", "shukra", "6-mukhi", "diamond", "white zircon", "sphatik", "shree yantra"],
        "sacred_reason_bn": "শুক্রের কৃপা, প্রেম-দাম্পত্য সৌহার্দ্য, মোহিনী আকর্ষণ ও বিলাসিতার জন্য মহালক্ষ্মী বিহিত প্রতিকার।",
        "sacred_reason_hi": "शुक्र ग्रह की कृपा, दांपत्य प्रेम, आकर्षण एवं ऐश्वर्य प्राप्ति हेतु महालक्ष्मी विहित उपाय।",
        "sacred_reason_en": "Venusian resonance for love, marital bliss, luxury, and Goddess Mahalakshmi's bounty.",
    },
    "shukra": {
        "keywords": ["venus", "shukra", "6-mukhi", "diamond", "white zircon", "sphatik", "shree yantra"],
        "sacred_reason_bn": "শুক্রের কৃপা, প্রেম-দাম্পত্য সৌহার্দ্য, মোহিনী আকর্ষণ ও বিলাসিতার জন্য মহালক্ষ্মী বিহিত প্রতিকার।",
        "sacred_reason_hi": "शुक्र ग्रह की कृपा, दांपत्य प्रेम, आकर्षण एवं ऐश्वर्य प्राप्ति हेतु महालक्ष्मी विहित उपाय।",
        "sacred_reason_en": "Venusian resonance for love, marital bliss, luxury, and Goddess Mahalakshmi's bounty.",
    },
    "mercury": {
        "keywords": ["mercury", "budha", "4-mukhi", "emerald", "panna", "green aventurine"],
        "sacred_reason_bn": "বুধ গ্রহের প্রভাবে বুদ্ধিমত্তা, বাণিজ্য কৌশল, চতুর বাকপটুতা ও ত্বক-স্নায়ু রক্ষার শুভ প্রতিবিধান।",
        "sacred_reason_hi": "बुध ग्रह अनुकूलता, व्यापार वृद्धि, तार्किक बुद्धि एवं संचार क्षमता संवर्धन हेतु उपाय।",
        "sacred_reason_en": "Mercury empowerment for intellect, business acumen, communication, and sharp memory.",
    },
    "budh": {
        "keywords": ["mercury", "budha", "4-mukhi", "emerald", "panna", "green aventurine"],
        "sacred_reason_bn": "বুধ গ্রহের প্রভাবে বুদ্ধিমত্তা, বাণিজ্য কৌশল, চতুর বাকপটুতা ও ত্বক-স্নায়ু রক্ষার শুভ প্রতিবিধান।",
        "sacred_reason_hi": "बुध ग्रह अनुकूलता, व्यापार वृद्धि, तार्किक बुद्धि एवं संचार क्षमता संवर्धन हेतु उपाय।",
        "sacred_reason_en": "Mercury empowerment for intellect, business acumen, communication, and sharp memory.",
    },
    "rahu": {
        "keywords": ["rahu", "8-mukhi", "hessonite", "gomed", "silver coin"],
        "sacred_reason_bn": "রাহুর মায়াজাল, অনিদ্রা, অমূলক ভয়, কালসর্প দোষ ও আকস্মিক ক্ষতি রোধে শাস্ত্রীয় প্রতিবিধান।",
        "sacred_reason_hi": "राहु दोष, कालसर्प शांति, भ्रम निवारण एवं आकस्मिक संकटों से सुरक्षा हेतु सिद्ध उपाय।",
        "sacred_reason_en": "Rahu & Kaal Sarp pacification against psychic confusion, sudden losses, and fear.",
    },
    "ketu": {
        "keywords": ["ketu", "9-mukhi", "cats eye", "lehsuniya", "gomti chakra"],
        "sacred_reason_bn": "কেতুর শুভত্ব, মোক্ষ, দুর্ঘটনা রোধ ও গুপ্ত শত্রুর কুপ্রভাব থেকে মুক্তির জন্য পবিত্র প্রতিকার।",
        "sacred_reason_hi": "केतु शांति, मोक्ष, गुप्त शत्रुओं से रक्षा एवं दुर्घटना निवारण हेतु शास्त्रोक्त उपाय।",
        "sacred_reason_en": "Ketu empowerment for spiritual transcendence, occult protection, and safety.",
    },
}

DOSHA_REMEDY_MAP: dict[str, dict[str, Any]] = {
    "sade_sati": {
        "planet": "saturn",
        "keywords": ["shani", "7-mukhi", "blue sapphire", "horseshoe"],
        "reason_bn": "শনির সাড়ে সাতির তীব্র পর্যায় প্রশমনে বিশেষ কার্যকরী মহাশক্তি কবচ ও রুদ্রাক্ষ।",
        "reason_hi": "शनि की साढ़े साती के अशुभ प्रभावों को शांत करने हेतु विशेष सिद्ध कवच व रुद्राक्ष।",
        "reason_en": "Consecrated protection for neutralizing acute Saturn Sade Sati transit trials.",
    },
    "manglik": {
        "planet": "mars",
        "keywords": ["mangal", "3-mukhi", "coral", "moonga"],
        "reason_bn": "মাঙ্গলিক দোষ ও বিবাহ বিলম্বের বাধা খণ্ডন করতে প্রাণ-প্রতিষ্ঠিত প্রতিকার।",
        "reason_hi": "मांगलिक दोष निवारण एवं शीघ्र दांपत्य सुख प्राप्ति हेतु प्राण-प्रतिष्ठित उपाय।",
        "reason_en": "Sanctified remedy for breaking Manglik obstacles and marriage delays.",
    },
    "kaal_sarp": {
        "planet": "rahu",
        "keywords": ["8-mukhi", "9-mukhi", "rahu", "silver"],
        "reason_bn": "কালসর্প দোষের জটিল চক্রান্ত ও স্থবিরতা থেকে মুক্তি দিতে সিদ্ধ রুদ্রাক্ষ ও ধাতু প্রতিকার।",
        "reason_hi": "कालसर्प दोष शांति एवं जीवन में निरंतर प्रगति हेतु शास्त्रोक्त उपाय।",
        "reason_en": "Canonical remedy for transmuting Kaal Sarp Dosha into ascendant victory.",
    },
    "pitra_dosha": {
        "planet": "sun",
        "keywords": ["gomti chakra", "copper", "sun", "surya"],
        "reason_bn": "৮টি গোমতী চক্র ও তাম্রপাত্রের বিশেষ লাল কিতাব নিয়মে পিতৃপুরুষের আশীর্বাদ লাভ।",
        "reason_hi": "८ गोमती चक्र एवं ताम्र पात्र द्वारा पितृ शांति व पूर्वजों का दिव्य आशीर्वाद।",
        "reason_en": "Sacred 8 Gomti Chakra Lal Kitab protocol for ancestral peace and progeny harmony.",
    },
    "blocked_money": {
        "planet": "venus",
        "keywords": ["shree yantra", "gomti chakra", "lakshmi", "kuber"],
        "reason_bn": "আটকে থাকা অর্থ উদ্ধার, ঋণের বোঝা থেকে মুক্তি ও অক্ষয় লক্ষ্মী কৃপা লাভের মহাশক্তি মহাপ্রতিকার।",
        "reason_hi": "रुके हुए धन की वापसी, ऋण मुक्ति एवं अखंड लक्ष्मी कृपा प्राप्ति का महाउपाय।",
        "reason_en": "Consecrated Mahaupay for recovery of blocked funds and debt liberation.",
    },
}


def _map_product_to_rec(p: Product, sacred_reason: str | None = None) -> ShopProductRecommendationOut:
    return ShopProductRecommendationOut(
        id=str(p.id),
        title=p.title,
        slug=p.slug,
        sku=p.sku,
        short_description=p.short_description,
        sale_price=p.sale_price,
        mrp=p.mrp,
        discount_percent=p.discount_percent,
        featured_image=p.featured_image,
        category_slug=p.category_slug,
        category_type=p.category_type,
        ruling_planet=p.ruling_planet,
        deity=p.deity,
        in_stock=p.stock_quantity > 0,
        sacred_reason=sacred_reason,
        store_url=f"/shop/products/{p.slug}",
    )


# ===========================================================================
# Core Recommendation Query Engine
# ===========================================================================


async def get_shop_recommendations_for_astrology(
    planet: str | None = None,
    dosha: str | None = None,
    rashi: str | None = None,
    life_pillar: str | None = None,
    category_type: ProductCategoryType | None = None,
    lang: str = "bn",
    limit: int = 4,
) -> list[ShopProductRecommendationOut]:
    """Dynamically queries the active AstroStore catalog for remedies matching
    the user's astrological configuration or afflicted planetary positions.
    """
    filters: list[Any] = [
        Product.is_active == True,
        Product.is_deleted == False,
    ]

    sacred_reason = None
    target_keywords: list[str] = []

    # 1. Match Dosha first if provided
    if dosha and dosha.lower() in DOSHA_REMEDY_MAP:
        dosha_info = DOSHA_REMEDY_MAP[dosha.lower()]
        target_keywords.extend(dosha_info["keywords"])
        sacred_reason = (
            dosha_info.get(f"reason_{lang}")
            or dosha_info.get("reason_bn")
            or dosha_info.get("reason_en")
        )
        if not planet:
            planet = dosha_info.get("planet")

    # 2. Match Planet
    if planet:
        clean_planet = planet.lower().strip()
        planet_info = PLANET_REMEDY_MAP.get(clean_planet)
        if planet_info:
            target_keywords.extend(planet_info["keywords"])
            if not sacred_reason:
                sacred_reason = (
                    planet_info.get(f"sacred_reason_{lang}")
                    or planet_info.get("sacred_reason_bn")
                    or planet_info.get("sacred_reason_en")
                )

    if category_type:
        filters.append(Product.category_type == category_type)

    # Build smart OR filter
    or_clauses: list[Any] = []
    if planet:
        or_clauses.append(RegEx(Product.ruling_planet, f"^{planet}$", "i"))

    if rashi:
        or_clauses.append(RegEx(Product.recommended_for_rashis, f"^{rashi}$", "i"))

    if life_pillar:
        or_clauses.append(RegEx(Product.life_pillars, f"^{life_pillar}$", "i"))

    for kw in target_keywords[:4]:
        or_clauses.append({"title": {"$regex": kw, "$options": "i"}})
        or_clauses.append({"benefits": {"$regex": kw, "$options": "i"}})

    if or_clauses:
        filters.append({"$or": or_clauses})

    # Prioritize in-stock and featured items
    prods = (
        await Product.find(*filters)
        .sort("-stock_quantity", "-is_featured", "-average_rating")
        .limit(limit)
        .to_list()
    )

    # Fallback to featured active products if specific query was narrow
    if len(prods) < limit:
        fallback_prods = (
            await Product.find(
                Product.is_active == True,
                Product.is_deleted == False,
                Product.stock_quantity > 0,
            )
            .sort("-is_featured", "-created_at")
            .limit(limit - len(prods))
            .to_list()
        )
        existing_ids = {str(p.id) for p in prods}
        for fp in fallback_prods:
            if str(fp.id) not in existing_ids:
                prods.append(fp)

    return [_map_product_to_rec(p, sacred_reason) for p in prods[:limit]]


# ===========================================================================
# Synchronous Enricher for 1-Year Lal Kitab Varshphal Dossiers
# ===========================================================================


def enrich_curated_remedies_with_store_links(
    remedies: list[dict[str, Any]],
    lang: str = "bn",
) -> list[dict[str, Any]]:
    """Enriches generated Lal Kitab Varshphal remedies with authentic remedy
    upsell links matching each planet (Sun, Moon, Mars, etc.).
    """
    for r in remedies:
        p_name = r.get("planet_name", "").lower()
        # Find matching info
        info = None
        for key in PLANET_REMEDY_MAP:
            if key in p_name:
                info = PLANET_REMEDY_MAP[key]
                break

        r["store_remedy_query"] = {
            "planet": r.get("planet_name"),
            "category_type": "rudraksha" if "saturn" in p_name or "jupiter" in p_name else "gemstones",
            "sacred_intent": info.get(f"sacred_reason_{lang}", "") if info else "Authentic Consecrated Remedy",
            "explore_url": f"/shop?planet={r.get('planet_name')}",
        }

    return remedies


def build_varshphal_store_recommendations(
    varsh_planets: list[dict[str, Any]],
    primary_focus: str = "general",
    lang: str = "bn",
    max_items: int = 4,
) -> list[dict[str, Any]]:
    """Generates canonical, high-converting AstroStore remedy product recommendations
    specifically targeted to the seeker's afflicted planets and primary life focus.
    """
    CANONICAL_STORE_REMEDIES: dict[str, dict[str, Any]] = {
        "saturn": {
            "title_bn": "নেপালি ৭-মুখী রুদ্রাক্ষ (প্রাণ-প্রতিষ্ঠিত)",
            "title_hi": "नेपाली 7-मुखी रुद्राक्ष (प्राण-प्रतिष्ठित)",
            "title_en": "Nepali 7-Mukhi Rudraksha (Consecrated)",
            "category": "rudraksha",
            "ruling_planet": "Saturn",
            "planet_symbol": "♄",
            "reason_bn": "শনির সাড়ে সাতি, ধাইয়া ও কণ্টক শনির অশুভ প্রভাব প্রশমন এবং কর্মক্ষেত্রে আকস্মিক বাধা দূরীকরণে পরম ফলদায়ী।",
            "reason_hi": "शनि साढ़े साती, ढैय्या एवं करियर में आ रही अप्रत्याशित बाधाओं के निवारण हेतु सिद्ध उपाय।",
            "reason_en": "Essential consecrated remedy for Saturn Sade Sati, Kantaka Shani, and career stability.",
            "mrp": 3999,
            "sale_price": 1899,
            "discount_percent": 52,
            "badge_bn": "১০০% ল্যাব সার্টিফাইড ও মন্ত্রপূত প্রাণ-প্রতিষ্ঠিত",
            "badge_hi": "100% लैब प्रमाणित एवं प्राण-प्रतिष्ठित",
            "badge_en": "100% Lab Certified & Prana-Pratishtha Consecrated",
            "image": "https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?w=600&auto=format&fit=crop&q=80",
            "store_url": "/shop?planet=saturn",
        },
        "rahu": {
            "title_bn": "৪ গ্রাম নিরেট চৌকো রুপোর পাত ও ৮-মুখী রুদ্রাক্ষ কম্বো",
            "title_hi": "4 ग्राम ठोस चौकोर चांदी का टुकड़ा व 8-मुखी रुद्राक्ष",
            "title_en": "Solid Square Silver Piece & 8-Mukhi Rudraksha Combo",
            "category": "rudraksha",
            "ruling_planet": "Rahu",
            "planet_symbol": "☊",
            "reason_bn": "৮ম ও ১২শ ভাবে রাহুর কুপ্রভাব, মানসিক বিভ্রান্তি, আইনি জটিলতা ও আকস্মিক অর্থক্ষতি রোধে বিশুদ্ধ লাল কিতাব ক্যানন।",
            "reason_hi": "राहु दोष, मानसिक संशय, अनिद्रा एवं अचानक नुकसान से सुरक्षा हेतु शास्त्रीय लाल किताब उपाय।",
            "reason_en": "Authentic Lal Kitab remedy against Rahu transits, anxiety, and unforeseen crises.",
            "mrp": 2999,
            "sale_price": 1499,
            "discount_percent": 50,
            "badge_bn": "১০০% খাঁটি রুপো ও শাস্ত্রীয় শক্তিসম্পন্ন",
            "badge_hi": "100% शुद्ध चांदी एवं सिद्ध सामग्री",
            "badge_en": "100% Pure Silver & Consecrated",
            "image": "https://images.unsplash.com/photo-1611591475879-166258f33cf2?w=600&auto=format&fit=crop&q=80",
            "store_url": "/shop?planet=rahu",
        },
        "mars": {
            "title_bn": "ন্যাচারাল রক্তপ্রবাল (Red Coral) ও ৩-মুখী রুদ্রাক্ষ কবচ",
            "title_hi": "प्राकृतिक लाल मूंगा व 3-मुखी रुद्राक्ष कवच",
            "title_en": "Natural Certified Red Coral & 3-Mukhi Rudraksha Kavach",
            "category": "gemstones",
            "ruling_planet": "Mars",
            "planet_symbol": "♂",
            "reason_bn": "মাঙ্গলিক দোষ প্রশমন, রক্তপীড়া ও ভূমি-সম্পত্তি সংক্রান্ত সংকট নিরসনে দেব সেনাপতি মঙ্গলের বিহিত মহাপ্রতিকার।",
            "reason_hi": "मांगलिक दोष शांति, रक्त विकार व भूमि विवाद समाधान हेतु भौम महा-उपाय।",
            "reason_en": "Powerful Mars remedy for Manglik Dosha pacification, vitality, and property success.",
            "mrp": 4999,
            "sale_price": 2499,
            "discount_percent": 50,
            "badge_bn": "খাঁটি প্রাকৃতিক রক্তপ্রবাল ও গঙ্গাজলে শোধিত",
            "badge_hi": "प्रामाणिक इटैलियन मूंगा व अभिमंत्रित",
            "badge_en": "100% Natural Red Coral, Vedic Consecrated",
            "image": "https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?w=600&auto=format&fit=crop&q=80",
            "store_url": "/shop?planet=mars",
        },
        "jupiter": {
            "title_bn": "নেপালি ৫-মুখী রুদ্রাক্ষ ও কাঁচা হলুদের সিদ্ধ মালা",
            "title_hi": "नेपाली 5-मुखी रुद्राक्ष व हल्दी की सिद्ध माला",
            "title_en": "Nepali 5-Mukhi Rudraksha & Consecrated Turmeric Mala",
            "category": "rudraksha",
            "ruling_planet": "Jupiter",
            "planet_symbol": "♃",
            "reason_bn": "বৃহস্পতি গ্রহের শুভত্ব বৃদ্ধি, আধ্যাত্মিক জ্ঞান, উচ্চশিক্ষা, কন্যা সন্তান বা পুত্র সন্তানের কল্যাণ ও অর্থ সমৃদ্ধি।",
            "reason_hi": "गुरु ग्रह कृपा, संतान सुख, उच्च शिक्षा एवं धन-वैभव संवर्धन हेतु देवगुरु उपाय।",
            "reason_en": "Divine Jupiter blessing for wisdom, progeny well-being, and financial expansion.",
            "mrp": 2499,
            "sale_price": 1199,
            "discount_percent": 52,
            "badge_bn": "দেবগুরু বৃহস্পতি মন্ত্রে ১০৮ বার জপকৃত",
            "badge_hi": "गुरु मंत्र द्वारा 108 बार अभिमंत्रित",
            "badge_en": "Chanted 108 Times with Guru Beej Mantra",
            "image": "https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?w=600&auto=format&fit=crop&q=80",
            "store_url": "/shop?planet=jupiter",
        },
        "sun": {
            "title_bn": "তাম্র সূর্য যন্ত্র ও ১২-মুখী সূর্য রুদ্রাক্ষ",
            "title_hi": "ताम्र सूर्य यंत्र व 12-मुखी सूर्य रुद्राक्ष",
            "title_en": "Pure Copper Surya Yantra & 12-Mukhi Sun Rudraksha",
            "category": "yantra",
            "ruling_planet": "Sun",
            "planet_symbol": "☉",
            "reason_bn": "সরকারি চাকরি, পদোন্নতি, পিতৃসুখ, আত্মবিশ্বাস ও সমাজে উচ্চ সম্মান বৃদ্ধির জন্য রবি গ্রহের অব্যর্থ প্রতিকার।",
            "reason_hi": "सरकारी पद, मान-प्रतिष्ठा, पितृ दोष शांति एवं आत्मबल वृद्धि हेतु सूर्य उपाय।",
            "reason_en": "Vedic Sun empowerment for leadership, prestige, executive power, and vitality.",
            "mrp": 3299,
            "sale_price": 1599,
            "discount_percent": 51,
            "badge_bn": "১০০% বিশুদ্ধ তামা ও গায়ত্রী মন্ত্রে সিদ্ধ",
            "badge_hi": "शुद्ध तांबा व गायत्री मंत्र सिद्ध",
            "badge_en": "Pure Copper Consecrated with Gayatri Mantra",
            "image": "https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?w=600&auto=format&fit=crop&q=80",
            "store_url": "/shop?planet=sun",
        },
        "moon": {
            "title_bn": "২-মুখী রুদ্রাক্ষ ও প্রাকৃতিক স্ফটিক মালা",
            "title_hi": "2-मुखी रुद्राक्ष व प्राकृतिक स्फटिक माला",
            "title_en": "2-Mukhi Rudraksha & Pure Sphatik Mala",
            "category": "rudraksha",
            "ruling_planet": "Moon",
            "planet_symbol": "☽",
            "reason_bn": "অতিরিক্ত মানসিক উদ্বেগ, হতাশা, নিদ্রাহীনতা ও চন্দ্র দোষ প্রশমনে মনঃশান্তি প্রদানকারী মহাপ্রতিকার।",
            "reason_hi": "मानसिक अशांति, अवसाद एवं चंद्र दोष शांति हेतु शीतलता प्रदायक उपाय।",
            "reason_en": "Deep emotional tranquility and mother's blessings for fragile Moon transits.",
            "mrp": 2799,
            "sale_price": 1299,
            "discount_percent": 53,
            "badge_bn": "হিমালয়ান স্ফটিক ও হর-পার্বতী শক্তিসম্পন্ন",
            "badge_hi": "प्राकृतिक स्फटिक व शिव-शक्ति सिद्ध",
            "badge_en": "Natural Himalayan Sphatik & Shiva-Parvati Energized",
            "image": "https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?w=600&auto=format&fit=crop&q=80",
            "store_url": "/shop?planet=moon",
        },
        "gomti_chakra": {
            "title_bn": "৮টি অলৌকিক সিদ্ধ গোমতী চক্র ও কনসেক্রেটেড শ্রীকুবের কয়েন",
            "title_hi": "8 सिद्ध गोमती चक्र एवं अभिमंत्रित श्रीकुबेर सिक्का",
            "title_en": "8 Sacred Consecrated Gomti Chakra & Kuber Coin Set",
            "category": "gomti_chakra",
            "ruling_planet": "Jupiter & Lakshmi",
            "planet_symbol": "卐",
            "reason_bn": "আটকে থাকা টাকা আদায়, গৃহের বাস্তুদোষ নিবারণ ও ধনলক্ষ্মীর চিরস্থায়ী কৃপাপ্রাপ্তির জন্য অলৌকিক তন্ত্রোক্ত টোটকা।",
            "reason_hi": "अटका धन वापसी, वास्तु दोष निवारण एवं स्थायी लक्ष्मी कृपा हेतु चमत्कारी उपाय।",
            "reason_en": "Sacred miracle set for blocked money recovery, debt relief, and permanent wealth harmony.",
            "mrp": 2199,
            "sale_price": 999,
            "discount_percent": 55,
            "badge_bn": "নদীগর্ভের প্রাকৃতিক গোমতী চক্র • প্রাণ-প্রতিষ্ঠিত",
            "badge_hi": "प्राकृतिक गोमती चक्र • पूर्णतः अभिमंत्रित",
            "badge_en": "Natural River Bed Gomti Chakra • Consecrated",
            "image": "https://images.unsplash.com/photo-1611591475879-166258f33cf2?w=600&auto=format&fit=crop&q=80",
            "store_url": "/shop?category=gomti_chakra",
        },
    }

    # Sort afflicted planets (ashubh first, then mixed)
    afflicted_planets = [
        p["planet_id"].lower()
        for p in sorted(
            varsh_planets,
            key=lambda x: 0 if x.get("nature") == "ashubh" else 1 if x.get("nature") == "mixed" else 2,
        )
    ]

    selected: list[dict[str, Any]] = []
    seen_keys: set[str] = set()

    # 1. Add afflicted planets
    for p_id in afflicted_planets:
        if p_id in CANONICAL_STORE_REMEDIES and p_id not in seen_keys:
            r = CANONICAL_STORE_REMEDIES[p_id]
            selected.append({
                "id": f"rem-{p_id}",
                "title": r.get(f"title_{lang}") or r["title_en"],
                "category": r["category"],
                "ruling_planet": r["ruling_planet"],
                "planet_symbol": r["planet_symbol"],
                "sacred_reason": r.get(f"reason_{lang}") or r["reason_en"],
                "mrp": r["mrp"],
                "sale_price": r["sale_price"],
                "discount_percent": r["discount_percent"],
                "badge": r.get(f"badge_{lang}") or r["badge_en"],
                "image": r["image"],
                "store_url": r["store_url"],
            })
            seen_keys.add(p_id)
            if len(selected) >= max_items - 1:
                break

    # 2. Always include Gomti Chakra miracle set for wealth/problem resolution
    if "gomti_chakra" not in seen_keys and len(selected) < max_items:
        g = CANONICAL_STORE_REMEDIES["gomti_chakra"]
        selected.append({
            "id": "rem-gomti-chakra",
            "title": g.get(f"title_{lang}") or g["title_en"],
            "category": g["category"],
            "ruling_planet": g["ruling_planet"],
            "planet_symbol": g["planet_symbol"],
            "sacred_reason": g.get(f"reason_{lang}") or g["reason_en"],
            "mrp": g["mrp"],
            "sale_price": g["sale_price"],
            "discount_percent": g["discount_percent"],
            "badge": g.get(f"badge_{lang}") or g["badge_en"],
            "image": g["image"],
            "store_url": g["store_url"],
        })

    return selected[:max_items]


