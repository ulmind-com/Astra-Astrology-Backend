"""100% In-House Daily Horoscope (দৈনিক রাশিফল) calculation service.

Calculated strictly using:
1. Swiss Ephemeris 2.10 (pyswisseph) astronomical sidereal positions (Lahiri Ayanamsha).
2. Classical Vedic Moon Transit (গোচর / Gochar) principles across the 12 Bhavas.
3. Client's Rashi classification rules (client_rules.py, rashi_rules.py, panchang.py).
4. ZERO third-party APIs. 100% accurate, private, and deterministic.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from loguru import logger

from app.schemas.astrology import (
    DailyHoroscopeRequest,
    DailyHoroscopeResponse,
    DailyPanchangSummary,
    DailySignHoroscope,
    HoraItem,
    PersonalizedNakshatraProfile,
    TaraBalaSummary,
    ChoghadiyaItem,
    PlanetaryDrishtiItem,
    PanchakStatus,
    AshtakavargaTransitPoints,
    NumerologyDailySynergy,
    BiorhythmHour,
    DualTransitInsight,
)
import app.services.astrology.client_rules as client_rules
from app.services.astrology.calculator import (
    EphemerisUnavailable,
    HAS_SWISSEPH,
    _require_swisseph,
    swe,
)
from app.services.astrology.nakshatra_rules import (
    NAKSHATRAS_MASTER,
    TARABALA_DEFINITIONS,
)
from app.services.astrology.panchang import (
    calculate_karana,
    calculate_tithi,
    calculate_yoga,
)
from app.services.astrology.rashi_rules import NAKSHATRAS_DATA, RASHIS_DATA

Lang = Literal["en", "bn", "hi"]

# -----------------------------------------------------------------------------
# 12 Rashi Metadata & Sanskrit Names
# -----------------------------------------------------------------------------
SIGN_NAMES_ORDERED = [
    {"en": "Aries", "bn": "মেষ", "hi": "मेष", "sa": "Mesha", "symbol": "♈", "lord": "Mars", "element": "Fire", "dir": "East"},
    {"en": "Taurus", "bn": "বৃষ", "hi": "वृष", "sa": "Vrishabha", "symbol": "♉", "lord": "Venus", "element": "Earth", "dir": "South"},
    {"en": "Gemini", "bn": "মিথুন", "hi": "मिथुन", "sa": "Mithuna", "symbol": "♊", "lord": "Mercury", "element": "Air", "dir": "West"},
    {"en": "Cancer", "bn": "কর্কট", "hi": "कर्क", "sa": "Karka", "symbol": "♋", "lord": "Moon", "element": "Water", "dir": "North"},
    {"en": "Leo", "bn": "সিংহ", "hi": "सिंह", "sa": "Simha", "symbol": "♌", "lord": "Sun", "element": "Fire", "dir": "East"},
    {"en": "Virgo", "bn": "কন্যা", "hi": "कन्या", "sa": "Kanya", "symbol": "♍", "lord": "Mercury", "element": "Earth", "dir": "South"},
    {"en": "Libra", "bn": "তুলা", "hi": "तुला", "sa": "Tula", "symbol": "♎", "lord": "Venus", "element": "Air", "dir": "West"},
    {"en": "Scorpio", "bn": "বৃশ্চিক", "hi": "वृश्चिक", "sa": "Vrishchika", "symbol": "♏", "lord": "Mars", "element": "Water", "dir": "North"},
    {"en": "Sagittarius", "bn": "ধনু", "hi": "धनु", "sa": "Dhanu", "symbol": "♐", "lord": "Jupiter", "element": "Fire", "dir": "East"},
    {"en": "Capricorn", "bn": "মকর", "hi": "मकर", "sa": "Makara", "symbol": "♑", "lord": "Saturn", "element": "Earth", "dir": "South"},
    {"en": "Aquarius", "bn": "কুম্ভ", "hi": "कुम्भ", "sa": "Kumbha", "symbol": "♒", "lord": "Saturn", "element": "Air", "dir": "West"},
    {"en": "Pisces", "bn": "মীন", "hi": "मीन", "sa": "Meena", "symbol": "♓", "lord": "Jupiter", "element": "Water", "dir": "North"},
]

VARA_INFO = [
    {"en": "Sunday", "bn": "রবিবার", "hi": "रविवार", "lord": "Sun", "rahu_period": (16.5, 18.0)},
    {"en": "Monday", "bn": "সোমবার", "hi": "सोमवार", "lord": "Moon", "rahu_period": (7.5, 9.0)},
    {"en": "Tuesday", "bn": "মঙ্গলবার", "hi": "मंगलवार", "lord": "Mars", "rahu_period": (15.0, 16.5)},
    {"en": "Wednesday", "bn": "বুধবার", "hi": "बुधवार", "lord": "Mercury", "rahu_period": (12.0, 13.5)},
    {"en": "Thursday", "bn": "বৃহস্পতিবার", "hi": "गुरुवार", "lord": "Jupiter", "rahu_period": (13.5, 15.0)},
    {"en": "Friday", "bn": "শুক্রবার", "hi": "शुक्रवार", "lord": "Venus", "rahu_period": (10.5, 12.0)},
    {"en": "Saturday", "bn": "শনিবার", "hi": "शनिवार", "lord": "Saturn", "rahu_period": (9.0, 10.5)},
]

# -----------------------------------------------------------------------------
# Classical Vedic Transit Predictions by House (1 to 12)
# -----------------------------------------------------------------------------
HOUSE_GOCHAR_TEMPLATES: dict[int, dict[str, dict[str, str]]] = {
    1: {
        "en": {
            "name": "1st House (Janma Rashi)",
            "verdict": "Self-Reflection & Vitality",
            "summary": "The Moon transits your Janma Rashi today. Your vitality and mental sensitivity are high. Direct your focus towards constructive initiatives and avoid impulsive hasty decisions.",
            "career": "Leadership initiative is rewarded. Good day for creative presentations, but avoid ego clashes with colleagues.",
            "love": "Emotional warmth in relationships. Express your feelings with sincerity and patience.",
            "finance": "Moderate day for money. Avoid spontaneous luxury shopping or emotional spending.",
            "health": "High mental energy; ensure adequate hydration and take short mindfulness breaks.",
        },
        "bn": {
            "name": "১ম ভাব (জন্ম রাশি)",
            "verdict": "আত্মবিশ্বাস ও মানসিক সংবেদনশীলতা",
            "summary": "চন্দ্র আজ আপনার রাশিতেই অবস্থান করছে। মানসিক সংবেদনশীলতা ও আত্মবল বৃদ্ধি পাবে। যেকোনো নতুন উদ্যোগে স্থির সিদ্ধান্ত নিন এবং হঠকারী রাগ পরিহার করুন।",
            "career": "কর্মক্ষেত্রে আপনার উদ্যম প্রশংসিত হবে। সহকর্মীদের সাথে শান্তভাবে কাজ করলে সাফল্য আসবে।",
            "love": "সম্পর্কে আন্তরিকতা বজায় থাকবে। সঙ্গীর মানসিক অনুভূতির মূল্যায়ন করুন।",
            "finance": "অর্থ ভাগ্য স্বাভাবিক। অহেতুক আবেগতাড়িত হয়ে অতিরিক্ত ব্যয় এড়িয়ে চলুন।",
            "health": "শারীরিক শক্তি ভালো থাকবে; প্রচুর জল পান করুন এবং মানসিক চাপমুক্ত থাকুন।",
        },
        "hi": {
            "name": "प्रथम भाव (जन्म राशि)",
            "verdict": "आत्मविश्वास और मानसिक सक्रियता",
            "summary": "चंद्रमा आज आपकी ही राशि में गोचर कर रहा है। आत्मविश्वास और संवेदनशीलता में वृद्धि होगी। रचनात्मक कार्यों में मन लगाएं और जल्दबाजी में निर्णय न लें।",
            "career": "कार्यक्षेत्र में आपकी पहल की सराहना होगी। सहयोगियों से तालमेल बनाकर रखें।",
            "love": "पारिवारिक रिश्तों में मधुरता रहेगी। साथी की भावनाओं का सम्मान करें।",
            "finance": "वित्तीय स्थिति सामान्य रहेगी। अनावश्यक खर्चों पर नियंत्रण रखें।",
            "health": "ऊर्जा का स्तर अच्छा रहेगा; समय पर भोजन और विश्राम करें।",
        },
    },
    2: {
        "en": {
            "name": "2nd House (Dhana Bhava)",
            "verdict": "Financial Focus & Family",
            "summary": "Moon transits your 2nd house of wealth and family. Financial calculations, family discussions, and sweet communication will bring fruitful results.",
            "career": "Excellent day for commercial negotiations, accounting, and closing sales discussions.",
            "love": "Harmonious family gatherings. Sweet and thoughtful words deepen emotional trust.",
            "finance": "Positive financial inflow. Past pending payments or family gains are indicated.",
            "health": "Care for throat and dietary habits; avoid excessively spicy or stale food.",
        },
        "bn": {
            "name": "২য় ভাব (ধন ও পরিবার ভাব)",
            "verdict": "আর্থিক সমৃদ্ধি ও পারিবারিক আলোচনা",
            "summary": "চন্দ্র আজ আপনার দ্বিতীয় ধন ভাবে অবস্থান করছে। পারিবারিক আলোচনা ও অর্থ সংক্রান্ত পরিকল্পনার জন্য দিনটি শুভ। মিষ্টি বাক্যালাপ লাভজনক ফলাফল দেবে।",
            "career": "বাণিজ্যিক লেনদেন ও হিসেব-নিকেশের কাজে শুভ ফল পাবেন। বসের সাথে ইতিবাচক আলোচনা হতে পারে।",
            "love": "পরিবারে আনন্দময় পরিবেশ বজায় থাকবে। প্রিয়জনের সাথে বোঝাপড়া মজবুত হবে।",
            "finance": "অর্থপ্রাপ্তির সম্ভাবনা রয়েছে। পাওনা টাকা আদায় হতে পারে।",
            "health": "গলা ও খাদ্যাভ্যাসের দিকে নজর দিন; অতিরিক্ত তেল-মশলাযুক্ত খাবার পরিহার করুন।",
        },
        "hi": {
            "name": "द्वितीय भाव (धन एवं कुटुंब)",
            "verdict": "आर्थिक लाभ और पारिवारिक सामंजस्य",
            "summary": "चंद्रमा आपके धन भाव में गोचर कर रहा है। वित्तीय योजना और पारिवारिक निर्णयों के लिए दिन उत्तम है। मीठी वाणी से कार्य सिद्ध होंगे।",
            "career": "व्यावसायिक बातचीत और लेन-देन में सफलता मिलेगी। कार्यशैली की प्रशंसा होगी।",
            "love": "पारिवारिक जीवन में सुख-शांति रहेगी। जीवनसाथी का सहयोग प्राप्त होगा।",
            "finance": "अचानक धन लाभ या रुका हुआ धन वापस मिलने के योग हैं।",
            "health": "खान-पान का विशेष ध्यान रखें; पर्याप्त नींद लें।",
        },
    },
    3: {
        "en": {
            "name": "3rd House (Parakrama Bhava)",
            "verdict": "High Courage & Success (Shubha Gochar)",
            "summary": "Moon transits the 3rd house of courage and initiatives. A highly auspicious transit bringing valor, support from associates, and success in short travels.",
            "career": "Dynamic momentum at work. New contracts, client outreach, and teamwork yield breakthroughs.",
            "love": "Playful and supportive interactions with partners and younger siblings.",
            "finance": "Gains through communication, trade, and media ventures. Wise investments flourish.",
            "health": "High physical stamina and mental optimism; great day for fitness or outdoor work.",
        },
        "bn": {
            "name": "৩য় ভাব (পরাক্রম ও সাহস ভাব - অতি শুভ গোচর)",
            "verdict": "অদম্য সাহস ও সর্বক্ষেত্রে সাফল্য",
            "summary": "চন্দ্র আজ তৃতীয় পরাক্রম ভাবে অবস্থান করছে। এটি অত্যন্ত শুভ গোচর। আপনার আত্মবিশ্বাস বৃদ্ধি পাবে, অনুজ ও বন্ধুদের সহায়তা পাবেন এবং যোগাযোগে বড় সাফল্য আসবে।",
            "career": "কর্মক্ষেত্রে প্রবল অগ্রগতি ও নতুন প্রকল্পের সুযোগ আসবে। দলগত কাজে বিশেষ সাফল্য লাভ করবেন।",
            "love": "সঙ্গীর সাথে সম্পর্কের দূরত্ব ঘুচে যাবে। ভ্রমণ বা মনোরম সময় কাটানোর সুযোগ হতে পারে।",
            "finance": "যোগাযোগ ও ব্যবসার মাধ্যমে আর্থিক লাভ নিশ্চিত হবে। নতুন বিনিয়োগে শুভ ফল।",
            "health": "শারীরিক উদ্যম চমৎকার থাকবে; মন প্রফুল্ল ও ইতিবাচক থাকবে।",
        },
        "hi": {
            "name": "तृतीय भाव (पराक्रम एवं पुरुषार्थ - शुभ गोचर)",
            "verdict": "साहस और सफलता का दिन",
            "summary": "चंद्रमा तीसरे भाव में गोचर कर रहा है, जो अत्यंत शुभ है। आत्मविश्वास और पराक्रम में वृद्धि होगी। मित्रों और सहयोगियों से पूरा सहयोग मिलेगा।",
            "career": "कार्यों में गति आएगी। नई योजनाओं और अनुबंधों के लिए दिन बहुत अनुकूल है।",
            "love": "प्रेम संबंधों में मधुरता और आपसी विश्वास बढ़ेगा।",
            "finance": "व्यापार और संचार माध्यमों से लाभ के नए अवसर प्राप्त होंगे।",
            "health": "स्वास्थ्य उत्तम रहेगा; मानसिक ताजगी और स्फूर्ति बनी रहेगी।",
        },
    },
    4: {
        "en": {
            "name": "4th House (Sukha Bhava)",
            "verdict": "Domestic Affairs & Emotional Care",
            "summary": "Moon transits your 4th house of home, mother, and mental peace. Emotional sensitivity is elevated; prioritize domestic comfort and avoid unnecessary mental overthinking.",
            "career": "Maintain focus on routine tasks. Postpone critical real estate or heavy asset purchases.",
            "love": "Seek solace in your home sanctuary. Listen with empathy to family members.",
            "finance": "Keep a steady hand on household expenses. Avoid impulsive home decor spending.",
            "health": "Restful sleep and soothing music or meditation are recommended to relax the mind.",
        },
        "bn": {
            "name": "৪র্থ ভাব (সুখ ও মানসিক শান্তি ভাব)",
            "verdict": "গৃহস্থালী ও মানসিক ভারসাম্যের প্রতি যত্ন",
            "summary": "চন্দ্র আজ চতুর্থ সুখ ভাবে অবস্থান করছে। মানসিক সংবেদনশীলতা একটু বেশি থাকতে পারে। পারিবারিক বিষয়ে ধৈর্য ধরুন এবং অতিরিক্ত দুশ্চিন্তা এড়িয়ে চলুন।",
            "career": "কর্মক্ষেত্রে দৈনন্দিন রুটিন মেনে চলুন। বড় কোনো রদবদল বা জমি-বাড়ির সিদ্ধান্ত ধীরেসুস্থে নিন।",
            "love": "গৃহপরিবেশে প্রিয়জনের সাথে সময় কাটান। মায়ের আশীর্বাদ ও পরামর্শে শান্তি মিলবে।",
            "finance": "গার্হস্থ্য কাজে কিছু ব্যয় হতে পারে। আয়ের সাথে ব্যয়ের ভারসাম্য বজায় রাখুন।",
            "health": "পর্যাপ্ত বিশ্রাম নিন; মানসিক প্রশান্তির জন্য ধ্যান বা হালকা হাঁটা উপকারী।",
        },
        "hi": {
            "name": "चतुर्थ भाव (सुख एवं माता भाव)",
            "verdict": "पारिवारिक शांति और मानसिक संतुलन",
            "summary": "चंद्रमा चौथे भाव में गोचर कर रहा है। मन में कुछ भावुकता रह सकती है। घरेलू मामलों में धैर्य रखें और सकारात्मक दृष्टिकोण अपनाएं।",
            "career": "कार्यक्षेत्र में सामान्य गति से कार्य करें। किसी विवाद में पड़ने से बचें।",
            "love": "परिजनों और जीवनसाथी के साथ समय बिताने से मन शांत रहेगा।",
            "finance": "घरेलू आवश्यकताओं पर व्यय हो सकता है। बजट का ध्यान रखें।",
            "health": "मानसिक शांति के लिए प्राणायाम और ध्यान करें; पर्याप्त नींद लें।",
        },
    },
    5: {
        "en": {
            "name": "5th House (Putra & Buddhi)",
            "verdict": "Creativity, Intellect & Romance",
            "summary": "Moon transits your 5th house of intelligence, children, and romance. A vibrant day for strategic problem-solving, intellectual pursuits, and heartfelt romance.",
            "career": "Creative innovations and analytical strategy set you apart. Great for examinations and design.",
            "love": "Sparkling romantic chemistry. Joyful conversations bring partners closer.",
            "finance": "Calculated investments look promising. Rely on disciplined analysis rather than pure luck.",
            "health": "Good digestive vitality; engage in hobbies or arts that bring pure joy.",
        },
        "bn": {
            "name": "৫ম ভাব (বুদ্ধি, সন্তান ও প্রেম ভাব)",
            "verdict": "সৃজনশীল প্রতিভা ও রোমান্টিক আনন্দ",
            "summary": "চন্দ্র আজ পঞ্চম বুদ্ধি ও জ্ঞান ভাবে অবস্থান করছে। সৃজনশীল চিন্তা ও কৌশলগত কাজে বিশেষ অগ্রগতি হবে। বুদ্ধিমত্তার প্রয়োগে জটিল সমস্যা সমাধান হবে।",
            "career": "কর্মে অভিনব আইডিয়া প্রশংসিত হবে। পড়াশোনা, গবেষণা ও আইটি কাজে চমৎকার দিন।",
            "love": "দাম্পত্য ও প্রণয় সম্পর্কে রোমাঞ্চকর আনন্দ থাকবে। সঙ্গীর মুখে হাসি ফুটবে।",
            "finance": "বুদ্ধিদীপ্ত পরিকল্পনায় অর্থ লাভ। ঝুঁকিপূর্ণ ফাটকা এড়িয়ে বিশ্লেষণধর্মী বিনিয়োগ করুন।",
            "health": "হৃদয় ও পেটের যত্ন নিন; পছন্দের সৃজনশীল কাজে মন রাখুন।",
        },
        "hi": {
            "name": "पंचम भाव (बुद्धि, संतान एवं प्रेम)",
            "verdict": "रचनात्मकता और बौद्धिक सफलता",
            "summary": "चंद्रमा पंचम भाव में गोचर कर रहा है। आपकी बुद्धि और रचनात्मकता चरम पर रहेगी। निर्णय लेने में आपकी दूरदर्शिता लाभकारी सिद्ध होगी।",
            "career": "नई योजनाओं और रणनीतियों में सफलता मिलेगी। विद्यार्थियों और शोधकर्ताओं के लिए उत्तम दिन है।",
            "love": "प्रेम संबंधों में प्रगाढ़ता आएगी। साथी के साथ मधुर समय बीतेगा।",
            "finance": "वित्तीय स्थिति मजबूत होगी। समझदारी से किए गए निवेश लाभ देंगे।",
            "health": "स्वास्थ्य अच्छा रहेगा; मन में उत्साह और प्रसन्नता बनी रहेगी।",
        },
    },
    6: {
        "en": {
            "name": "6th House (Ripu & Roga - Shubha Gochar)",
            "verdict": "Victory Over Hurdles & Efficiency",
            "summary": "Moon in the 6th house brings classical victory over obstacles (Shatru Vijaya). Your analytical discipline and competitive resilience defeat difficulties.",
            "career": "Exceptional productivity. You solve pending backlogs and win over professional rivals.",
            "love": "Pragmatic support between partners. Practical teamwork strengthens the bond.",
            "finance": "Recovery of debts and resolution of disputed bills. Prudent budgeting wins.",
            "health": "Health regimen shows improvement. Beneficial day to begin a disciplined detox or workout.",
        },
        "bn": {
            "name": "৬ষ্ঠ ভাব (শত্রু ও রোগ জয় ভাব - শুভ গোচর)",
            "verdict": "বাধা দূরীকরণ ও কর্মদক্ষতা",
            "summary": "চন্দ্র আজ ষষ্ঠ শত্রু ও বাধা জয়ী ভাবে অবস্থান করছে। বৈদিক শাস্ত্রে এটি অতি শুভ গোচর। কর্মক্ষেত্রে প্রতিদ্বন্দ্বীদের উপর জয়লাভ করবেন এবং পুরনো সমস্যা মিটে যাবে।",
            "career": "কাজে দারুণ কর্মদক্ষতা দেখাবেন। বকেয়া কাজ শেষ হবে এবং দায়িত্ব সফলভাবে পালন করবেন।",
            "love": "সম্পর্কে পারস্পরিক সহযোগিতার মনোভাব বজায় থাকবে। বাস্তববাদী চিন্তায় বন্ধন দৃঢ় হবে।",
            "finance": "ঋণমুক্তি বা আটকে থাকা অর্থ প্রাপ্তির সম্ভাবনা। হিসেব বজায় রাখলে সঞ্চয় বাড়বে।",
            "health": "পুরনো কোনো শারীরিক অস্বস্তি থেকে উপশম মিলবে। যোগব্যায়ামে শুভ ফল।",
        },
        "hi": {
            "name": "षष्ठ भाव (शत्रु एवं रोग विजय - शुभ गोचर)",
            "verdict": "बाधाओं पर विजय और कार्यकुशलता",
            "summary": "चंद्रमा छठे भाव में गोचर कर रहा है, जो अत्यंत फलदायी है। विरोधियों पर विजय मिलेगी और पुरानी समस्याओं का समाधान होगा।",
            "career": "कार्यक्षेत्र में आपकी कार्यकुशलता की प्रशंसा होगी। रुके हुए कार्य पूरे होंगे।",
            "love": "जीवनसाथी का व्यावहारिक सहयोग मिलेगा। मतभेद दूर होंगे।",
            "finance": "कर्ज से मुक्ति और रुके हुए धन की प्राप्ति के शुभ योग हैं।",
            "health": "स्वास्थ्य में सुधार होगा; पुरानी व्याधियों से राहत मिलेगी।",
        },
    },
    7: {
        "en": {
            "name": "7th House (Kalatra & Partnership)",
            "verdict": "Harmony, Public Dealings & Union",
            "summary": "Moon in the 7th house brings social charm, public rapport, and marital harmony. Collaborative partnerships flourish under this bright transit.",
            "career": "Outstanding day for client negotiations, business partnerships, and public PR.",
            "love": "Deep romantic harmony and mutual admiration. Excellent for marriage discussions.",
            "finance": "Joint ventures and spousal fortunes bring favorable financial stability.",
            "health": "Feelings of lightness and radiance; maintain balance in work and leisure.",
        },
        "bn": {
            "name": "৭ম ভাব (দাম্পত্য ও অংশীদারি ভাব - শুভ গোচর)",
            "verdict": "দাম্পত্য সুখ ও ব্যবসায়িক অংশীদারিত্ব",
            "summary": "চন্দ্র আজ সপ্তম জায়া ও অংশীদারি ভাবে অবস্থান করছে। সামাজিক গ্রহণযোগ্যতা বৃদ্ধি পাবে এবং দাম্পত্য জীবনে পারস্পরিক সৌহার্দ্য ও আনন্দ বজায় থাকবে।",
            "career": "ব্যবসায়িক অংশীদার ও ক্লায়েন্টদের সাথে ফলপ্রসূ চুক্তি হতে পারে। অংশীদারি কাজে লাভ।",
            "love": "দাম্পত্যে মধুর সম্প্রীতি। অবিবাহিতদের বিবাহের পাকা কথা এগোতে পারে।",
            "finance": "যৌথ ব্যবসা বা অংশীদারিত্বের মাধ্যমে আর্থিক মুনাফার শুভ যোগ।",
            "health": "শারীরিক ও মানসিক প্রশান্তি বজায় থাকবে; সুষম খাবার গ্রহণ করুন।",
        },
        "hi": {
            "name": "सप्तम भाव (दाम्पत्य एवं साझेदारी - शुभ गोचर)",
            "verdict": "दाम्पत्य सुख और व्यापारिक सफलता",
            "summary": "चंद्रमा सप्तम भाव में गोचर कर रहा है। सामाजिक मान-सम्मान और साझेदारी के कार्यों में उत्तम सफलता मिलेगी।",
            "career": "व्यापार में नए साझेदार और बड़े ग्राहकों से लाभ होगा। सार्वजनिक संबंध सुधरेंगे।",
            "love": "दाम्पत्य जीवन में प्रेम और सामंजस्य बढ़ेगा। अविवाहितों के रिश्ते तय हो सकते हैं।",
            "finance": "व्यापारिक यात्राओं और साझेदारों के माध्यम से धन लाभ होगा।",
            "health": "स्वास्थ्य उत्तम रहेगा; चेहरे पर तेज और मन में उत्साह रहेगा।",
        },
    },
    8: {
        "en": {
            "name": "8th House (Ashtama Chandra)",
            "verdict": "Caution, Deep Research & Mindfulness",
            "summary": "Moon transits your 8th house (Ashtama Chandra). Practice discretion, avoid unnecessary arguments, postpone high-risk gambles, and focus on inner meditation.",
            "career": "Stick to documented facts and quiet research. Avoid confrontation with managers.",
            "love": "Practice patience and emotional empathy. Avoid raising sensitive past grievances.",
            "finance": "Guard against sudden unexpected expenditures. Keep personal credentials secure.",
            "health": "Prioritize mental calm; avoid over-exhaustion, driving in haste, or skipping meals.",
        },
        "bn": {
            "name": "৮ম ভাব (অষ্টম চন্দ্র - সতর্ক গোচর)",
            "verdict": "সতর্কতা, ধৈর্য ও আত্মানুসন্ধান",
            "summary": "চন্দ্র আজ অষ্টম ঘরে (অষ্টম চন্দ্র) অবস্থান করছে। বৈদিক নিয়মে এই সময় তাড়াহুড়ো না করে শান্ত ও সতর্ক থাকা শ্রেয়। বিতর্ক এড়িয়ে ধ্যান ও গবেষণায় মন দিন।",
            "career": "কর্মক্ষেত্রে অতিরিক্ত ঝুঁকি নেবেন না। নথিপত্র সতর্কতার সাথে যাচাই করে স্বাক্ষর করুন।",
            "love": "সঙ্গীর সাথে কথা বলার সময় সংবেদনশীল হোন। পুরনো অপ্রিয় কথা তোলা থেকে বিরত থাকুন।",
            "finance": "হঠাৎ অপ্রত্যাশিত খরচ দেখা দিতে পারে। ঋণ দেওয়া বা নেওয়া থেকে বিরত থাকুন।",
            "health": "যানবাহন চালানোর সময় সাবধানতা অবলম্বন করুন; অতিরিক্ত মানসিক চাপ পরিহার করুন।",
        },
        "hi": {
            "name": "अष्टम भाव (अष्टम चंद्रमा - सावधानी का दिन)",
            "verdict": "धैर्य, शोध और सावधानी आवश्यक",
            "summary": "चंद्रमा अष्टम भाव में गोचर कर रहा है। आज के दिन सतर्कता और संयम बरतना अत्यंत आवश्यक है। वाद-विवाद से बचें और शांति बनाए रखें।",
            "career": "कार्यों में जल्दबाजी न करें। वरिष्ठ अधिकारियों से बातचीत में सावधानी बरतें।",
            "love": "रिश्तों में गलतफहमी से बचें। धैर्यपूर्वक साथी की बात सुनें।",
            "finance": "जोखिम भरे निवेश से बचें और अनावश्यक खर्चों पर रोक लगाएं।",
            "health": "वाहन सावधानी से चलाएं और मानसिक तनाव से दूर रहने के लिए ध्यान करें।",
        },
    },
    9: {
        "en": {
            "name": "9th House (Bhagya & Dharma)",
            "verdict": "Fortune, Higher Wisdom & Grace",
            "summary": "Moon in the 9th house of fortune (Bhagya) elevates spiritual clarity, brings blessings from mentors, and turns favorable tides in long-term goals.",
            "career": "Fortunate support from mentors and supervisors. Excellent day for publishing and law.",
            "love": "Shared spiritual values and intellectual conversations inspire deep bonding.",
            "finance": "Favorable fortune brings long-term wealth growth. Wise investments flourish.",
            "health": "Optimistic mental outlook promotes restorative healing and physical vitality.",
        },
        "bn": {
            "name": "৯ম ভাব (ভাগ্য ও ধর্ম ভাব - পরম শুভ গোচর)",
            "verdict": "ভাগ্যোন্নতি, গুরুকৃপা ও আধ্যাত্মিক শুভফল",
            "summary": "চন্দ্র আজ নবম ভাগ্য ভাবে অবস্থান করছে। এটি পরম শুভ গোচর। ভাগ্য আপনার সহায় হবে, গুরুজনদের আশীর্বাদ লাভ করবেন এবং দীর্ঘমেয়াদী পরিকল্পনায় সাফল্য আসবে।",
            "career": "উচ্চপদস্থ কর্মকর্তাদের সমর্থন পাবেন। নতুন সুযোগের দ্বার উন্মুক্ত হবে।",
            "love": "সম্পর্কে আধ্যাত্মিক প্রশান্তি ও পারস্পরিক শ্রদ্ধা বৃদ্ধি পাবে। শুভ ভ্রমণ হতে পারে।",
            "finance": "ভাগ্যের অনুকূলতায় আর্থিক সমৃদ্ধি ঘটবে। পূর্বে আটকে থাকা অর্থ পেতে পারেন।",
            "health": "মন শান্ত ও আনন্দিত থাকবে; স্বাস্থ্য সবল ও ইতিবাচক থাকবে।",
        },
        "hi": {
            "name": "नवम भाव (भाग्य एवं धर्म - अत्यंत शुभ गोचर)",
            "verdict": "भाग्योदय और आध्यात्मिक उन्नति",
            "summary": "चंद्रमा नवम भाव में गोचर कर रहा है, जिससे भाग्य का पूरा साथ मिलेगा। धार्मिक और मांगलिक कार्यों में रुचि बढ़ेगी। वरिष्ठों का आशीर्वाद प्राप्त होगा।",
            "career": "कार्यक्षेत्र में प्रतिष्ठा और प्रभाव बढ़ेगा। नई उपलब्धियों के योग बन रहे हैं।",
            "love": "पारस्परिक विश्वास और आत्मीयता में वृद्धि होगी। तीर्थ यात्रा का योग बन सकता है।",
            "finance": "आर्थिक दृष्टि से दिन अत्यंत लाभकारी है। रुके हुए कार्य भाग्यवश पूर्ण होंगे।",
            "health": "स्वास्थ्य उत्तम रहेगा; मन में शांति और संतोष का अनुभव होगा।",
        },
    },
    10: {
        "en": {
            "name": "10th House (Karma Bhava - Auspicious)",
            "verdict": "Career Triumph & Authority",
            "summary": "Moon illuminates your 10th house of career and professional status. Superior performance, executive recognition, and authority shine today.",
            "career": "Stellar achievements at work. Superiors notice your dedication and reward excellence.",
            "love": "Partner respects your professional drive. Balanced time together brings mutual pride.",
            "finance": "Strong professional earnings and commercial gains. Strategic decisions pay off.",
            "health": "High stamina, but avoid skipping lunch due to busy executive schedules.",
        },
        "bn": {
            "name": "১০ম ভাব (কর্ম ভাব - অতি শুভ গোচর)",
            "verdict": "কর্মসাফল্য, প্রতিপত্তি ও সম্মান",
            "summary": "চন্দ্র আজ দশম কর্ম ভাবে অবস্থান করছে। কর্মক্ষেত্রে আপনার কর্তৃত্ব ও সম্মান বৃদ্ধি পাবে। ঊর্ধ্বতন কর্তৃপক্ষের সহযোগিতা পাবেন এবং কর্মক্ষেত্রে বড় সাফল্য অর্জিত হবে।",
            "career": "পেশাগত জীবনে দারুণ সম্মান ও পদোন্নতির অনুকূল পরিবেশ তৈরি হবে। নতুন প্রজেক্ট সফল হবে।",
            "love": "আপনার কর্মনিষ্ঠা সঙ্গীকে অনুপ্রাণিত করবে। পরিবারে আপনার মর্যাদা বৃদ্ধি পাবে।",
            "finance": "কাজের সূত্রে আর্থিক লাভ ও সম্মানীয় ইনকাম বৃদ্ধি পাবে। ব্যবসা সম্প্রসারণের সুযোগ।",
            "health": "কাজের চাপে খাওয়া-দাওয়ায় অনিয়ম করবেন না; শারীরিক শক্তি অটুট থাকবে।",
        },
        "hi": {
            "name": "दशम भाव (कर्म एवं यश - अत्यंत शुभ गोचर)",
            "verdict": "कार्यक्षेत्र में सफलता और मान-सम्मान",
            "summary": "चंद्रमा दशम भाव में गोचर कर रहा है। कार्यक्षेत्र में आपके वर्चस्व और सम्मान में वृद्धि होगी। उच्च अधिकारियों का पूर्ण सहयोग प्राप्त होगा।",
            "career": "पदोन्नति और नई जिम्मेदारियां मिलने के प्रबल योग हैं। व्यावसायिक योजनाएं सफल होंगी।",
            "love": "पारिवारिक प्रतिष्ठा में वृद्धि होगी। जीवनसाथी आपकी सफलता पर गर्व करेगा।",
            "finance": "आर्थिक लाभ और व्यापारिक विस्तार के उत्तम अवसर मिलेंगे।",
            "health": "स्वास्थ्य अच्छा रहेगा; कार्यव्यस्तता के बीच भी स्फूर्ति बनी रहेगी।",
        },
    },
    11: {
        "en": {
            "name": "11th House (Labha Bhava - Supreme)",
            "verdict": "Highest Gains, Wealth & Fulfilment",
            "summary": "Moon in the 11th house of gains (Labha) is the supreme transit in classical Vedic astrology. Incoming profits, fulfillment of wishes, and influential networking prevail.",
            "career": "Projects complete successfully with outstanding applause. Great day for team bonuses.",
            "love": "Social circles and romantic friendships bring immense happiness and shared laughter.",
            "finance": "Peak financial inflow. Multiple income channels open and profits exceed projections.",
            "health": "Vibrant vitality and mental cheer; feel revitalized and enthusiastic.",
        },
        "bn": {
            "name": "১১শ ভাব (লাভ ভাব - সর্বশ্রেষ্ঠ শুভ গোচর)",
            "verdict": "সর্বাধিক লাভ, অর্থাগমন ও ইচ্ছা পূরণ",
            "summary": "চন্দ্র আজ একাদশ লাভ ভাবে অবস্থান করছে। বৈদিক জ্যোতিষ অনুযায়ী এটি সর্বশ্রেষ্ঠ শুভ গোচর। মনের ইচ্ছা পূরণ হবে, বন্ধুদের সহায়তা পাবেন এবং আর্থিক মুনাফা তুঙ্গে থাকবে।",
            "career": "প্রকল্পের আশাতীত সাফল্য ও কর্মক্ষেত্রে সবার সাথে সৌহার্দ্যপূর্ণ লাভজনক সম্পর্ক তৈরি হবে।",
            "love": "সামাজিক মেলামেশা ও প্রণয় সম্পর্কের দারুণ সুন্দর সময়। বন্ধুদের মাধ্যমে শুভ যোগাযোগ।",
            "finance": "চমৎকার অর্থপ্রাপ্তি। একাধিক উৎস থেকে অর্থ আসার সম্ভাবনা ও ব্যবসায় বিপুল লাভ।",
            "health": "দেহ ও মন অত্যন্ত প্রফুল্ল থাকবে; শারীরিক সক্ষমতা তুঙ্গে থাকবে।",
        },
        "hi": {
            "name": "एकादश भाव (लाभ एवं आय - सर्वश्रेष्ठ गोचर)",
            "verdict": "प्रचुर धन लाभ और मनोकामना सिद्धि",
            "summary": "चंद्रमा एकादश भाव में गोचर कर रहा है, जो सभी गोचरों में सर्वश्रेष्ठ माना जाता है। सभी इच्छाएं पूर्ण होंगी और आय के नए स्रोत बनेंगे।",
            "career": "व्यापार और नौकरी में अभूतपूर्व सफलता मिलेगी। वरिष्ठों और मित्रों का पूरा सहयोग रहेगा।",
            "love": "सामाजिक और पारिवारिक जीवन में उत्सव जैसा माहौल रहेगा। प्रेम संबंध मजबूत होंगे।",
            "finance": "धन आगमन के प्रबल योग हैं। आर्थिक स्थिति अत्यंत सुदृढ़ होगी।",
            "health": "स्वास्थ्य उत्तम और ऊर्जावान रहेगा; मानसिक प्रसन्नता बनी रहेगी।",
        },
    },
    12: {
        "en": {
            "name": "12th House (Vyaya Bhava)",
            "verdict": "Foreign Ventures, Expenditures & Rest",
            "summary": "Moon transits your 12th house of expenditures, foreign affairs, and subconscious rest. Manage spending prudently, avoid late-night stress, and pursue spiritual reflection.",
            "career": "Good for overseas clients, multinational liaison, and solitary creative writing.",
            "love": "Cherish quiet, intimate moments together away from external distractions.",
            "finance": "Keep a careful watch on expenses; direct funds toward charitable or spiritual deeds.",
            "health": "Prioritize restful sleep and reduce screen exposure before bedtime.",
        },
        "bn": {
            "name": "১২শ ভাব (ব্যয় ও বিদেশ ভাব)",
            "verdict": "ব্যয় নিয়ন্ত্রণ, আত্মবিশ্লেষণ ও আধ্যাত্মিক বিশ্রাম",
            "summary": "চন্দ্র আজ দ্বাদশ ব্যয় ও মোক্ষ ভাবে অবস্থান করছে। দূরপাল্লার যোগাযোগ বা বিদেশ সংক্রান্ত বিষয়ে লাভ হলেও ব্যয়ের দিকে সতর্ক নজর দেওয়া প্রয়োজন। পর্যাপ্ত ঘুম ও বিশ্রাম নিন।",
            "career": "আন্তর্জাতিক ক্লায়েন্ট বা দূরবর্তী কাজের সাথে যুক্তদের জন্য শুভ। শান্তভাবে কাজ করুন।",
            "love": "শান্ত ও নিরিবিলি পরিবেশে সঙ্গীর সাথে সময় কাটান। অপ্রয়োজনীয় ভুল বোঝাবুঝি এড়িয়ে চলুন।",
            "finance": "হঠাৎ বাড়তি ব্যয়ের সম্ভাবনা রয়েছে; বাজেট কঠোরভাবে নিয়ন্ত্রণ করুন এবং সৎকাজে দান করুন।",
            "health": "চোখ ও ঘুমের দিকে নজর দিন; রাতে ঘুমানোর আগে মোবাইল বা স্ক্রিনের ব্যবহার কমান।",
        },
        "hi": {
            "name": "द्वादश भाव (व्यय एवं विदेश भाव)",
            "verdict": "व्यय नियंत्रण और आध्यात्मिक विश्राम",
            "summary": "चंद्रमा द्वादश भाव में गोचर कर रहा है। आज खर्चों पर नियंत्रण रखना आवश्यक है। विदेश या दूरस्थ स्थानों से जुड़े कार्यों में लाभ के संकेत हैं।",
            "career": "गुप्त शत्रुओं से सतर्क रहें। अपने कार्य में एकाग्रता बनाए रखें।",
            "love": "साथी के साथ धैर्य और समझदारी से पेश आएं। शांतिपूर्ण वार्तालाप हितकर रहेगा।",
            "finance": "अचानक खर्चे बढ़ सकते हैं, इसलिए वित्तीय अनुशासन बनाए रखें।",
            "health": "पर्याप्त नींद लें और आंखों की देखभाल करें; योग-ध्यान से मानसिक शांति मिलेगी।",
        },
    },
}

# Base Scores by Transit House (1 to 12)
HOUSE_BASE_SCORES: dict[int, dict[str, int]] = {
    1: {"overall": 76, "career": 78, "love": 72, "finance": 70, "health": 82},
    2: {"overall": 78, "career": 75, "love": 74, "finance": 88, "health": 72},
    3: {"overall": 88, "career": 90, "love": 82, "finance": 86, "health": 88},
    4: {"overall": 66, "career": 68, "love": 70, "finance": 65, "health": 64},
    5: {"overall": 84, "career": 85, "love": 90, "finance": 80, "health": 82},
    6: {"overall": 86, "career": 88, "love": 76, "finance": 85, "health": 86},
    7: {"overall": 85, "career": 82, "love": 92, "finance": 80, "health": 84},
    8: {"overall": 58, "career": 60, "love": 56, "finance": 52, "health": 55},
    9: {"overall": 90, "career": 88, "love": 86, "finance": 92, "health": 88},
    10: {"overall": 92, "career": 96, "love": 82, "finance": 90, "health": 88},
    11: {"overall": 96, "career": 94, "love": 90, "finance": 98, "health": 92},
    12: {"overall": 62, "career": 66, "love": 62, "finance": 54, "health": 60},
}


def _calculate_julian_day(date_obj: datetime, hour_utc: float) -> float:
    """Computes exact Julian Day using Swiss Ephemeris."""
    return float(swe.julday(date_obj.year, date_obj.month, date_obj.day, hour_utc))


# -----------------------------------------------------------------------------
# Classical Vedic Horas, Disha Shoola, Gochar Vedha & Planetary Data
# -----------------------------------------------------------------------------
CHALDEAN_ORDER = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]

HORA_PLANETS_DATA: dict[str, dict[str, Any]] = {
    "Sun": {
        "planet_bn": "সূর্য", "planet_hi": "सूर्य", "planet_sa": "Surya",
        "category": "Tejaswi / Shubh", "category_bn": "তেজস্বী / শুভ", "category_hi": "तेजस्वी / शुभ",
        "is_auspicious": True,
        "verdict": "Leadership & Administration",
        "verdict_bn": "নেতৃত্ব ও প্রশাসনিক সাফল্য",
        "verdict_hi": "नेतृत्व और प्रशासनिक सफलता",
        "best_activities": "Meeting superiors, government paperwork, high-level planning, leadership initiatives.",
        "best_activities_bn": "ঊর্ধ্বতন কর্তৃপক্ষের সাথে সাক্ষাৎ, সরকারি কাগজপত্র জমা, নতুন দায়িত্ব গ্রহণ ও নেতৃত্বদান।",
        "best_activities_hi": "वरिष्ठ अधिकारियों से भेंट, सरकारी कार्य, नई जिम्मेदारियां और प्रशासनिक योजनाएं।",
    },
    "Venus": {
        "planet_bn": "শুক্র", "planet_hi": "शुक्र", "planet_sa": "Shukra",
        "category": "Amrit / Supreme", "category_bn": "অমৃত / অতীব শুভ", "category_hi": "अमृत / अत्यंत शुभ",
        "is_auspicious": True,
        "verdict": "Arts, Romance & Prosperity",
        "verdict_bn": "শিল্প, প্রণয় ও সমৃদ্ধি",
        "verdict_hi": "कला, प्रेम और समृद्धि",
        "best_activities": "Creative arts, purchasing luxury items, jewellery, romance, music, beauty treatments.",
        "best_activities_bn": "শিল্পচর্চা, নতুন পোশাক বা অলংকার ক্রয়, প্রণয় নিবেদন, রূপচর্চা ও সামাজিক আনন্দানুষ্ঠান।",
        "best_activities_hi": "कला, आभूषण और नए वस्त्र क्रय, सौंदर्य प्रसाधन और प्रेम प्रसंग।",
    },
    "Mercury": {
        "planet_bn": "বুধ", "planet_hi": "बुध", "planet_sa": "Budha",
        "category": "Shubh / Chara", "category_bn": "শুভ / চলমান", "category_hi": "शुभ / गतिशील",
        "is_auspicious": True,
        "verdict": "Commerce, Media & Learning",
        "verdict_bn": "বাণিজ্য, হিসেব-নিকাশ ও বিদ্যাচর্চা",
        "verdict_hi": "व्यापार, संचार और विद्या",
        "best_activities": "Signing contracts, accounting, trading, writing, marketing, studying, tech tasks.",
        "best_activities_bn": "ব্যবসা-বাণিজ্য, হিসাবরক্ষণ, চুক্তিপত্র স্বাক্ষর, লেখালেখি, শেয়ার বা ব্যাংকিং লেনদেন।",
        "best_activities_hi": "व्यापारिक लेन-देन, अनुबंध हस्ताक्षर, लेखन, अध्ययन और संचार।",
    },
    "Moon": {
        "planet_bn": "চন্দ্র", "planet_hi": "चन्द्र", "planet_sa": "Chandra",
        "category": "Chara / Shubh", "category_bn": "চল / শুভ", "category_hi": "गतिशील / शुभ",
        "is_auspicious": True,
        "verdict": "Peace, Travel & Domestic Joy",
        "verdict_bn": "ভ্রমণ, মানসিক শান্তি ও গৃহসুখ",
        "verdict_hi": "यात्रा, मानसिक शांति और गृहसुख",
        "best_activities": "Short journeys, meeting family, water-related trade, gardening, peace meditation.",
        "best_activities_bn": "স্বল্প দূরত্বের ভ্রমণ, পরিবারের সাথে সময় কাটানো, খাদ্য ও জল সংক্রান্ত ব্যবসা, মনের প্রশান্তি।",
        "best_activities_hi": "यात्रा, पारिवारिक मिलन, जल-संबंधित व्यापार और ध्यान।",
    },
    "Saturn": {
        "planet_bn": "শনি", "planet_hi": "शनि", "planet_sa": "Shani",
        "category": "Manda / Kaal", "category_bn": "মন্থর / সতর্ক হোরা", "category_hi": "मंद / सावधानी",
        "is_auspicious": False,
        "verdict": "Discipline, Labor & Deep Focus",
        "verdict_bn": "কঠিন শ্রম, গবেষণা ও সংযম",
        "verdict_hi": "कठिन श्रम, शोध और अनुशासन",
        "best_activities": "Deep technical research, routine repair, agricultural work, meditation, discipline. Avoid starting celebratory events.",
        "best_activities_bn": "গবেষণা, বকেয়া কাজ শেষ করা, কৃষিকাজ, মাটির কাজ ও ধ্যান। নতুন মাঙ্গলিক কাজ পরিহার্য।",
        "best_activities_hi": "गहन तकनीकी कार्य, मरम्मत, कृषि और ध्यान। मांगलिक कार्यों से बचें।",
    },
    "Jupiter": {
        "planet_bn": "বৃহস্পতি", "planet_hi": "गुरु", "planet_sa": "Brihaspati",
        "category": "Amrit / Supreme", "category_bn": "অমৃত / পরম শুভ", "category_hi": "अमृत / सर्वोत्तम",
        "is_auspicious": True,
        "verdict": "Wisdom, Finance & Dharma",
        "verdict_bn": "জ্ঞানচর্চা, আধ্যাত্মিকতা ও ধনলাভ",
        "verdict_hi": "ज्ञान, अध्यात्म और धन लाभ",
        "best_activities": "Starting auspicious ventures, higher education, banking investments, religious ceremonies, meeting mentors.",
        "best_activities_bn": "যেকোনো নতুন কাজের সূচনা, গুরুকৃপা লাভ, বড় আর্থিক বিনিয়োগ, পুজো-অর্চনা ও শিক্ষা।",
        "best_activities_hi": "नए शुभ कार्य, धार्मिक अनुष्ठान, निवेश और गुरुओं से मार्गदर्शन।",
    },
    "Mars": {
        "planet_bn": "মঙ্গল", "planet_hi": "मंगल", "planet_sa": "Mangala",
        "category": "Ugra / Teekshna", "category_bn": "উগ্র / শৌর্য হোরা", "category_hi": "उग्र / साहसिक",
        "is_auspicious": False,
        "verdict": "Courage, Sports & Technical Execution",
        "verdict_bn": "সাহস, খেলাধুলা ও যান্ত্রিক কাজ",
        "verdict_hi": "साहस, खेलकूद और तकनीकी कार्य",
        "best_activities": "Sports competition, police/military tasks, surgery, legal debates, heavy engineering. Avoid calm negotiations.",
        "best_activities_bn": "খেলাধুলা, প্রতিযোগিতামূলক পরীক্ষা, জমিজমা সংক্রান্ত সমীক্ষা ও প্রযুক্তিগত কাজ। বিতর্ক এড়িয়ে চলুন।",
        "best_activities_hi": "प्रतियोगिता, भूमि कार्य, शल्य चिकित्सा और तकनीकी कार्य। विवाद से बचें।",
    },
}

DISHA_SHOOLA_DATA: dict[str, dict[str, str]] = {
    "Sunday": {
        "dir": "West", "dir_bn": "পশ্চিম", "dir_hi": "पश्चिम",
        "remedy": "Consume pan (betel leaf) or sesame seeds before journey.",
        "remedy_bn": "যাত্রার পূর্বে পান বা সাদা তিল মুখে দিয়ে যাত্রা শুভ।",
        "remedy_hi": "यात्रा से पूर्व पान या तिल खाकर निकलें।",
    },
    "Monday": {
        "dir": "East", "dir_bn": "পূর্ব", "dir_hi": "पूर्व",
        "remedy": "Look into a mirror (darpan) before journey.",
        "remedy_bn": "যাত্রার পূর্বে আয়নায় নিজের মুখ দর্শন করে যাত্রা করুন।",
        "remedy_hi": "यात्रा से पूर्व दर्पण देखकर निकलें।",
    },
    "Tuesday": {
        "dir": "North", "dir_bn": "উত্তর", "dir_hi": "उत्तर",
        "remedy": "Consume jaggery or coriander seeds before journey.",
        "remedy_bn": "যাত্রার পূর্বে গুড় বা ধনে মুখে দেওয়া কল্যাণকর।",
        "remedy_hi": "यात्रा से पूर्व थोड़ा गुड़ या धनिया खाकर निकलें।",
    },
    "Wednesday": {
        "dir": "North", "dir_bn": "উত্তর", "dir_hi": "उत्तर",
        "remedy": "Consume green coriander or sesame seeds.",
        "remedy_bn": "যাত্রার পূর্বে ধনে বা তিল গ্রহণ করা শুভ।",
        "remedy_hi": "यात्रा से पूर्व धनिया या तिल ग्रहण करें।",
    },
    "Thursday": {
        "dir": "South", "dir_bn": "দক্ষিণ", "dir_hi": "दक्षिण",
        "remedy": "Consume fresh curd or cumin seeds.",
        "remedy_bn": "যাত্রার পূর্বে খাঁটি দই বা সামান্য জিরা মুখে দেওয়া বিধেয়।",
        "remedy_hi": "यात्रा से पूर्व दही या जीरा खाकर निकलें।",
    },
    "Friday": {
        "dir": "West", "dir_bn": "পশ্চিম", "dir_hi": "पश्चिम",
        "remedy": "Consume barley or mustard seeds before journey.",
        "remedy_bn": "যাত্রার পূর্বে যব বা সাদা সর্ষে মুখে দিয়ে যাত্রা করুন।",
        "remedy_hi": "यात्रा से पूर्व जौ या सरसों खाकर निकलें।",
    },
    "Saturday": {
        "dir": "East", "dir_bn": "পূর্ব", "dir_hi": "पूर्व",
        "remedy": "Consume ginger or black urad grains before journey.",
        "remedy_bn": "যাত্রার পূর্বে সামান্য আদা বা কালো বিউলি ডাল মুখে দেওয়া শুভ।",
        "remedy_hi": "यात्रा से पूर्व अदरक या उड़द खाकर निकलें।",
    },
}

RASHI_CLASSICAL_EXTRAS: list[dict[str, Any]] = [
    {
        "sign_idx": 0,
        "beej_mantra": "ॐ ক্রাং ক্রীং ক্রৌং সঃ ভৌমায় নমঃ",
        "beej_mantra_hi": "ॐ क्रां क्रीं क्रौं सः भौमाय नमः",
        "charity_en": "Donate red lentils (masoor dal), copper vessels, or red cloth to needy.",
        "charity_bn": "লাল মসুর ডাল, তামার পাত্র বা লাল বস্ত্র অভাবী মানুষকে দান করুন।",
        "charity_hi": "लाल मसूर दाल, तांबे का बर्तन या लाल वस्त्र दान करें।",
        "favorable_rashis": ["Leo", "Sagittarius", "Cancer"],
        "favorable_rashis_bn": ["সিংহ", "ধনু", "কর্কট"],
    },
    {
        "sign_idx": 1,
        "beej_mantra": "ॐ দ্রাং দ্রীং দ্রৌং সঃ শুক্রায় নমঃ",
        "beej_mantra_hi": "ॐ द्रां द्रीं द्रौं सः शुक्राय नमः",
        "charity_en": "Donate white rice, sugar, curd, milk or perfumed items.",
        "charity_bn": "সুগন্ধি আতর, চাল, চিনি, দুধ বা সাদা মিষ্টান্ন দান করুন।",
        "charity_hi": "चावल, चीनी, दूध, दही या इत्र दान करें।",
        "favorable_rashis": ["Virgo", "Capricorn", "Libra"],
        "favorable_rashis_bn": ["কন্যা", "মকর", "তুলা"],
    },
    {
        "sign_idx": 2,
        "beej_mantra": "ॐ ব্রাং ব্রীং ব্রৌং সঃ বুধায় নমঃ",
        "beej_mantra_hi": "ॐ ब्रां ब्रीं ब्रौं सः बुधाय नमः",
        "charity_en": "Donate green moong dal, educational books, or green vegetables to cows.",
        "charity_bn": "সবুজ মুগ ডাল, ছাত্রছাত্রীদের বই বা গোরুকে সবুজ ঘাস/শাকসবজি দান।",
        "charity_hi": "हरी मूंग दाल, पुस्तकें या गाय को हरा चारा खिलाएं।",
        "favorable_rashis": ["Libra", "Aquarius", "Aries"],
        "favorable_rashis_bn": ["তুলা", "কুম্ভ", "মেষ"],
    },
    {
        "sign_idx": 3,
        "beej_mantra": "ॐ শ্রাং শ্রীং শ্রৌং সঃ চন্দ্রায় নমঃ",
        "beej_mantra_hi": "ॐ श्रां श्रीं श्रौं सः चन्द्राय नमः",
        "charity_en": "Donate milk, silver, rice, white flowers, or drinking water facility.",
        "charity_bn": "দুধ, রূপা, চাল, সাদা ফুল অথবা তৃষ্ণার্তকে সুপেয় জল দান।",
        "charity_hi": "दूध, चांदी, चावल, सफेद फूल या जल सेवा करें।",
        "favorable_rashis": ["Scorpio", "Pisces", "Taurus"],
        "favorable_rashis_bn": ["বৃশ্চিক", "মীন", "বৃষ"],
    },
    {
        "sign_idx": 4,
        "beej_mantra": "ॐ হ্রাং হ্রীং হ্রৌং সঃ সূর্যায় নমঃ",
        "beej_mantra_hi": "ॐ ह्रां ह्रीं ह्रौं सः सूर्याय नमः",
        "charity_en": "Offer water to the rising Sun; donate wheat, jaggery, or ruby red items.",
        "charity_bn": "উদীয়মান সূর্যকে তামার ঘটিতে অর্ঘ্য প্রদান; গম, গুড় বা কেশর দান করুন।",
        "charity_hi": "सूर्य को अर्घ्य दें; गेहूं, गुड़ या तांबे का दान करें।",
        "favorable_rashis": ["Aries", "Sagittarius", "Gemini"],
        "favorable_rashis_bn": ["মেষ", "ধনু", "মিথুন"],
    },
    {
        "sign_idx": 5,
        "beej_mantra": "ॐ বুং বুধায় নমঃ",
        "beej_mantra_hi": "ॐ बुं बुधाय नमः",
        "charity_en": "Water the Tulsi plant; donate green apparel, notebooks, or pens.",
        "charity_bn": "তুলসী গাছে জল সিঞ্চন; সবুজ বস্ত্র, খাতা বা কলম অভাবী পড়ুয়াকে দান।",
        "charity_hi": "तुलसी में जल दें; हरी वस्तुएं, स्टेशनरी या किताबें दान करें।",
        "favorable_rashis": ["Taurus", "Capricorn", "Cancer"],
        "favorable_rashis_bn": ["বৃষ", "মকর", "কর্কট"],
    },
    {
        "sign_idx": 6,
        "beej_mantra": "ॐ শুং শুক্রায় নমঃ",
        "beej_mantra_hi": "ॐ शुं शुक्राय नमः",
        "charity_en": "Donate white silks, sandalwood, cosmetics, or sweets made of khoya.",
        "charity_bn": "সাদা রেশমি বস্ত্র, চন্দন, সুগন্ধি বা ক্ষীরের মিষ্টি দান করুন।",
        "charity_hi": "सफेद रेशमी वस्त्र, चंदन, सौंदर्य सामग्री या खीर दान करें।",
        "favorable_rashis": ["Gemini", "Aquarius", "Leo"],
        "favorable_rashis_bn": ["মিথুন", "কুম্ভ", "সিংহ"],
    },
    {
        "sign_idx": 7,
        "beej_mantra": "ॐ ভৌং ভৌমায় নমঃ",
        "beej_mantra_hi": "ॐ भौं भौमाय नमः",
        "charity_en": "Recite Hanuman Chalisa; donate jaggery, sweets, or red coral items.",
        "charity_bn": "হনুমান চালিসা পাঠ; লাল মিষ্টি, গুড় বা রক্তচন্দন দান করুন।",
        "charity_hi": "हनुमान चालीसा पाठ करें; लाल मिठाई, गुड़ या सिंदूर दान करें।",
        "favorable_rashis": ["Cancer", "Pisces", "Virgo"],
        "favorable_rashis_bn": ["কর্কট", "মীন", "কন্যা"],
    },
    {
        "sign_idx": 8,
        "beej_mantra": "ॐ গ্রাং গ্রীং গ্রৌং সঃ গুরবে নমঃ",
        "beej_mantra_hi": "ॐ ग्रां ग्रीं ग्रौं सः गुरवे नमः",
        "charity_en": "Donate chana dal, yellow bananas, turmeric, or spiritual scriptures.",
        "charity_bn": "ছোলার ডাল, পাকা কলা, হলুদ গুঁড়ো বা ধর্মীয় গ্রন্থ দান করুন।",
        "charity_hi": "चने की दाल, पीले केले, हल्दी या धार्मिक ग्रंथ दान करें।",
        "favorable_rashis": ["Aries", "Leo", "Libra"],
        "favorable_rashis_bn": ["মেষ", "সিংহ", "তুলা"],
    },
    {
        "sign_idx": 9,
        "beej_mantra": "ॐ প্রাং প্রীং প্রৌং সঃ শনৈশ্চরায় নমঃ",
        "beej_mantra_hi": "ॐ प्रां प्रीं प्रौं सः शनैश्चराय नमः",
        "charity_en": "Donate sesame oil, black umbrella, leather shoes, or black blankets.",
        "charity_bn": "তিল তেল, কালো ছাতা, চামড়ার জুতো বা কালো কম্বল দরিদ্রকে দান।",
        "charity_hi": "तिल का तेल, काला छाता, जूते या काला कंबल दान करें।",
        "favorable_rashis": ["Taurus", "Virgo", "Scorpio"],
        "favorable_rashis_bn": ["বৃষ", "কন্যা", "বৃশ্চিক"],
    },
    {
        "sign_idx": 10,
        "beej_mantra": "ॐ শং শনৈশ্চরায় নমঃ",
        "beej_mantra_hi": "ॐ शं शनैश्चराय नमः",
        "charity_en": "Light a mustard oil lamp under Peepal tree; serve visually impaired elders.",
        "charity_bn": "অশ্বত্থ তলায় সর্ষের তেলের প্রদীপ প্রজ্জ্বলন ও প্রবীণ/অসহায় মানুষকে সেবা।",
        "charity_hi": "पीपल के नीचे सरसों के तेल का दीपक जलाएं; असहायों की सेवा करें।",
        "favorable_rashis": ["Gemini", "Libra", "Sagittarius"],
        "favorable_rashis_bn": ["মিথুন", "তুলা", "ধনু"],
    },
    {
        "sign_idx": 11,
        "beej_mantra": "ॐ বৃহস্পতয়ে নমঃ",
        "beej_mantra_hi": "ॐ बृहस्पतये नमः",
        "charity_en": "Feed cows yellow fruits; donate saffron sweets, books, or yellow cloth.",
        "charity_bn": "গোরুকে পাকা কলা খাওয়ান; কেশর মিষ্টান্ন, পুজোসামগ্রী বা হলুদ কাপড় দান।",
        "charity_hi": "गाय को केले खिलाएं; केसरिया मिठाई या पीले वस्त्र दान करें।",
        "favorable_rashis": ["Cancer", "Scorpio", "Capricorn"],
        "favorable_rashis_bn": ["কর্কট", "বৃশ্চিক", "মকর"],
    },
]

# Classical Gochar Vedha Pairs for Moon's Auspicious Houses (Phaladeepika & Brihat Samhita)
MOON_VEDHA_PAIRS: dict[int, int] = {
    3: 9,   # Moon in 3rd obstructed by planet in 9th
    6: 12,  # Moon in 6th obstructed by planet in 12th
    7: 2,   # Moon in 7th obstructed by planet in 2nd
    10: 4,  # Moon in 10th obstructed by planet in 4th
    11: 8,  # Moon in 11th obstructed by planet in 8th
}


def _fmt_time_str(h_float: float) -> str:
    """Formats float hour (0-24) into standard 12-hour AM/PM string."""
    h_int = int(h_float) % 24
    m_int = int((h_float - int(h_float)) * 60) % 60
    period = "AM" if h_int < 12 else "PM"
    disp_h = h_int if h_int <= 12 else h_int - 12
    if disp_h == 0:
        disp_h = 12
    return f"{disp_h:02d}:{m_int:02d} {period}"


def _calculate_24_horas(
    sunrise_h: float,
    sunset_h: float,
    next_sunrise_h: float,
    vara_lord: str,
) -> list[HoraItem]:
    """Calculates all 24 planetary horas starting from local sunrise."""
    day_span = (sunset_h - sunrise_h) if sunset_h > sunrise_h else (sunset_h + 24.0 - sunrise_h)
    day_dur = day_span / 12.0

    night_span = (next_sunrise_h - sunset_h) if next_sunrise_h > sunset_h else (next_sunrise_h + 24.0 - sunset_h)
    night_dur = night_span / 12.0

    try:
        start_idx = CHALDEAN_ORDER.index(vara_lord)
    except ValueError:
        start_idx = 3  # default Sun

    horas: list[HoraItem] = []

    # 12 Daytime Horas
    for i in range(12):
        s_time = (sunrise_h + i * day_dur) % 24.0
        e_time = (sunrise_h + (i + 1) * day_dur) % 24.0
        p_name = CHALDEAN_ORDER[(start_idx + i) % 7]
        p_meta = HORA_PLANETS_DATA.get(p_name, HORA_PLANETS_DATA["Sun"])

        horas.append(
            HoraItem(
                hora_index=i + 1,
                hora_number=i + 1,
                is_day=True,
                start_time=_fmt_time_str(s_time),
                end_time=_fmt_time_str(e_time),
                planet=p_name,
                planet_bn=p_meta["planet_bn"],
                planet_hi=p_meta["planet_hi"],
                planet_sa=p_meta["planet_sa"],
                is_auspicious=p_meta["is_auspicious"],
                category=p_meta["category"],
                category_bn=p_meta["category_bn"],
                category_hi=p_meta["category_hi"],
                verdict=p_meta["verdict"],
                verdict_bn=p_meta["verdict_bn"],
                verdict_hi=p_meta["verdict_hi"],
                best_activities=p_meta["best_activities"],
                best_activities_bn=p_meta["best_activities_bn"],
                best_activities_hi=p_meta["best_activities_hi"],
            )
        )

    # 12 Nighttime Horas
    for j in range(12):
        total_idx = 12 + j
        s_time = (sunset_h + j * night_dur) % 24.0
        e_time = (sunset_h + (j + 1) * night_dur) % 24.0
        p_name = CHALDEAN_ORDER[(start_idx + total_idx) % 7]
        p_meta = HORA_PLANETS_DATA.get(p_name, HORA_PLANETS_DATA["Sun"])

        horas.append(
            HoraItem(
                hora_index=total_idx + 1,
                hora_number=j + 1,
                is_day=False,
                start_time=_fmt_time_str(s_time),
                end_time=_fmt_time_str(e_time),
                planet=p_name,
                planet_bn=p_meta["planet_bn"],
                planet_hi=p_meta["planet_hi"],
                planet_sa=p_meta["planet_sa"],
                is_auspicious=p_meta["is_auspicious"],
                category=p_meta["category"],
                category_bn=p_meta["category_bn"],
                category_hi=p_meta["category_hi"],
                verdict=p_meta["verdict"],
                verdict_bn=p_meta["verdict_bn"],
                verdict_hi=p_meta["verdict_hi"],
                best_activities=p_meta["best_activities"],
                best_activities_bn=p_meta["best_activities_bn"],
                best_activities_hi=p_meta["best_activities_hi"],
            )
        )

    return horas


PLANET_DISPLAY_NAMES: dict[str, dict[str, str]] = {
    "Sun": {"bn": "সূর্য", "hi": "सूर्य", "sa": "Surya"},
    "Moon": {"bn": "চন্দ্র", "hi": "चन्द्र", "sa": "Chandra"},
    "Mars": {"bn": "মঙ্গল", "hi": "मंगल", "sa": "Mangala"},
    "Mercury": {"bn": "বুধ", "hi": "बुध", "sa": "Budha"},
    "Jupiter": {"bn": "বৃহস্পতি", "hi": "गुरु", "sa": "Brihaspati"},
    "Venus": {"bn": "শুক্র", "hi": "शुक्र", "sa": "Shukra"},
    "Saturn": {"bn": "শনি", "hi": "शनि", "sa": "Shani"},
    "Rahu": {"bn": "রাহু", "hi": "राहु", "sa": "Rahu"},
    "Ketu": {"bn": "কেতু", "hi": "केतु", "sa": "Ketu"},
}



# -----------------------------------------------------------------------------
# Vedic Choghadiya Data & Calculation (Amrit, Shubh, Labh, Char, Rog, Kaal, Udveg)
# -----------------------------------------------------------------------------
CHOGHADIYA_METADATA: dict[str, dict[str, Any]] = {
    "Amrit": {
        "bn": "অমৃত", "hi": "अमृत", "ruler": "Moon", "status": "auspicious",
        "guidance_en": "Supreme nectar muhurat. Highly auspicious for starting major ventures, signing agreements, ceremonies, and travel.",
        "guidance_bn": "অমৃত মুহূর্ত। নতুন কার্যারম্ভ, গৃহপ্রবেশ, চুক্তি স্বাক্ষর ও শুভ কাজের জন্য সর্বোত্তম।",
        "guidance_hi": "अमृत मुहूर्त। सभी प्रकार के शुभ कार्य, नवीन उद्यम, यात्रा और समझौते के लिए सर्वोत्तम।",
    },
    "Shubh": {
        "bn": "শুভ", "hi": "शुभ", "ruler": "Jupiter", "status": "auspicious",
        "guidance_en": "Highly propitious period ruled by Guru. Favorable for education, religious rites, investments, and medical healing.",
        "guidance_bn": "শুভ মুহূর্ত। বৃহস্পতির প্রভাবে পুজো-অর্চনা, বিদ্যালাভ, নতুন বিনিয়োগ ও মাঙ্গলিক অনুষ্ঠানের জন্য প্রশস্ত।",
        "guidance_hi": "शुभ मुहूर्त। धार्मिक अनुष्ठान, शिक्षा, नवीन निवेश और मांगलिक कार्यों हेतु अत्यंत अनुकूल।",
    },
    "Labh": {
        "bn": "লাভ", "hi": "लाभ", "ruler": "Mercury", "status": "auspicious",
        "guidance_en": "Dynamic wealth & commercial window ruled by Budha. Ideal for business, trading, tech, and negotiation.",
        "guidance_bn": "লাভ মুহূর্ত। বুধের কৃপায় ব্যবসা-বাণিজ্য, শেয়ার লেনদেন, নতুন চুক্তি ও আর্থিক লাভের জন্য শ্রেষ্ঠ।",
        "guidance_hi": "लाभ मुहूर्त। व्यापार, नए वित्तीय अनुबंध, संचार और लाभ प्राप्ति हेतु श्रेष्ठ समय।",
    },
    "Char": {
        "bn": "চল", "hi": "चर", "ruler": "Venus", "status": "auspicious",
        "guidance_en": "Movable/dynamic period ruled by Shukra. Favorable for journeys, vehicle purchases, arts, and dynamic movements.",
        "guidance_bn": "চল মুহূর্ত। শুক্রের অধীন। যাত্রা, গাড়ি কেনা, স্থান পরিবর্তন, শিল্পচর্চা ও সক্রিয় কাজের জন্য শুভ।",
        "guidance_hi": "चर मुहूर्त। यात्रा, वाहन क्रय, कलात्मक कार्य और गतिशील गतिविधियों के लिए शुभ।",
    },
    "Rog": {
        "bn": "রোগ", "hi": "रोग", "ruler": "Mars", "status": "inauspicious",
        "guidance_en": "Adverse window ruled by Mars. Avoid beginning treatment or celebrating; suitable only for fierce/technical tasks.",
        "guidance_bn": "রোগ মুহূর্ত। মঙ্গলের প্রভাব। নতুন চিকিৎসা বা মাঙ্গলিক কাজ পরিহার করুন। শত্রু দমন বা শ্রমসাধ্য কাজ চলে।",
        "guidance_hi": "रोग मुहूर्त। मांगलिक कार्यों व नए उपचार से बचें। केवल साहसिक व तकनीकी कार्यों हेतु उपयुक्त।",
    },
    "Kaal": {
        "bn": "কাল", "hi": "काल", "ruler": "Saturn", "status": "inauspicious",
        "guidance_en": "Strict/obstructive period ruled by Saturn. Delay important meetings, loans, and celebrations. Keep a low profile.",
        "guidance_bn": "কাল মুহূর্ত। শনির প্রভাব। ঋণ গ্রহণ, বড় চুক্তি বা শুভ উৎসব স্থগিত রাখা বিধেয়। সংযম পালন করুন।",
        "guidance_hi": "काल मुहूर्त। शनि की कठोर ऊर्जा। महत्वपूर्ण बैठकें और वित्तीय निर्णय टालें।",
    },
    "Udveg": {
        "bn": "উদ্বেগ", "hi": "उद्वेग", "ruler": "Sun", "status": "inauspicious",
        "guidance_en": "Agitated/tense window ruled by Sun. Avoid government disputes, confrontations, and stressful commitments.",
        "guidance_bn": "উদ্বেগ মুহূর্ত। রবির উগ্রতা। সরকারি বিরোধ, বিবাদ বা মানসিক চাপ তৈরি করে এমন বিষয় এড়িয়ে চলুন।",
        "guidance_hi": "उद्वेग मुहूर्त। कलह और विवाद से दूर रहें। शांति बनाए रखें और तनावपूर्ण कार्य टालें।",
    },
}

CHOGHADIYA_DAY_SEQS: list[list[str]] = [
    ["Udveg", "Char", "Labh", "Amrit", "Kaal", "Shubh", "Rog", "Udveg"],         # Sunday
    ["Amrit", "Kaal", "Shubh", "Rog", "Udveg", "Char", "Labh", "Amrit"],         # Monday
    ["Rog", "Udveg", "Char", "Labh", "Amrit", "Kaal", "Shubh", "Rog"],           # Tuesday
    ["Labh", "Amrit", "Kaal", "Shubh", "Rog", "Udveg", "Char", "Labh"],         # Wednesday
    ["Shubh", "Rog", "Udveg", "Char", "Labh", "Amrit", "Kaal", "Shubh"],         # Thursday
    ["Char", "Labh", "Amrit", "Kaal", "Shubh", "Rog", "Udveg", "Char"],           # Friday
    ["Kaal", "Shubh", "Rog", "Udveg", "Char", "Labh", "Amrit", "Kaal"],         # Saturday
]

CHOGHADIYA_NIGHT_SEQS: list[list[str]] = [
    ["Shubh", "Amrit", "Char", "Rog", "Kaal", "Labh", "Udveg", "Shubh"],         # Sunday night
    ["Char", "Rog", "Kaal", "Labh", "Udveg", "Shubh", "Amrit", "Char"],         # Monday night
    ["Kaal", "Labh", "Udveg", "Shubh", "Amrit", "Char", "Rog", "Kaal"],         # Tuesday night
    ["Udveg", "Shubh", "Amrit", "Char", "Rog", "Kaal", "Labh", "Udveg"],         # Wednesday night
    ["Amrit", "Char", "Rog", "Kaal", "Labh", "Udveg", "Shubh", "Amrit"],         # Thursday night
    ["Rog", "Kaal", "Labh", "Udveg", "Shubh", "Amrit", "Char", "Rog"],           # Friday night
    ["Labh", "Udveg", "Shubh", "Amrit", "Char", "Rog", "Kaal", "Labh"],         # Saturday night
]


def _calculate_16_choghadiya(
    sunrise_h: float,
    sunset_h: float,
    next_sunrise_h: float,
    weekday_idx: int,
    lang: Lang,
) -> list[ChoghadiyaItem]:
    """Computes all 16 Vedic Choghadiyas (8 Day + 8 Night) with exact times and client rules."""
    items: list[ChoghadiyaItem] = []
    day_span = sunset_h - sunrise_h
    day_slot = day_span / 8.0

    day_seq = CHOGHADIYA_DAY_SEQS[weekday_idx % 7]
    for i in range(8):
        s_h = sunrise_h + i * day_slot
        e_h = sunrise_h + (i + 1) * day_slot
        name_en = day_seq[i]
        meta = CHOGHADIYA_METADATA.get(name_en, {})
        items.append(
            ChoghadiyaItem(
                period_index=i,
                is_day=True,
                name=name_en,
                name_bn=meta.get("bn", name_en),
                name_hi=meta.get("hi", name_en),
                ruler_planet=meta.get("ruler", "Sun"),
                start_time=_fmt_time_str(s_h),
                end_time=_fmt_time_str(e_h),
                status=meta.get("status", "neutral"),
                guidance=meta.get(f"guidance_{lang}", meta.get("guidance_en", "")),
                guidance_bn=meta.get("guidance_bn", ""),
                guidance_hi=meta.get("guidance_hi", ""),
            )
        )

    night_span = (next_sunrise_h + 24.0) - sunset_h
    night_slot = night_span / 8.0
    night_seq = CHOGHADIYA_NIGHT_SEQS[weekday_idx % 7]
    for j in range(8):
        s_h = sunset_h + j * night_slot
        e_h = sunset_h + (j + 1) * night_slot
        s_fmt = s_h if s_h < 24.0 else s_h - 24.0
        e_fmt = e_h if e_h < 24.0 else e_h - 24.0
        name_en = night_seq[j]
        meta = CHOGHADIYA_METADATA.get(name_en, {})
        items.append(
            ChoghadiyaItem(
                period_index=8 + j,
                is_day=False,
                name=name_en,
                name_bn=meta.get("bn", name_en),
                name_hi=meta.get("hi", name_en),
                ruler_planet=meta.get("ruler", "Sun"),
                start_time=_fmt_time_str(s_fmt),
                end_time=_fmt_time_str(e_fmt),
                status=meta.get("status", "neutral"),
                guidance=meta.get(f"guidance_{lang}", meta.get("guidance_en", "")),
                guidance_bn=meta.get("guidance_bn", ""),
                guidance_hi=meta.get("guidance_hi", ""),
            )
        )
    return items


# -----------------------------------------------------------------------------
# Vedic Panchak Engine (Dhanishta 3rd pada to Revati)
# -----------------------------------------------------------------------------
def _calculate_panchak(moon_lon: float, weekday_idx: int, lang: Lang) -> PanchakStatus:
    """Determines whether Moon is in Vedic Panchak (296.6667° to 360°) and its precise category."""
    is_active = (moon_lon >= 296.6666667 and moon_lon < 360.0)
    if not is_active:
        return PanchakStatus(
            is_panchak=False,
            panchak_type="None",
            panchak_type_bn="পঞ্চক মুক্ত",
            panchak_type_hi="पंचक रहित",
            severity="none",
            description="Moon is free from Panchak dosha. All auspicious sanskars are unobstructed.",
            description_bn="চন্দ্র পঞ্চক মুক্ত। গৃহনির্মাণ, ছাদ ঢালাই ও শুভ কাজ নির্বিঘ্নে সম্পন্ন করা যাবে।",
            description_hi="चन्द्रमा पंचक से मुक्त है। सभी शुभ कार्य और गृह निर्माण निर्बाध रूप से किए जा सकते हैं।",
            prohibited_activities=[],
        )

    panchak_catalog = {
        0: ("Rog Panchak", "রোগ পঞ্চক", "रोग पंचक", "high",
            "Panchak on Sunday induces physical weakness or ailments. Avoid commencing new treatments or starting major physical endeavors.",
            "রবিবার পঞ্চক শারীরিক দুর্বলতা বা রোগ বৃদ্ধি করতে পারে। নতুন চিকিৎসা শুরু করা এড়িয়ে চলুন।",
            "रविवार को पंचक शारीरिक कष्ट दे सकता है। नए उपचार व अत्यधिक श्रम से बचें।",
            "Avoid starting new medical treatments; offer water to Surya."),
        1: ("Raj Panchak", "রাজ পঞ্চক", "राज पंचक", "low",
            "Panchak on Monday is royal and highly auspicious for state affairs, property acquisition, and careers.",
            "সোমবার পঞ্চক অত্যন্ত শুভ 'রাজ পঞ্চক'। সরকারি কাজ, সম্পত্তি ক্রয় ও পেশাগত সাফল্যের জন্য অনুকূল।",
            "सोमवार को राज पंचक होता है जो संपत्ति व सरकारी कार्यों के लिए बहुत शुभ है।",
            "No major prohibitions; highly favorable for governance and real estate."),
        2: ("Agni Panchak", "অগ্নি পঞ্চক", "अग्नि पंचक", "medium",
            "Panchak on Tuesday carries fire and dispute risks. Strictly avoid electrical work, furnace setup, or heated debates.",
            "মঙ্গলবার অগ্নি পঞ্চক অগ্নিকাণ্ড ও বিবাদের ঝুঁকি বাড়ায়। ইলেকট্রিক্যাল কাজ ও বিতর্ক এড়িয়ে চলুন।",
            "मंगलवार को अग्नि पंचक में आग, औजार और विवादों से दूर रहना चाहिए।",
            "Strictly avoid electrical equipment work, fire installations, or heated confrontations."),
        3: ("Laghu Panchak", "লঘু পঞ্চক", "लघु पंचक", "low",
            "Panchak on Wednesday brings mild effects; routine work proceeds smoothly.",
            "বুধবার লঘু পঞ্চক মৃদু প্রভাব ফেলে; সাধারণ কাজ নির্দ্বিধায় সম্পন্ন করা যায়।",
            "बुधवार को लघु पंचक सामान्य फल देता है।",
            "Avoid financial speculation."),
        4: ("Laghu Panchak", "লঘু পঞ্চক", "लघु पंचक", "low",
            "Panchak on Thursday is mild and shielded by Guru's wisdom.",
            "বৃহস্পতিবার লঘু পঞ্চক গুরুর প্রভাবে সুরক্ষিত থাকে।",
            "गुरुवार को लघु पंचक में गुरु कृपा से सुरक्षा रहती है।",
            "Avoid southern direction journeys."),
        5: ("Chor Panchak", "চোর পঞ্চক", "চোর পঞ্চক", "medium",
            "Panchak on Friday warns of theft, monetary negligence, and impulsive luxury spending. Avoid starting major travel.",
            "শুক্রবার চোর পঞ্চক আর্থিক ক্ষতি বা চুরির আশঙ্কা বাড়ায়। মূল্যবান জিনিস সামলান ও দক্ষিণমুখী যাত্রা বর্জন করুন।",
            "शुक्रवार को चोर पंचक में धन हानि और चोरी से सावधान रहें। दक्षिण दिशा की यात्रा से बचें।",
            "Avoid travel towards south, unsecured money transactions, or leaving valuables unattended."),
        6: ("Mrityu Panchak", "মৃত্যু পঞ্চক", "মৃত্যু পঞ্চক", "high",
            "Panchak on Saturday carries severe obstructive energy. Strictly avoid roof casting, south travel, cot making, or high-risk tasks.",
            "শনিবার মৃত্যু পঞ্চক অত্যন্ত সংবেদনশীল। ছাদ ঢালাই, দক্ষিণ যাত্রা ও ঝুঁকিপূর্ণ সিদ্ধান্ত বর্জন করুন।",
            "शनिवार को मृत्यु पंचक में छत ढलाई, दक्षिण दिशा में यात्रा और जोखिम भरे कार्यों से बचना आवश्यक है।",
            "Strictly prohibit roof casting (chad dhalai), traveling South, making wooden beds/cots, or wood gathering."),
    }

    info = panchak_catalog.get(weekday_idx % 7, panchak_catalog[3])
    return PanchakStatus(
        is_panchak=True,
        panchak_type=info[0],
        panchak_type_bn=info[1],
        panchak_type_hi=info[2],
        severity=info[3],
        description=info[4],
        description_bn=info[5],
        description_hi=info[6],
        prohibited_activities=[info[7]],
    )


# -----------------------------------------------------------------------------
# Real-Time Planetary Drishti & Transit Yoga Matrix
# -----------------------------------------------------------------------------
def _calculate_planetary_drishti(
    planet_longitudes: dict[str, float],
    moon_sign_idx: int,
    moon_deg_in_sign: float,
    lang: Lang,
) -> list[PlanetaryDrishtiItem]:
    """Calculates classical Parashari aspects and transit conjunction yogas onto the Transit Moon."""
    drishtis: list[PlanetaryDrishtiItem] = []
    moon_total_lon = moon_sign_idx * 30.0 + moon_deg_in_sign

    # 1. Gajakesari Yoga Gochar (Jupiter in Kendra from Moon: 1st, 4th, 7th, 10th)
    if "Jupiter" in planet_longitudes:
        jup_lon = planet_longitudes["Jupiter"]
        jup_sign = int(jup_lon / 30.0) % 12
        house_diff = ((jup_sign - moon_sign_idx) % 12) + 1
        if house_diff in [1, 4, 7, 10]:
            drishtis.append(
                PlanetaryDrishtiItem(
                    aspecting_planet="Jupiter",
                    aspect_type=f"Kendra Sambandha ({house_diff}th House)",
                    yoga_name="Gajakesari Gochar Yoga",
                    yoga_name_bn="গজকেশরী গোচর যোগ",
                    yoga_name_hi="गजकेसरी गोचर योग",
                    is_positive=True,
                    impact="Gajakesari Gochar active! Bestows exceptional mental clarity, mentor blessings, diplomatic triumph, and financial stability today.",
                    impact_bn="গজকেশরী গোচর সক্রিয়! মানসিক স্থৈর্য, গুরুর আশীর্বাদ, কর্মে পদোন্নতি ও আর্থিক সুরক্ষার মহা শুভ যোগ।",
                    impact_hi="गजकेसरी गोचर सक्रिय! मानसिक शांति, गुरु का आशीर्वाद, मान-सम्मान और वित्तीय समृद्धि का योग।",
                    classical_remedy="Offer yellow flowers or bananas to Lord Vishnu or Guru.",
                    classical_remedy_bn="ভগবান বিষ্ণু অথবা বৃহস্পতি দেবের উদ্দেশ্যে হলুদ ফুল বা ফল নিবেদন করুন।",
                    classical_remedy_hi="भगवान विष्णु को पीले फूल और फल अर्पित करें।",
                )
            )

    # 2. Chandra-Mangala Gochar (Moon conjunct Mars)
    if "Mars" in planet_longitudes:
        mars_lon = planet_longitudes["Mars"]
        mars_sign = int(mars_lon / 30.0) % 12
        if mars_sign == moon_sign_idx:
            drishtis.append(
                PlanetaryDrishtiItem(
                    aspecting_planet="Mars",
                    aspect_type="Yuti (Conjunction)",
                    yoga_name="Chandra-Mangala Yoga",
                    yoga_name_bn="চন্দ্র-মঙ্গল ধন যোগ",
                    yoga_name_hi="चन्द्र-मंगल धन योग",
                    is_positive=True,
                    impact="Chandra-Mangala Yoga! Supercharges entrepreneurial drive, land deals, and decisive financial courage.",
                    impact_bn="চন্দ্র-মঙ্গল গোচর যোগ! উদ্যম বৃদ্ধি, জমিজমা সংক্রান্ত সিদ্ধান্ত ও আর্থিক লেনদেনে দারুণ আত্মবিশ্বাস পাবেন।",
                    impact_hi="चन्द्र-मंगल योग! अदम्य साहस, भूमि संबंधित लाभ और त्वरित व्यापारिक निर्णयों के लिए फलदायी।",
                    classical_remedy="Chant Hanuman Chalisa and donate jaggery.",
                    classical_remedy_bn="হনুমান চালিসা পাঠ করুন এবং গুড় বা মিষ্টি দান করুন।",
                    classical_remedy_hi="हनुमान चालीसा का पाठ करें और गुड़ का दान करें।",
                )
            )
        elif ((mars_sign - moon_sign_idx) % 12) + 1 in [4, 7, 8]:
            drishtis.append(
                PlanetaryDrishtiItem(
                    aspecting_planet="Mars",
                    aspect_type="Special Drishti (4th/7th/8th Aspect)",
                    yoga_name="Mangala Drishti",
                    yoga_name_bn="মঙ্গলের দৃষ্টি প্রভাব",
                    yoga_name_hi="मंगल की दृष्टि प्रभाव",
                    is_positive=False,
                    impact="Mars casts drishti on Moon. Guard against temperamental outbursts, driving haste, or blood pressure fluctuations.",
                    impact_bn="মঙ্গলের দৃষ্টির প্রভাব। রাগ নিয়ন্ত্রণ করুন, গাড়ি সাবধানে চালান এবং তাড়াহুড়ো করে সিদ্ধান্ত নেবেন না।",
                    impact_hi="मंगल की दृष्टि से मन में उत्तेजना रह सकती है। वाहन संभलकर चलाएं और वाद-विवाद से बचें।",
                    classical_remedy="Drink water from a silver cup and avoid arguments.",
                    classical_remedy_bn="রুপোর পাত্রে জল পান করুন এবং বিতর্ক থেকে বিরত থাকুন।",
                    classical_remedy_hi="चांदी के पात्र में जल पिएं और वाद-विवाद से बचें।",
                )
            )

    # 3. Visha Yoga / Saturn Drishti (Moon with or aspected by Saturn)
    if "Saturn" in planet_longitudes:
        sat_lon = planet_longitudes["Saturn"]
        sat_sign = int(sat_lon / 30.0) % 12
        house_diff = ((sat_sign - moon_sign_idx) % 12) + 1
        if house_diff == 1:
            drishtis.append(
                PlanetaryDrishtiItem(
                    aspecting_planet="Saturn",
                    aspect_type="Visha Yoga (Moon + Saturn Conjunction)",
                    yoga_name="Visha Yoga Gochar",
                    yoga_name_bn="বিষ যোগ গোচর",
                    yoga_name_hi="विष योग गोचर",
                    is_positive=False,
                    impact="Visha Yoga transit window. May cause melancholic thoughts or delay. Engage in meditation and avoid rash choices.",
                    impact_bn="বিষ যোগ গোচর। মন বিষাদগ্রস্ত হতে পারে বা কাজে কিছুটা বিলম্ব হবে। শিব আরাধনা ও ধ্যান শুভ।",
                    impact_hi="विष योग प्रभाव। मानसिक अवसाद या कार्य में देरी संभव है। धैर्य रखें और ॐ नमः शिवाय का जप करें।",
                    classical_remedy="Perform Shiva Jalabhishekam with raw milk.",
                    classical_remedy_bn="শিবলিঙ্গে কাঁচা দুধ ও গঙ্গাজল অর্পণ করুন।",
                    classical_remedy_hi="शिवलिंग पर कच्चा दूध और जल अर्पित करें।",
                )
            )
        elif house_diff in [3, 7, 10]:
            drishtis.append(
                PlanetaryDrishtiItem(
                    aspecting_planet="Saturn",
                    aspect_type=f"Saturn Aspect ({house_diff}th Drishti)",
                    yoga_name="Shani Drishti",
                    yoga_name_bn="শনির দৃষ্টি প্রভাব",
                    yoga_name_hi="शनि दृष्टि प्रभाव",
                    is_positive=False,
                    impact="Saturn's sobering aspect demands discipline, meticulous record-keeping, and emotional detachment.",
                    impact_bn="শনির দৃষ্টির কারণে কাজে নিষ্ঠা ও অধ্যবসায়ের প্রয়োজন। আবেগ পরিহার করে বাস্তবমুখী থাকুন।",
                    impact_hi="शनि की दृष्टि कार्य में अनुशासन और धैर्य की मांग करती है। जल्दबाजी न करें।",
                    classical_remedy="Light a mustard oil lamp under a Peepal tree in the evening.",
                    classical_remedy_bn="সন্ধ্যাবেলায় অশ্বত্থ গাছের তলায় সর্ষের তেলের প্রদীপ প্রজ্বলন করুন।",
                    classical_remedy_hi="संध्या समय पीपल के वृक्ष के नीचे सरसों के तेल का दीपक जलाएं।",
                )
            )

    # 4. Venus Harmony (Shukra-Chandra Trine / Kendra)
    if "Venus" in planet_longitudes:
        ven_lon = planet_longitudes["Venus"]
        ven_sign = int(ven_lon / 30.0) % 12
        diff = ((ven_sign - moon_sign_idx) % 12) + 1
        if diff in [1, 5, 9]:
            drishtis.append(
                PlanetaryDrishtiItem(
                    aspecting_planet="Venus",
                    aspect_type="Trikona / Shubh Sambandha",
                    yoga_name="Chandra-Shukra Sambandha",
                    yoga_name_bn="চন্দ্র-শুক্র শুভ সম্বন্ধ",
                    yoga_name_hi="चन्द्र-शुक्र शुभ संबंध",
                    is_positive=True,
                    impact="Chandra-Shukra harmony! Enhances creative magnetism, artistic taste, romantic harmony, and public relations.",
                    impact_bn="চন্দ্র-শুক্রের শুভ সম্বন্ধ! শিল্পকর্ম, প্রণয় সম্পর্ক, ফ্যাশন ও পারিবারিক আনন্দে চমৎকার সময়।",
                    impact_hi="चन्द्र-शुक्र योग! कलात्मक कार्यों, दांपत्य सुख और सामाजिक संबंधों के लिए अत्यंत सुखद।",
                    classical_remedy="Chant Mahalakshmi Ashtakam and donate white rice.",
                    classical_remedy_bn="মহালক্ষ্মী অষ্টকম পাঠ করুন এবং আতপ চাল বা চিনি দান করুন।",
                    classical_remedy_hi="महालक्ष्मी अष्टकम का पाठ करें व सफेद चावल दान करें।",
                )
            )

    return drishtis


# -----------------------------------------------------------------------------
# Ashtakavarga Transit Engine (Parashara SAV & BAV Point Multipliers)
# -----------------------------------------------------------------------------
PARASHARA_SAV_BASELINES: list[int] = [28, 28, 30, 27, 29, 29, 26, 28, 28, 30, 29, 28]
PARASHARA_BAV_MOON: list[int] = [4, 5, 5, 6, 4, 5, 3, 4, 5, 5, 4, 4]


def _calculate_ashtakavarga(sign_idx: int, lang: Lang) -> AshtakavargaTransitPoints:
    """Computes Sarvashtakavarga (SAV) and Moon Bhinnashtakavarga (BAV) transit points and verdicts."""
    sav = PARASHARA_SAV_BASELINES[sign_idx % 12]
    bav = PARASHARA_BAV_MOON[sign_idx % 12]

    if sav >= 30 and bav >= 5:
        grade_en = "Maha Shubh (Very Strong)"
        grade_bn = "মহা শুভ (পরম সুরক্ষা)"
        grade_hi = "महा शुभ (अत्यधिक बलवान)"
        multiplier = 1.15
    elif sav >= 28 and bav >= 4:
        grade_en = "Shubh (Auspicious)"
        grade_bn = "শুভ (অনুকূল)"
        grade_hi = "शुभ (अनुकूल)"
        multiplier = 1.05
    else:
        grade_en = "Madhyam / Alpaphala (Caution)"
        grade_bn = "মধ্যম / সাবধানী (কম বল)"
        grade_hi = "मध्यम / सतर्कता (कम बल)"
        multiplier = 0.90

    return AshtakavargaTransitPoints(
        sign_index=sign_idx,
        sarvashtakavarga_points=sav,
        moon_bhinnashtakavarga_points=bav,
        strength_grade=grade_bn if lang == "bn" else (grade_hi if lang == "hi" else grade_en),
        strength_grade_bn=grade_bn,
        strength_grade_hi=grade_hi,
        score_multiplier=multiplier,
    )


# -----------------------------------------------------------------------------
# Client's NEW NUMRO.docx §3.5 Daily Numerology Synergy Engine
# -----------------------------------------------------------------------------
def _calculate_numerology_synergy(
    birth_date_str: str | None,
    weekday_idx: int,
    lang: Lang,
) -> NumerologyDailySynergy | None:
    """Calculates Mulank & Bhagyank and pairs them with reigning Day Lord using client's exact §3.5 rules."""
    if not birth_date_str:
        return None

    try:
        parts = birth_date_str.strip().split("-")
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
    except Exception:
        return None

    def reduce_sum(n: int) -> int:
        while n > 9:
            n = sum(int(ch) for ch in str(n))
        return n

    mulank = reduce_sum(d)
    bhagyank = reduce_sum(y + m + d)

    day_lords = [1, 2, 9, 5, 3, 6, 8]
    day_lord_num = day_lords[weekday_idx % 7]

    planet_names = {
        1: "Sun", 2: "Moon", 3: "Jupiter", 4: "Rahu",
        5: "Mercury", 6: "Venus", 7: "Ketu", 8: "Saturn", 9: "Mars",
    }
    ruling_planet = planet_names.get(mulank, "Sun")

    friendship_table = {
        1: {"friends": [2, 3, 9], "neutrals": [5], "enemies": [4, 6, 7, 8]},
        2: {"friends": [1, 5], "neutrals": [3, 6, 8], "enemies": [4, 7, 9]},
        3: {"friends": [1, 2, 9], "neutrals": [5, 8], "enemies": [4, 6, 7]},
        4: {"friends": [5, 6, 8], "neutrals": [7, 3], "enemies": [1, 2, 9]},
        5: {"friends": [1, 6], "neutrals": [3, 8, 9], "enemies": [2, 4, 7]},
        6: {"friends": [5, 8], "neutrals": [3, 4, 7], "enemies": [1, 2, 9]},
        7: {"friends": [6, 8], "neutrals": [3, 5], "enemies": [1, 2, 4, 9]},
        8: {"friends": [4, 5, 6, 7], "neutrals": [3], "enemies": [1, 2, 9]},
        9: {"friends": [1, 2, 3], "neutrals": [5], "enemies": [4, 6, 7, 8]},
    }

    m_entry = friendship_table.get(mulank, {"friends": [], "neutrals": [], "enemies": []})
    if day_lord_num == mulank:
        rel = "Self / Royal Resonance"
        rel_bn = "আত্মীয় / রাজকীয় সম্পর্ক"
        rel_hi = "स्व-संबंध / राजयोग"
        score = 96
    elif day_lord_num in m_entry["friends"]:
        rel = "Friendly (Mitra)"
        rel_bn = "মিত্র সম্পর্ক (পরম শুভ)"
        rel_hi = "मित्र संबंध (शुभ)"
        score = 88
    elif day_lord_num in m_entry["neutrals"]:
        rel = "Neutral (Sama)"
        rel_bn = "সম সম্পর্ক (মধ্যম)"
        rel_hi = "सम संबंध (मध्यम)"
        score = 70
    else:
        rel = "Enemy (Shatru)"
        rel_bn = "শত্রু সম্পর্ক (সতর্কতা)"
        rel_hi = "शत्रु संबंध (सतर्कता)"
        score = 52

    advice_en = f"Mulank {mulank} vibrates in '{rel}' with today's Day Lord {day_lord_num}. Synergy score {score}%."
    advice_bn = f"আপনার মূলাঙ্ক {mulank}-এর সাথে আজকের বার অধিপতি সংখ্যা {day_lord_num}-এর সম্পর্ক '{rel_bn}'। শুভ সুরসংগতি সূচক {score}%।"
    advice_hi = f"आपके मूलांक {mulank} और दिन-स्वामी संख्या {day_lord_num} का संबंध '{rel_hi}' है। सद्भाव स्कोर {score}%।"

    return NumerologyDailySynergy(
        mulank=mulank,
        bhagyank=bhagyank,
        ruling_planet=ruling_planet,
        day_relationship=rel,
        day_relationship_bn=rel_bn,
        day_relationship_hi=rel_hi,
        synergy_score_pct=score,
        advice=advice_bn if lang == "bn" else (advice_hi if lang == "hi" else advice_en),
        advice_bn=advice_bn,
        advice_hi=advice_hi,
    )


# -----------------------------------------------------------------------------
# 24-Hour Cosmic Biorhythm Energy Engine
# -----------------------------------------------------------------------------
def _calculate_24h_biorhythm(
    horas_24: list[HoraItem],
    choghadiyas_16: list[ChoghadiyaItem],
    ashtakavarga_pts: int = 28,
    panchak_active: bool = False,
) -> list[BiorhythmHour]:
    """Generates an hour-by-hour cosmic energy index (0-100) combining reigning Hora, Choghadiya & Ashtakavarga."""
    biorhythm: list[BiorhythmHour] = []

    choghadiya_scores = {
        "Amrit": 95,
        "Shubh": 88,
        "Labh": 82,
        "Char": 75,
        "Rog": 42,
        "Kaal": 35,
        "Udveg": 40,
    }

    hora_planet_scores = {
        "Jupiter": 92,
        "Venus": 88,
        "Mercury": 80,
        "Moon": 78,
        "Sun": 76,
        "Mars": 55,
        "Saturn": 48,
    }

    for h in range(24):
        active_hora = horas_24[h] if h < len(horas_24) else horas_24[0]
        h_score = hora_planet_scores.get(active_hora.planet, 70)

        c_idx = (h * 16) // 24
        active_c = choghadiyas_16[c_idx] if c_idx < len(choghadiyas_16) else choghadiyas_16[0]
        c_score = choghadiya_scores.get(active_c.name, 70)

        sav_mod = (ashtakavarga_pts - 28) * 1.5
        panchak_mod = -4 if panchak_active else 0

        total_idx = int(max(20, min(99, (h_score * 0.55 + c_score * 0.45) + sav_mod + panchak_mod)))

        if total_idx >= 80:
            phase_en = "Peak Focus & Victory"
            phase_bn = "শীর্ষ উদ্যম ও শুভকাল"
            phase_hi = "सर्वोत्तम ऊर्जा व सफलता"
        elif total_idx >= 65:
            phase_en = "Favorable Action"
            phase_bn = "অনুকূল কর্মপ্রবাহ"
            phase_hi = "अनुकूल कार्य समय"
        elif total_idx >= 50:
            phase_en = "Moderate / Routine"
            phase_bn = "সাধারণ গতি"
            phase_hi = "सामान्य कार्य"
        else:
            phase_en = "Introspective / Caution"
            phase_bn = "ধীরস্থির ও সতর্কতা"
            phase_hi = "धैर्य व सावधानी"

        biorhythm.append(
            BiorhythmHour(
                hour=h,
                time_label=f"{h:02d}:00 - {(h+1)%24:02d}:00",
                energy_score=total_idx,
                dominant_graha=active_hora.planet,
                status=phase_en,
                status_bn=phase_bn,
                status_hi=phase_hi,
            )
        )
    return biorhythm


# -----------------------------------------------------------------------------
# Dual Transit Engine (Moon Gochar for Mind + Lagna Gochar for Physical Reality)
# -----------------------------------------------------------------------------
def _calculate_dual_transit(
    moon_house_transit: int,
    lagna_house_transit: int | None,
    sign_name_en: str,
    lang: Lang,
) -> DualTransitInsight | None:
    """Combines Moon Gochar (Internal emotional state) with Lagna Gochar (External worldly manifestations)."""
    if lagna_house_transit is None:
        return None

    house_keywords = {
        1: ("Vitality & Self-Transformation", "আত্মবিশ্বাস ও শারীরিক তেজ", "आत्मबल व नई शुरुआत"),
        2: ("Wealth Accumulation & Speech", "আর্থিক সঞ্চয় ও বাচনভঙ্গি", "धन संचय व वाणी"),
        3: ("Courage, Siblings & Initiatives", "সাহসিক পদক্ষেপ ও ভ্রাতৃসুখ", "पराक्रम व नवीन प्रयास"),
        4: ("Domestic Bliss, Property & Mother", "গৃহসুখ, যানবাহন ও মানসিক শান্তি", "गृहसुख व वाहन"),
        5: ("Intelligence, Romance & Speculation", "বুদ্ধিদীপ্ত সিদ্ধান্ত ও সৃষ্টিশীলতা", "ज्ञान, संतान व निवेश"),
        6: ("Victory over Debt, Disease & Rivals", "ঋণমুক্তি, রোগারোগ্য ও বিজয়", "शत्रु विजय व स्वास्थ्य"),
        7: ("Partnerships, Spouse & Public Deals", "অংশীদারি বাণিজ্য ও দাম্পত্য সুখ", "साझेदारी व दांपत्य"),
        8: ("Transformation, Research & Secrets", "গভীর গবেষণা ও অপ্রত্যাশিত পরিবর্তন", "गूढ़ अनुसंधान व परिवर्तन"),
        9: ("Dharma, Fortune & Higher Mentorship", "ভাগ্যোদয়, তীর্থভ্রমণ ও গুরুকৃপা", "भाग्योदय व तीर्थाटन"),
        10: ("Career Zenith, Authority & Prestige", "পেশাগত উন্নতি, প্রতিষ্ঠা ও কর্তৃত্ব", "कर्मक्षेत्र व पदोन्नति"),
        11: ("Fulfillment of Desires & Profit", "সর্বার্থসিদ্ধি ও বৃহৎ আর্থিক লাভ", "प्रचुर लाभ व मित्र सहयोग"),
        12: ("Expenditure, Foreign Realms & Rest", "বিদেশ সংযোগ, আধ্যাত্মিক ব্যয় ও বিশ্রাম", "व्यय, विदेश गमन व मोक्ष"),
    }

    m_info = house_keywords.get(moon_house_transit, ("General Influence", "সাধারণ প্রভাব", "सामान्य प्रभाव"))
    l_info = house_keywords.get(lagna_house_transit, ("General Influence", "সাধারণ প্রভাব", "सामान्य प्रभाव"))

    synthesis_en = (
        f"Your Moon transit through Bhava {moon_house_transit} governs mental perception ({m_info[0]}), "
        f"while your Lagna transit through Bhava {lagna_house_transit} manifests tangible physical events ({l_info[0]})."
    )
    synthesis_bn = (
        f"চন্দ্র গোচর {moon_house_transit}ম ভাবে মানসিক উপলব্ধি ({m_info[1]}) পরিচালনা করছে, "
        f"এবং লগ্ন গোচর {lagna_house_transit}ম ভাবে বাস্তব জাগতিক সাফল্য ({l_info[1]}) প্রকাশ ঘটাচ্ছে।"
    )
    synthesis_hi = (
        f"चन्द्र गोचर {moon_house_transit}वें भाव में मानसिक स्थिति ({m_info[2]}) को दर्शाता है, "
        f"जबकि लग्न गोचर {lagna_house_transit}वें भाव में वास्तविक घटनाओं ({l_info[2]}) को रूप देता है।"
    )

    harmony_score = 85 if (moon_house_transit in [1, 3, 5, 9, 10, 11] and lagna_house_transit in [1, 3, 5, 9, 10, 11]) else 70

    return DualTransitInsight(
        moon_transit_house=moon_house_transit,
        lagna_transit_house=lagna_house_transit,
        lagna_sign_name=sign_name_en,
        emotional_outlook=m_info[0],
        emotional_outlook_bn=m_info[1],
        emotional_outlook_hi=m_info[2],
        physical_event_outlook=l_info[0],
        physical_event_outlook_bn=l_info[1],
        physical_event_outlook_hi=l_info[2],
        synthesis_verdict=synthesis_en,
        synthesis_verdict_bn=synthesis_bn,
        synthesis_verdict_hi=synthesis_hi,
        dual_harmony_score=harmony_score,
    )


# -----------------------------------------------------------------------------
# KP Nakshatra Sub-Lord Precision Calculator
# -----------------------------------------------------------------------------
KP_LORDS_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
KP_DASHA_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]


def _calculate_kp_sublord(moon_lon: float, lang: Lang) -> dict[str, Any]:
    """Computes exact KP Nakshatra Lord, Sub-Lord and sub-arc degrees using Krishnamurti Paddhati rules."""
    nak_span = 360.0 / 27.0
    nak_idx = int(moon_lon / nak_span)
    nak_deg = moon_lon - (nak_idx * nak_span)

    nak_ruler_idx = nak_idx % 9
    nak_lord = KP_LORDS_ORDER[nak_ruler_idx]

    start_sub_idx = nak_ruler_idx
    sub_lord = nak_lord

    accumulated_deg = 0.0
    for step in range(9):
        curr_sub_idx = (start_sub_idx + step) % 9
        span_sub = (KP_DASHA_YEARS[curr_sub_idx] / 120.0) * nak_span
        if accumulated_deg + span_sub >= nak_deg:
            sub_lord = KP_LORDS_ORDER[curr_sub_idx]
            break
        accumulated_deg += span_sub

    return {
        "nakshatra_lord": nak_lord,
        "kp_sub_lord": sub_lord,
        "exact_arc": round(nak_deg, 4),
    }


def _calculate_gochar_vedha(
    moon_sign_idx: int,
    sign_idx: int,
    transit_house: int,
    planet_signs: dict[str, int],
    lang: Lang,
) -> tuple[bool, str | None, str | None]:
    """Detects if an auspicious transit house of the Moon is obstructed by Vedha."""
    if transit_house not in MOON_VEDHA_PAIRS:
        return False, None, None

    vedha_house = MOON_VEDHA_PAIRS[transit_house]
    # Zodiac sign index of the Vedha house
    target_sign_idx = (sign_idx + vedha_house - 1) % 12

    # Check which planets are in this sign (ignoring Moon itself)
    obstructing_planets: list[str] = [
        p for p, s_idx in planet_signs.items()
        if s_idx == target_sign_idx and p != "Moon"
    ]

    if not obstructing_planets:
        return False, None, None

    chosen_p = obstructing_planets[0]
    p_meta = PLANET_DISPLAY_NAMES.get(chosen_p, {"bn": chosen_p, "hi": chosen_p})

    if lang == "bn":
        desc = (
            f"চন্দ্র {transit_house}ম ভাবে অবস্থান করায় শুভ হলেও, {vedha_house}ম ভাবে "
            f"{p_meta['bn']}-এর গোচর বেধ (বাধা) রয়েছে। ফলে ফললাভে সামান্য বিলম্ব বা যোগাযোগে অতিরিক্ত ধৈর্য বজায় রাখা আবশ্যক।"
        )
    elif lang == "hi":
        desc = (
            f"चंद्रमा के {transit_house}वें भाव में शुभ गोचर पर {vedha_house}वें भाव में स्थित "
            f"{p_meta['hi']} का गोचर वेध है। इसलिए कार्यों में थोड़ा धैर्य और सावधानी आवश्यक है।"
        )
    else:
        desc = (
            f"While Moon in house {transit_house} is auspicious, {chosen_p}'s presence in house {vedha_house} "
            f"creates classical Gochar Vedha (obstruction), advising calm patience."
        )

    return True, chosen_p, desc


def _calculate_saturn_gochar(sign_idx: int, saturn_sign_idx: int, lang: Lang) -> str:
    """Calculates Saturn Sade Sati & Dhaiya status from Janma Rashi."""
    diff = (saturn_sign_idx - sign_idx) % 12 + 1
    if diff == 12:
        return "সাড়ে সাতি - ১ম পর্যায় (ব্যয় ও স্বাস্থ্য সতর্কতা)" if lang == "bn" else "साढ़े साती - प्रथम चरण (आरंभिक)" if lang == "hi" else "Sade Sati - Rising Phase (12th House)"
    elif diff == 1:
        return "সাড়ে সাতি - ২য় পর্যায় (কন্টক শনি / মধ্য পর্যায়)" if lang == "bn" else "साढ़े साती - द्वितीय चरण (मध्य / कंटक)" if lang == "hi" else "Sade Sati - Peak Phase (Janma Shani)"
    elif diff == 2:
        return "সাড়ে সাতি - ৩য় পর্যায় (নিস্তার / অবতরণ পর্ব)" if lang == "bn" else "साढ़े साती - तृतीय चरण (अंतिम)" if lang == "hi" else "Sade Sati - Setting Phase (2nd House)"
    elif diff == 4:
        return "কন্টক শনি ঢাইয়া (৪র্থ ভাব)" if lang == "bn" else "कंटक शनि ढैया (चतुर्थ भाव)" if lang == "hi" else "Kantaka Shani Dhaiya (4th House)"
    elif diff == 8:
        return "অষ্টম শনি ঢাইয়া (৮ম ভাব - অতি সতর্ক)" if lang == "bn" else "अष्टम शनि ढैया (अष्टम भाव - सतर्कता)" if lang == "hi" else "Ashtama Shani Dhaiya (8th House)"
    else:
        return "সাড়ে সাতি বা ঢাইয়া মুক্ত (সম্পূর্ণ শুভ)" if lang == "bn" else "साढ़े साती / ढैया मुक्त (शुभ)" if lang == "hi" else "Sade Sati / Dhaiya Free (Auspicious)"


def _calculate_jupiter_gochar(sign_idx: int, jupiter_sign_idx: int, lang: Lang) -> str:
    """Calculates Jupiter transit blessing or neutrality from Janma Rashi."""
    diff = (jupiter_sign_idx - sign_idx) % 12 + 1
    if diff in (2, 5, 7, 9, 11):
        return f"বৃহস্পতি অনুকূল গোচর ({diff}ম ভাব - গুরুকৃপা)" if lang == "bn" else f"बृहस्पति शुभ गोचर ({diff}वां भाव - कृपा)" if lang == "hi" else f"Jupiter Auspicious Transit ({diff}th House)"
    else:
        return f"বৃহস্পতি সাধারণ গোচর ({diff}ম ভাব)" if lang == "bn" else f"बृहस्पति सामान्य गोचर ({diff}वां भाव)" if lang == "hi" else f"Jupiter Neutral Transit ({diff}th House)"


def _calculate_tara_bala(transit_nak_idx: int, birth_nak_idx: int) -> TaraBalaSummary:
    """Calculates classical 9-Tara Navatara Bala for any birth nakshatra against transit nakshatra."""
    count = ((transit_nak_idx - birth_nak_idx) % 27) + 1
    tara_idx = ((count - 1) % 9) + 1
    defn = TARABALA_DEFINITIONS[tara_idx - 1]

    score_map = {
        1: 65,  # Janma
        2: 95,  # Sampat
        3: 42,  # Vipat
        4: 90,  # Kshema
        5: 45,  # Pratyak
        6: 95,  # Sadhana
        7: 35,  # Naidhana / Vadha
        8: 92,  # Mitra
        9: 98,  # Param Mitra
    }

    verdict_map = {
        1: {"en": "Body & Self-Care", "bn": "শারীরিক সত্ত্বা ও আত্মরক্ষা", "hi": "शरीर और स्वास्थ्य का ध्यान"},
        2: {"en": "Great Wealth & Prosperity", "bn": "ধনসম্পদ, সমৃদ্ধি ও আর্থিক লাভ", "hi": "धन लाभ और संपन्नता"},
        3: {"en": "Hazard & Impediment", "bn": "বাধা, ক্ষতি ও সতর্কতা", "hi": "बाधा और अड़चनें"},
        4: {"en": "Well-Being & Protection", "bn": "শান্তি, মঙ্গল ও পরিবার কল্যাণ", "hi": "कल्याण, आरोग्य और सुरक्षा"},
        5: {"en": "Opposition & Enmity", "bn": "বিরোধ, বিলম্ব ও ধৈর্য", "hi": "विरोध और असफलता"},
        6: {"en": "Achievement & Mastery", "bn": "লক্ষ্যসাধন, পরীক্ষা ও সর্বসিদ্ধি", "hi": "सिद्धि और महान सफलता"},
        7: {"en": "Crisis & Danger", "bn": "সংকট, বিনাশ ও চরম সতর্কতা", "hi": "गंभीर संकट - सतर्कता आवश्यक"},
        8: {"en": "Friendship & Alliance", "bn": "বন্ধুত্ব, সৌহার্দ্য ও সহযোগিতা", "hi": "मित्रता और शुभ संबंध"},
        9: {"en": "Supreme Ally & Fortune", "bn": "পরম মিত্র, উচ্চ প্রাপ্তি ও সৌভাগ্য", "hi": "परम सौभाग्य और मनोकामना पूर्ति"},
    }

    return TaraBalaSummary(
        tara_index=tara_idx,
        tara_name=defn["name_en"],
        tara_name_bn=defn["name_bn"],
        tara_name_hi=defn["name_hi"],
        is_auspicious=defn["is_auspicious"],
        score_percent=score_map.get(tara_idx, 75),
        verdict=verdict_map[tara_idx]["en"],
        verdict_bn=verdict_map[tara_idx]["bn"],
        verdict_hi=verdict_map[tara_idx]["hi"],
        guidance=defn["significance_en"],
        guidance_bn=defn["significance_bn"],
        guidance_hi=defn["significance_hi"],
    )


def calculate_daily_horoscope(payload: DailyHoroscopeRequest) -> DailyHoroscopeResponse:
    """Computes complete 100% in-house Daily Horoscope with Vedic Horas, Gochar Vedha, & Personalization."""
    _require_swisseph()

    lang: Lang = payload.language or "en"
    tz_offset = payload.timezone if payload.timezone is not None else 5.5

    # Determine target date
    if payload.date:
        try:
            target_date = datetime.strptime(payload.date.strip(), "%Y-%m-%d")
        except ValueError:
            target_date = datetime.now(timezone(timedelta(hours=tz_offset)))
    else:
        target_date = datetime.now(timezone(timedelta(hours=tz_offset)))

    # Midday in local time corresponds to hour in UTC:
    local_midday = 12.0
    hour_utc = (local_midday - tz_offset) % 24.0

    jd = _calculate_julian_day(target_date, hour_utc)

    # Set Lahiri Sidereal mode (standard Vedic ayanamsha)
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    # Calculate astronomical Moon and Sun positions
    moon_res, _ = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL | swe.FLG_SPEED)
    sun_res, _ = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL | swe.FLG_SPEED)

    moon_lon = float(moon_res[0]) % 360.0
    sun_lon = float(sun_res[0]) % 360.0

    moon_sign_idx = int(moon_lon / 30.0) % 12
    sun_sign_idx = int(sun_lon / 30.0) % 12
    deg_in_sign = moon_lon % 30.0

    # Multi-planet positions for Gochar Vedha and Saturn/Jupiter transits
    planets_to_calc = [
        ("Sun", swe.SUN),
        ("Moon", swe.MOON),
        ("Mars", swe.MARS),
        ("Mercury", swe.MERCURY),
        ("Jupiter", swe.JUPITER),
        ("Venus", swe.VENUS),
        ("Saturn", swe.SATURN),
        ("Rahu", swe.MEAN_NODE),
    ]
    planet_signs: dict[str, int] = {}
    planet_longitudes: dict[str, float] = {}
    for p_name, p_code in planets_to_calc:
        p_res, _ = swe.calc_ut(jd, p_code, swe.FLG_SIDEREAL | swe.FLG_SPEED)
        p_lon = float(p_res[0]) % 360.0
        planet_signs[p_name] = int(p_lon / 30.0) % 12
        planet_longitudes[p_name] = p_lon

    # Ketu is exactly 180 degrees opposite Rahu
    rahu_lon_deg = float(swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SIDEREAL | swe.FLG_SPEED)[0][0]) % 360.0
    ketu_lon_deg = (rahu_lon_deg + 180.0) % 360.0
    planet_signs["Ketu"] = int(ketu_lon_deg / 30.0) % 12

    # Nakshatra calculation: 27 nakshatras in 360 degrees
    span = 360.0 / 27.0
    nak_idx = int(moon_lon / span) % 27
    offset_in_nak = moon_lon % span
    pada = int(offset_in_nak / (span / 4.0)) + 1

    # Weekday determination
    weekday_idx = target_date.weekday()  # Monday = 0, Sunday = 6 in python
    vara_idx = (weekday_idx + 1) % 7
    vara_data = VARA_INFO[vara_idx]
    weekday_en = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][weekday_idx]

    # Calculate Panchang Elements
    tithi_data = calculate_tithi(sun_lon, moon_lon, lang)
    yoga_data = calculate_yoga(sun_lon, moon_lon, lang)
    karana_data = calculate_karana(sun_lon, moon_lon, lang)

    # Astronomical Sunrise & Sunset using Swiss Ephemeris
    geopos = (payload.longitude, payload.latitude, 0.0)
    jd_day_start = swe.julday(target_date.year, target_date.month, target_date.day, 0.0)

    try:
        rise_res = swe.rise_trans(jd_day_start, swe.SUN, swe.CALC_RISE, geopos)
        _, _, _, rise_ut = swe.revjul(rise_res[1][0])
        sunrise_h = (rise_ut + tz_offset) % 24.0
    except Exception:
        sunrise_h = 5.75  # ~05:45 AM fallback

    try:
        set_res = swe.rise_trans(jd_day_start, swe.SUN, swe.CALC_SET, geopos)
        _, _, _, set_ut = swe.revjul(set_res[1][0])
        sunset_h = (set_ut + tz_offset) % 24.0
    except Exception:
        sunset_h = 17.5  # ~05:30 PM fallback

    try:
        next_rise_res = swe.rise_trans(jd_day_start + 1.0, swe.SUN, swe.CALC_RISE, geopos)
        _, _, _, next_rise_ut = swe.revjul(next_rise_res[1][0])
        next_sunrise_h = (next_rise_ut + tz_offset) % 24.0
    except Exception:
        next_sunrise_h = sunrise_h

    sunrise_time = _fmt_time_str(sunrise_h)
    sunset_time = _fmt_time_str(sunset_h)

    # Abhijit Muhurat: ~24 mins before and after solar midday
    midday_h = (sunrise_h + sunset_h) / 2.0 if sunset_h > sunrise_h else ((sunrise_h + sunset_h + 24.0) / 2.0) % 24.0
    abhijit_str = f"{_fmt_time_str(midday_h - 0.4)} – {_fmt_time_str(midday_h + 0.4)}"

    # Rahu Kaal window from weekday
    r_start, r_end = vara_data["rahu_period"]
    rahu_kaal_str = f"{_fmt_time_str(r_start)} – {_fmt_time_str(r_end)}"

    # 24 Planetary Horas Calculation
    horas_list = _calculate_24_horas(sunrise_h, sunset_h, next_sunrise_h, vara_data["lord"])

    # Disha Shoola & Remedies
    disha_info = DISHA_SHOOLA_DATA.get(weekday_en, DISHA_SHOOLA_DATA["Sunday"])
    disha_shoola_text = disha_info[f"dir_{lang}"] if f"dir_{lang}" in disha_info else disha_info["dir"]
    disha_remedy_text = disha_info[f"remedy_{lang}"] if f"remedy_{lang}" in disha_info else disha_info["remedy"]

    # 16 Vedic Choghadiyas (8 Day + 8 Night)
    choghadiyas_16 = _calculate_16_choghadiya(sunrise_h, sunset_h, next_sunrise_h, weekday_idx, lang)

    # Vedic Panchak Status (Dhanishta 3rd/4th pada to Revati)
    panchak_info = _calculate_panchak(moon_lon, weekday_idx, lang)

    # Real-time Planetary Drishtis on Moon
    drishtis_on_moon = _calculate_planetary_drishti(planet_longitudes, moon_sign_idx, deg_in_sign, lang)

    # KP Sub-Lord
    kp_info = _calculate_kp_sublord(moon_lon, lang)

    # Chandra Bala Favorable Signs (Moon transits houses 1, 3, 6, 7, 10, 11)
    favorable_rashis_indices = [
        (moon_sign_idx - (h - 1)) % 12 for h in [1, 3, 6, 7, 10, 11]
    ]
    favorable_rashis_names = [
        SIGN_NAMES_ORDERED[idx].get(lang, SIGN_NAMES_ORDERED[idx]["en"])
        for idx in favorable_rashis_indices
    ]

    panchang_summary = DailyPanchangSummary(
        tithi=tithi_data.get("name", ""),
        paksha=tithi_data.get("paksha", ""),
        nakshatra=NAKSHATRAS_DATA[nak_idx]["name"] if nak_idx < len(NAKSHATRAS_DATA) else f"Nakshatra #{nak_idx+1}",
        nakshatra_pada=pada,
        yoga=yoga_data.get("name", ""),
        karana=karana_data.get("name", ""),
        vara=vara_data.get(lang, vara_data["en"]),
        sunrise=sunrise_time,
        sunset=sunset_time,
        abhijit_muhurat=abhijit_str,
        rahu_kaal=rahu_kaal_str,
        disha_shoola=disha_shoola_text,
        disha_remedy=disha_remedy_text,
        favorable_chandra_rashis=favorable_rashis_names,
        horas=horas_list,
        choghadiya=choghadiyas_16,
        panchak=panchak_info,
    )

    # Format Moon degree string
    deg_in_sign = moon_lon % 30.0
    deg_int = int(deg_in_sign)
    deg_min = int((deg_in_sign - deg_int) * 60)
    moon_deg_formatted = f"{deg_int}° {deg_min:02d}'"

    moon_sign_meta = SIGN_NAMES_ORDERED[moon_sign_idx]
    sun_sign_meta = SIGN_NAMES_ORDERED[sun_sign_idx]

    # Personalized Profile (if birth nakshatra or birth chart is supplied)
    personalized_profile: PersonalizedNakshatraProfile | None = None
    target_birth_nak_idx: int | None = payload.birth_nakshatra_index

    if target_birth_nak_idx is None and payload.birth_date:
        try:
            b_date = datetime.strptime(payload.birth_date.strip(), "%Y-%m-%d")
            b_hour = 12.0
            if payload.birth_time:
                try:
                    parts = payload.birth_time.strip().split(":")
                    b_hour = float(parts[0]) + float(parts[1]) / 60.0
                except Exception:
                    b_hour = 12.0
            b_hour_utc = (b_hour - tz_offset) % 24.0
            b_jd = _calculate_julian_day(b_date, b_hour_utc)
            b_moon_res, _ = swe.calc_ut(b_jd, swe.MOON, swe.FLG_SIDEREAL | swe.FLG_SPEED)
            b_moon_lon = float(b_moon_res[0]) % 360.0
            target_birth_nak_idx = int(b_moon_lon / (360.0 / 27.0)) % 27
        except Exception as e:
            logger.warning(f"Could not compute natal chart from birth_date: {e}")

    if target_birth_nak_idx is not None and 0 <= target_birth_nak_idx < len(NAKSHATRAS_MASTER):
        b_nak_master = NAKSHATRAS_MASTER[target_birth_nak_idx]
        tara_summary = _calculate_tara_bala(nak_idx, target_birth_nak_idx)
        personalized_profile = PersonalizedNakshatraProfile(
            birth_nakshatra_index=target_birth_nak_idx,
            birth_nakshatra_name=b_nak_master["name_en"],
            birth_nakshatra_name_bn=b_nak_master["name_bn"],
            birth_nakshatra_name_hi=b_nak_master["name_hi"],
            birth_nakshatra_lord=b_nak_master["lord"],
            birth_nakshatra_deity=b_nak_master.get(f"deity_{lang}", b_nak_master["deity_en"]),
            sacred_tree=b_nak_master.get(f"sacred_tree_{lang}", b_nak_master["sacred_tree_en"]),
            beej_mantra=b_nak_master["beej_mantra"],
            tara_bala=tara_summary,
        )

    # Target sign filtering
    target_signs = list(range(12))
    if payload.sign:
        req_sign = payload.sign.strip().lower()
        matched = None
        for idx, s in enumerate(SIGN_NAMES_ORDERED):
            if req_sign in (s["en"].lower(), s["bn"].lower(), s["hi"].lower(), s["sa"].lower(), str(idx)):
                matched = idx
                break
        if matched is not None:
            target_signs = [matched]

    # Compute Daily Horoscope for each target sign
    sign_horoscopes: list[DailySignHoroscope] = []

    for sign_idx in target_signs:
        sign_meta = SIGN_NAMES_ORDERED[sign_idx]
        client_rashi_data = RASHIS_DATA[sign_idx] if sign_idx < len(RASHIS_DATA) else {}
        rashi_extra = RASHI_CLASSICAL_EXTRAS[sign_idx] if sign_idx < len(RASHI_CLASSICAL_EXTRAS) else {}

        # Transit house = (Moon sign - Rashi sign) % 12 + 1
        transit_house = (moon_sign_idx - sign_idx) % 12 + 1

        # Fetch template for this house and language
        house_templates = HOUSE_GOCHAR_TEMPLATES.get(transit_house, HOUSE_GOCHAR_TEMPLATES[1])
        lang_template = house_templates.get(lang, house_templates["en"])

        # Base scores
        base_scores = HOUSE_BASE_SCORES.get(transit_house, HOUSE_BASE_SCORES[1])

        # Minor harmonic variance based on day's lord vs sign lord
        is_favorable_day = (vara_data["lord"] == sign_meta["lord"])
        day_bonus = 3 if is_favorable_day else 0

        # Chandrashtama detection (Moon transiting 8th house)
        is_chandrashtama = (transit_house == 8)
        chandrashtama_adv: str | None = None
        if is_chandrashtama:
            if lang == "bn":
                chandrashtama_adv = (
                    "⚠️ আজ আপনার রাশিতে চন্দ্রাষ্টম চলছে। এটি শাস্ত্রীয়ভাবে অত্যন্ত সংবেদনশীল গোচর (৪৮ ঘণ্টা)। "
                    "এই সময় নতুন কোনো ঝুঁকিপূর্ণ আর্থিক চুক্তি স্বাক্ষর, ঋণ লেনদেন, দীর্ঘ দূরত্বের বিপজ্জনক যাত্রা ও বিতর্ক "
                    "সম্পূর্ণরূপে পরিহার করুন। মানসিক প্রশান্তির জন্য 'ॐ সোঁ সোমায় নমঃ' জপ করুন এবং সাদা মিষ্টি বা দুধ দান করুন।"
                )
            elif lang == "hi":
                chandrashtama_adv = (
                    "⚠️ आज आपकी राशि में चंद्राष्टम गोचर चल रहा है। यह अत्यंत संवेदनशील समय है। कोई भी नया जोखिम भरा "
                    "निवेश या विवाद से बचें। शांति हेतु 'ॐ सों सोमाय नमः' का जाप करें और सफेद वस्तुएं दान करें।"
                )
            else:
                chandrashtama_adv = (
                    "⚠️ Today your sign is experiencing Chandrashtama (Moon transiting 8th house). Practice deep discretion, "
                    "postpone critical financial contracts, avoid heated debates, and recite 'Om Som Somaya Namah'."
                )

        # Classical Gochar Vedha check
        vedha_active, vedha_planet, vedha_desc = _calculate_gochar_vedha(
            moon_sign_idx, sign_idx, transit_house, planet_signs, lang
        )

        # Saturn Sade Sati & Dhaiya status
        sade_sati_status = _calculate_saturn_gochar(sign_idx, planet_signs.get("Saturn", 11), lang)

        # Jupiter transit status
        guru_status = _calculate_jupiter_gochar(sign_idx, planet_signs.get("Jupiter", 3), lang)

        # Tara Bala for this sign
        sign_tara_bala: TaraBalaSummary | None = None
        if target_birth_nak_idx is not None:
            # If user specified a birth nakshatra, apply it
            sign_tara_bala = _calculate_tara_bala(nak_idx, target_birth_nak_idx)
        else:
            # Otherwise use primary nakshatra of this sign (each sign spans 2.25 nakshatras)
            primary_nak = int(sign_idx * 2.25)
            sign_tara_bala = _calculate_tara_bala(nak_idx, primary_nak)

        # Score adjustment based on Tara Bala and Vedha
        tara_adj = 0
        if sign_tara_bala:
            if sign_tara_bala.tara_index in (2, 6, 9):
                tara_adj += 5
            elif sign_tara_bala.tara_index in (4, 8):
                tara_adj += 3
            elif sign_tara_bala.tara_index in (3, 5):
                tara_adj -= 5
            elif sign_tara_bala.tara_index == 7:
                tara_adj -= 8

        vedha_adj = -4 if vedha_active else 0
        chandrashtama_adj = -6 if is_chandrashtama else 0

        overall_sc = min(98, max(42, base_scores["overall"] + day_bonus + tara_adj + vedha_adj + chandrashtama_adj))
        career_sc = min(98, max(40, base_scores["career"] + day_bonus + (tara_adj // 2) + vedha_adj))
        love_sc = min(98, max(40, base_scores["love"] + day_bonus + (tara_adj // 2)))
        finance_sc = min(98, max(40, base_scores["finance"] + day_bonus + tara_adj + vedha_adj))
        health_sc = min(98, max(40, base_scores["health"] + day_bonus + (tara_adj // 2) + chandrashtama_adj))

        # Dynamic Lucky number based on Rashi lord and transit
        lucky_nums: list[int] = client_rashi_data.get("lucky_numbers", [sign_idx + 1])
        chosen_lucky_num = lucky_nums[(transit_house + vara_idx) % len(lucky_nums)]

        # Lucky color from client's Rashi rules
        chosen_color = client_rashi_data.get("lucky_color", "Golden Saffron")
        if lang == "bn":
            chosen_color_text = "স্বর্ণালী গেরুয়া ও লাল" if "Red" in chosen_color else "শুভ্র সাদা ও হলুদ"
        elif lang == "hi":
            chosen_color_text = "सुनहरा और लाल" if "Red" in chosen_color else "सफेद और पीला"
        else:
            chosen_color_text = chosen_color

        # Auspicious window for this sign
        lucky_time_window = abhijit_str if overall_sc >= 75 else "02:30 PM – 04:00 PM"

        # Remedy from client's Rashi rules & classical texts
        client_remedies: list[str] = client_rashi_data.get("beneficial_actions_and_remedies", [])
        if client_remedies:
            remedy_text = client_remedies[transit_house % len(client_remedies)]
        else:
            remedy_text = f"Chant Om Namah Shivaya and offer water to the Sun ({sign_meta['lord']})."

        beej_mantra = rashi_extra.get("beej_mantra_hi" if lang == "hi" else "beej_mantra", "")
        charity_dana = rashi_extra.get(f"charity_{lang}", rashi_extra.get("charity_en", ""))

        sign_horoscopes.append(
            DailySignHoroscope(
                sign_index=sign_idx,
                sign_name=sign_meta.get(lang, sign_meta["en"]),
                sign_name_sanskrit=sign_meta["sa"],
                symbol=sign_meta["symbol"],
                transit_house=transit_house,
                transit_house_name=lang_template["name"],
                gochar_verdict=lang_template["verdict"],
                overall_score=overall_sc,
                career_score=career_sc,
                love_score=love_sc,
                finance_score=finance_sc,
                health_score=health_sc,
                summary=lang_template["summary"],
                career_prediction=lang_template["career"],
                love_prediction=lang_template["love"],
                finance_prediction=lang_template["finance"],
                health_prediction=lang_template["health"],
                lucky_number=chosen_lucky_num,
                lucky_color=chosen_color_text,
                lucky_time=lucky_time_window,
                remedy=remedy_text,
                favorable_direction=sign_meta["dir"],
                is_chandrashtama=is_chandrashtama,
                chandrashtama_advice=chandrashtama_adv,
                vedha_active=vedha_active,
                vedha_planet=vedha_planet,
                vedha_description=vedha_desc,
                sade_sati_status=sade_sati_status,
                guru_gochar_verdict=guru_status,
                beej_mantra=beej_mantra,
                charity_dana=charity_dana,
                tara_bala=sign_tara_bala,
                ashtakavarga=_calculate_ashtakavarga(sign_idx, lang),
                client_classifications=client_rules.get_sign_profile(sign_idx, lang),
                nakshatra_pada_shift=kp_info,
                planetary_drishtis=drishtis_on_moon,
            )
        )

    # 24-Hour Biorhythm Timeline
    biorhythm_timeline = _calculate_24h_biorhythm(
        horas_list, choghadiyas_16, ashtakavarga_pts=28, panchak_active=panchak_info.is_panchak
    )

    # Daily Numerology Synergy
    num_synergy = _calculate_numerology_synergy(payload.birth_date, weekday_idx, lang)

    # Dual Transit Insight (Moon vs Lagna)
    dual_insight = None
    if payload.birth_lagna_index is not None and 0 <= payload.birth_lagna_index < 12:
        lagna_transit_house = (moon_sign_idx - payload.birth_lagna_index) % 12 + 1
        m_house = (moon_sign_idx - (payload.birth_rashi_index if payload.birth_rashi_index is not None else moon_sign_idx)) % 12 + 1
        dual_insight = _calculate_dual_transit(m_house, lagna_transit_house, moon_sign_meta["en"], lang)

    return DailyHoroscopeResponse(
        date=target_date.strftime("%Y-%m-%d"),
        day_of_week=vara_data.get(lang, vara_data["en"]),
        vara_lord=vara_data["lord"],
        moon_sign=moon_sign_meta.get(lang, moon_sign_meta["en"]),
        moon_sign_sanskrit=moon_sign_meta["sa"],
        moon_degree=moon_deg_formatted,
        sun_sign=sun_sign_meta.get(lang, sun_sign_meta["en"]),
        panchang=panchang_summary,
        signs=sign_horoscopes,
        personalized_profile=personalized_profile,
        numerology_synergy=num_synergy,
        biorhythm_timeline=biorhythm_timeline,
        dual_transit=dual_insight,
        calculation_meta={
            "engine": "Swiss Ephemeris 2.10 (pyswisseph)",
            "ayanamsha": "Lahiri (Chitra Paksha)",
            "calculation_method": "Vedic Gochar (Moon Transit Relative to Janma Rashi) with Vedha & 24 Horas",
            "precision": "Astronomical sub-second arc accuracy",
            "observer_coordinates": f"{payload.latitude}°N, {payload.longitude}°E",
        },
    )
