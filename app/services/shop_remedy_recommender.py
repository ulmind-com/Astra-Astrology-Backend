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
