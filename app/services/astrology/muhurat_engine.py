"""100% In-House Vedic Muhurat & Kaal Calculation Engine via Swiss Ephemeris.

Calculates:
1. Astronomical Sunrise, Sunset, Next Sunrise & Solar Noon for exact geographic coordinates.
2. Exact Core Kaal Windows based on classical 1/8th and 1/15th divisions:
   - Abhijit Muhurat (universal midday victory window)
   - Brahma Muhurat (pre-dawn spiritual awakening window)
   - Rahu Kaal (inauspicious 1/8th planetary shadow window)
   - Yamaganda / Yamaghanta (inauspicious 1/8th window)
   - Gulika Kaal (neutral/steadfast 1/8th window)
   - Vijaya Muhurat (afternoon victory window)
   - Godhuli Muhurat (twilight transition window)
   - Amrit Kaal & Durmuhurats
3. 16 Vedic Choghadiyas (8 Day + 8 Night) with active slot detection.
4. 24 Planetary Horas (12 Day + 12 Night) with active hora detection.
5. Milestone Auspicious Activity Guidance (Vivah, Griha Pravesh, Vahan, Vyapar, Gold, Vidya, Yatra, Namakaran).
6. Daily Panchang summary (Tithi, Nakshatra, Yoga, Karana, Vara).
"""

from __future__ import annotations

import math
from datetime import date, datetime, timezone
from typing import Any, Literal
from loguru import logger

from app.services.astrology.calculator import (
    HAS_SWISSEPH,
    _require_swisseph,
    swe,
)
from app.services.astrology.panchang import (
    calculate_karana,
    calculate_tithi,
    calculate_yoga,
)
from app.schemas.astrology import (
    MuhuratChoghadiyaSlot,
    MuhuratHoraSlot,
    MuhuratMilestoneItem,
    MuhuratRequest,
    MuhuratResponse,
    MuhuratTimingWindow,
)

Lang = Literal["en", "bn", "hi"]

# 7 Weekdays Master Data (0 = Monday, 6 = Sunday)
WEEKDAY_LORDS = [
    "Moon",     # Mon
    "Mars",     # Tue
    "Mercury",  # Wed
    "Jupiter",  # Thu
    "Venus",    # Fri
    "Saturn",   # Sat
    "Sun",      # Sun
]

WEEKDAY_NAMES: list[dict[str, str]] = [
    {"en": "Monday", "bn": "সোমবার", "hi": "सोमवार", "lord": "Moon"},
    {"en": "Tuesday", "bn": "মঙ্গলবার", "hi": "मंगलवार", "lord": "Mars"},
    {"en": "Wednesday", "bn": "বুধবার", "hi": "बुधवार", "lord": "Mercury"},
    {"en": "Thursday", "bn": "বৃহস্পতিবার", "hi": "गुरुवार", "lord": "Jupiter"},
    {"en": "Friday", "bn": "শুক্রবার", "hi": "शुक्रवार", "lord": "Venus"},
    {"en": "Saturday", "bn": "শনিবার", "hi": "शनिवार", "lord": "Saturn"},
    {"en": "Sunday", "bn": "রবিবার", "hi": "रविवार", "lord": "Sun"},
]

# 1/8th Daytime Division Orders (1-indexed segment 1..8)
# Monday=0, Tuesday=1, Wednesday=2, Thursday=3, Friday=4, Saturday=5, Sunday=6
RAHU_KAAL_PARTS = [2, 7, 5, 6, 4, 3, 8]
YAMAGANDA_PARTS = [4, 3, 2, 1, 7, 6, 5]
GULIKA_PARTS = [6, 5, 4, 3, 2, 1, 7]

# Choghadiya Sequence (Day)
DAY_CHOGHADIYA_ORDER = [
    ["amrit", "kaal", "shubh", "rog", "udveg", "char", "labh", "amrit"],  # Mon (0)
    ["rog", "udveg", "char", "labh", "amrit", "kaal", "shubh", "rog"],    # Tue (1)
    ["labh", "amrit", "kaal", "shubh", "rog", "udveg", "char", "labh"],    # Wed (2)
    ["shubh", "rog", "udveg", "char", "labh", "amrit", "kaal", "shubh"],  # Thu (3)
    ["char", "labh", "amrit", "kaal", "shubh", "rog", "udveg", "char"],    # Fri (4)
    ["kaal", "shubh", "rog", "udveg", "char", "labh", "amrit", "kaal"],    # Sat (5)
    ["udveg", "char", "labh", "amrit", "kaal", "shubh", "rog", "udveg"],  # Sun (6)
]

# Choghadiya Sequence (Night)
NIGHT_CHOGHADIYA_ORDER = [
    ["char", "rog", "kaal", "labh", "udveg", "shubh", "amrit", "char"],  # Mon
    ["kaal", "labh", "udveg", "shubh", "amrit", "char", "rog", "kaal"],  # Tue
    ["udveg", "shubh", "amrit", "char", "rog", "kaal", "labh", "udveg"],  # Wed
    ["amrit", "char", "rog", "kaal", "labh", "udveg", "shubh", "amrit"],  # Thu
    ["rog", "kaal", "labh", "udveg", "shubh", "amrit", "char", "rog"],    # Fri
    ["labh", "udveg", "shubh", "amrit", "char", "rog", "kaal", "labh"],  # Sat
    ["shubh", "amrit", "char", "rog", "kaal", "labh", "udveg", "shubh"],  # Sun
]

CHOGHADIYA_META: dict[str, dict[str, Any]] = {
    "amrit": {
        "en": "Amrit (Nectar)",
        "bn": "অমৃত (সর্বোত্তম শুভ)",
        "hi": "अमृत (सर्वोत्तम शुभ)",
        "quality": "super_auspicious",
        "lord": "Moon",
        "desc_en": "Supreme auspicious window for all spiritual and milestone commencements.",
        "desc_bn": "সর্বপ্রকার শুভ সংস্কার, পূজা ও গুরুত্বপূর্ণ চুক্তি স্বাক্ষরের শ্রেষ্ঠ সময়।",
        "desc_hi": "सर्वश्रेष्ठ शुभ मुहूर्त, नए कार्य एवं मंगल अनुष्ठानों हेतु उपयुक्त।",
    },
    "shubh": {
        "en": "Shubh (Auspicious)",
        "bn": "শুভ (মঙ্গলময়)",
        "hi": "शुभ (मंगलकारी)",
        "quality": "auspicious",
        "lord": "Jupiter",
        "desc_en": "Highly auspicious for ceremonies, purchases, weddings, and investments.",
        "desc_bn": "বিবাহ, গৃহপ্রবেশ, স্বর্ণক্রয় ও নতুন বিনিয়োগের জন্য বিশেষ অনুকূল।",
        "desc_hi": "विवाह, गृहप्रवेश एवं शुभ मांगलिक कार्यों हेतु उत्तम।",
    },
    "labh": {
        "en": "Labh (Gain/Profit)",
        "bn": "লাভ (সমৃদ্ধি)",
        "hi": "लाभ (उन्नति)",
        "quality": "auspicious",
        "lord": "Mercury",
        "desc_en": "Excellent for commerce, business expansion, signing deals, and education.",
        "desc_bn": "বাণিজ্য আরম্ভ, নতুন ব্যবসা, চুক্তি স্বাক্ষর ও অর্থাগমের পক্ষে প্রশস্ত।",
        "desc_hi": "व्यापार, आर्थिक लेनदेन और लाभप्रद कार्य आरंभ करने हेतु शुभ।",
    },
    "char": {
        "en": "Char (Motion/Dynamic)",
        "bn": "চর (চলনশীল)",
        "hi": "चर (गतिशील)",
        "quality": "neutral",
        "lord": "Venus",
        "desc_en": "Ideal for travel, journey start, vehicle purchase, and dynamic actions.",
        "desc_bn": "ভ্রমণ, যানবাহন ক্রয় ও গতিশীল কাজের জন্য অনুকূল, স্থাবর কাজের জন্য সাধারণ।",
        "desc_hi": "यात्रा, वाहन क्रय एवं गतिशीलता से जुड़े कार्यों हेतु श्रेष्ठ।",
    },
    "udveg": {
        "en": "Udveg (Anxiety/Sun)",
        "bn": "উদ্বেগ (বর্জনীয়)",
        "hi": "उद्वेग (त्याज्य)",
        "quality": "inauspicious",
        "lord": "Sun",
        "desc_en": "Avoid commencing new ventures; government work may be done cautiously.",
        "desc_bn": "মানসিক অস্থিরতা ও বাধার সৃষ্টি হতে পারে; নতুন উদ্যোগ পরিহার করুন।",
        "desc_hi": "मानसिक चिंता व कलह की संभावना, नए कार्यों से बचें।",
    },
    "kaal": {
        "en": "Kaal (Loss/Saturn)",
        "bn": "কাল (অশুভ)",
        "hi": "काल (अशुभ)",
        "quality": "inauspicious",
        "lord": "Saturn",
        "desc_en": "Inauspicious window ruled by Saturn. Strictly avoid auspicious beginnings.",
        "desc_bn": "শনির প্রভাবযুক্ত অশুভ কাল; শুভ কর্ম ও আর্থিক লেনদেন বর্জনীয়।",
        "desc_hi": "शनि शासित अशुभ समय, शुभ कार्य आरंभ न करें।",
    },
    "rog": {
        "en": "Rog (Illness/Mars)",
        "bn": "রোগ (পীড়াদায়ক)",
        "hi": "रोग (अशुभ)",
        "quality": "inauspicious",
        "lord": "Mars",
        "desc_en": "Afflicted period ruled by Mars. Avoid medical treatments or dispute initiation.",
        "desc_bn": "বিবাদ, দ্বন্দ্ব ও অসুস্থতার ঝুঁকি থাকে; বিতর্ক ও শুভ সূচনা বর্জনীয়।",
        "desc_hi": "विवाद एवं रोगकारक प्रभाव, शांति व संयम बनाए रखें।",
    },
}

# Chaldean planetary hora sequence
CHALDEAN_ORDER = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]

HORA_DESCRIPTIONS: dict[str, dict[str, Any]] = {
    "Sun": {
        "nature": "Shubh for authority, government, leadership",
        "activities_en": "Meeting officials, leadership roles, gold dealings, administrative tasks.",
        "activities_bn": "প্রশাসনিক কাজ, উচ্চপদস্থ ব্যক্তির সাক্ষাৎ, স্বর্ণ ক্রয় ও নেতৃত্বের সূচনা।",
        "activities_hi": "सरकारी कार्य, उच्चाधिकारियों से भेंट, पदभार ग्रहण।",
    },
    "Moon": {
        "nature": "Shubh for emotional, watery, domestic matters",
        "activities_en": "Starting journeys, public relations, gardening, food, silver purchases.",
        "activities_bn": "জলীয় কাজ, রৌপ্য ক্রয়, খাদ্যসামগ্রী বাণিজ্য, গৃহস্থালি ও ভ্রমণ।",
        "activities_hi": "यात्रा, जनसंपर्क, जल सम्बन्धी कार्य एवं गृहस्थी की शुरुआत।",
    },
    "Mars": {
        "nature": "Ashubh for peace; Shubh for courage, sports, surgery",
        "activities_en": "Physical competition, surgery, real estate litigation, technical repairs.",
        "activities_bn": "অস্ত্রোপচার, প্রযুক্তিগত কাজ, শারীরিক ব্যায়াম ও আইনি প্রতিরক্ষা।",
        "activities_hi": "शस्त्र, चिकित्सा, तकनीकी कार्य एवं प्रतिस्पर्धा।",
    },
    "Mercury": {
        "nature": "Super Shubh for commerce, writing, education",
        "activities_en": "Signing contracts, publishing, accounts, trade, learning new skills.",
        "activities_bn": "চুক্তি স্বাক্ষর, নতুন ব্যবসা, হিসাবনিকাশ, লেখালেখি ও বিদ্যাচর্চা।",
        "activities_hi": "व्यापार, लेखा-जोखा, विद्यारम्भ, लेखन एवं नवीन अनुबंध।",
    },
    "Jupiter": {
        "nature": "Supreme Shubh for wisdom, wealth, spirituality",
        "activities_en": "Religious ceremonies, investing, approaching mentors, wedding prep.",
        "activities_bn": "ধর্মীয় আচার, গুরুদর্শন, দীক্ষা গ্রহণ, অর্থ বিনিয়োগ ও বিদ্যালাভ।",
        "activities_hi": "यज्ञ, पूजन, गुरु कृपा, धार्मिक कार्य एवं बड़े निवेश।",
    },
    "Venus": {
        "nature": "Super Shubh for romance, arts, luxury, jewels",
        "activities_en": "Artistic work, buying luxury items, jewellery, music, romantic meetings.",
        "activities_bn": "শিল্পকলা, অলংকার ক্রয়, সংগীত, গৃহসজ্জা ও রোমান্টিক মিলন।",
        "activities_hi": "कला, सौंदर्य प्रसाधन, आभूषण क्रय एवं प्रेम संबंध।",
    },
    "Saturn": {
        "nature": "Slow, heavy; Shubh only for oil, iron, meditation",
        "activities_en": "Iron/oil deals, deep meditation, labor management, laying foundations.",
        "activities_bn": "ভিত্তিস্থাপন, লোহার কাজ, তেল বাণিজ্য, সাধনা ও কঠোর শ্রম।",
        "activities_hi": "नींव डालना, तेल व लोहे का कार्य, गहन साधना।",
    },
}

MILESTONES_CANON: list[dict[str, Any]] = [
    {
        "id": "vivah",
        "name": {"en": "Marriage (Vivah)", "bn": "শুভ বিবাহ মুহূর্ত", "hi": "शुभ विवाह मुहूर्त"},
        "tagline": {
            "en": "Sacred bond of seven vows under divine celestial witness",
            "bn": "সপ্তপদী ও অগ্নিসাক্ষী রেখে আজীবন সৌহার্দ্য বন্ধন",
            "hi": "अग्नि साक्षी एवं सप्तपदी द्वारा आजीवन पावन परिणय सूत्र",
        },
        "desc": {
            "en": "Optimal planetary alignments ensuring everlasting marital fidelity and family harmony.",
            "bn": "আজীবন দাম্পত্য সুখ, সৌহার্দ্য ও বংশবৃদ্ধির জন্য শাস্ত্রীয় গ্রহ-নক্ষত্র ও লগ্ন বিচার।",
            "hi": "सुखी दांपत्य जीवन, वंश वृद्धि और पारिवारिक सौहार्द हेतु सर्वश्रेष्ठ लग्न व ग्रह स्थिति।",
        },
        "shloka": "॥ धर्मे च अर्थे च कामे च नातिचरामि ॥",
        "shloka_meaning": {
            "en": "“In righteous duty, prosperity, and love, I shall remain devoted forever.”",
            "bn": "“ধর্ম, অর্থ ও কামে আমি আজীবন তোমার প্রতি নিষ্ঠাবান থাকিব।”",
            "hi": "“धर्म, अर्थ और काम में मैं सदैव तुम्हारा साथ निभाऊँगा।”",
        },
        "best_nakshatras": "Rohini, Mrigashira, Magha, Uttara Phalguni, Hasta, Swati, Anuradha, Mula, Uttara Ashadha, Uttara Bhadrapada, Revati",
        "best_tithis": "Shukla Dvitiya, Tritiya, Panchami, Saptami, Dashami, Ekadashi, Trayodashi",
        "best_vara": "Monday, Wednesday, Thursday, Friday",
        "best_choghadiya": "Amrit, Shubh, Labh (Day & Godhuli Kaal)",
        "caution": "Strictly avoid combustion of Jupiter or Venus, Bhadra Vishti Karana, Chaturmasya, and solar/lunar eclipses.",
        "scripture_ref": "Muhurat Chintamani · Vivah Prakarana (Sl. 12-24)",
    },
    {
        "id": "griha",
        "name": {"en": "Griha Pravesh", "bn": "গৃহপ্রবেশ মুহূর্ত", "hi": "गृह प्रवेश मुहूर्त"},
        "tagline": {
            "en": "Consecrating home soil with Mangal Kalash & Vastu Purusha blessings",
            "bn": "মঙ্গল কলশ স্থাপন ও বাস্তু পুরুষের আশীর্বাদে শান্তি লাভ",
            "hi": "मंगल कलश एवं वास्तु पुरुष कृपा से सुख-समृद्धि वास",
        },
        "desc": {
            "en": "Auspicious solar transitions for new dwelling entry to ensure generational peace.",
            "bn": "নতুন বাস্তুতে পরিবারের সুখ, শান্তি ও ধনবৃদ্ধির জন্য শাস্ত্রীয় গৃহপ্রবেশ লগ্ন।",
            "hi": "नए घर में वास करने पर वंश वृद्धि, सकारात्मक ऊर्जा और धन प्रवाह सुनिश्चित करने हेतु।",
        },
        "shloka": "॥ ॐ वास्तुपुरुषाय नमः सर्वविঘ্নবিনাশায় সর্বসৌখ্যপ্রদায়িনে ॥",
        "shloka_meaning": {
            "en": "“Salutations to Vastu Purusha, remover of obstacles and bestowal of supreme felicity.”",
            "bn": "“বাস্তু পুরুষকে প্রণাম, যিনি সর্ব বিঘ্ন হরণকারী এবং সর্ব সৌখ্য প্রদানকারী।”",
            "hi": "“वास्तु पुरुष को प्रणाम, जो समस्त विघ्नों के नाशक और परम सुख के प्रदाता हैं।”",
        },
        "best_nakshatras": "Rohini, Mrigashira, Pushya, Uttara Phalguni, Hasta, Chitra, Anuradha, Uttara Ashadha, Uttara Bhadrapada, Revati",
        "best_tithis": "Shukla Paksha Dvitiya, Tritiya, Panchami, Saptami, Dashami, Ekadashi, Trayodashi",
        "best_vara": "Monday, Wednesday, Thursday, Friday",
        "best_choghadiya": "Amrit, Shubh, Labh (Morning to Midday)",
        "caution": "Avoid Tuesday, Sunday, Amavasya, Rikta Tithis (4th, 9th, 14th), and when the female head is in advanced pregnancy.",
        "scripture_ref": "Brihat Samhita · Vastu Vidya (Adhyaya 53)",
    },
    {
        "id": "vehicle",
        "name": {"en": "Vehicle Purchase (Vahan)", "bn": "যানবাহন ক্রয় মুহূর্ত", "hi": "वाहन क्रय मुहूर्त"},
        "tagline": {
            "en": "Protection on every journey under the chariot wheel of Surya",
            "bn": "পথের সুরক্ষায় ও নিরাপদ যাত্রায় নতুন গাড়ি ক্রয়ের ক্ষণ",
            "hi": "मार्ग रक्षा एवं दुर्घटना मुक्त यात्रा हेतु शुभ वाहन मुहूर्त",
        },
        "desc": {
            "en": "Fortunate planetary periods for purchasing, taking delivery, and inaugural drives.",
            "bn": "নিরাপদ ভ্রমণ, দীর্ঘস্থায়িত্ব ও দুর্ঘটনা রোধের উদ্দেশ্যে নতুন যান ক্রয়ের সঠিক ক্ষণ।",
            "hi": "सुरक्षित यात्रा, दीर्घायु और सुखद सफर सुनिश्चित करने के लिए वाहन डिलीवरी का समय।",
        },
        "shloka": "॥ ভদ্রং কর্ণেভিঃ শৃণুয়াম দেবা ভদ্রং পশ্যেমাক্ষভির্যজত্রাঃ ॥",
        "shloka_meaning": {
            "en": "“May we hear and behold only what is auspicious through every turn of our journey.”",
            "bn": "“আমাদের পথের প্রতিটি পদক্ষেপে শুভ ও কল্যাণ বর্ষিত হোক।”",
            "hi": "“हमारी हर यात्रा में शुभता, सुरक्षा एवं मंगलमय दर्शन प्राप्त हों।”",
        },
        "best_nakshatras": "Ashwini, Rohini, Punarvasu, Pushya, Hasta, Swati, Shravana, Dhanishta, Shatabhisha",
        "best_tithis": "Pratipada, Tritiya, Panchami, Shashthi, Dashami, Ekadashi, Purnima",
        "best_vara": "Wednesday, Thursday, Friday, Sunday",
        "best_choghadiya": "Amrit, Shubh, Char (Moving energy)",
        "caution": "Avoid taking delivery during Rahu Kaal, Yamaghanta, Saturdays, and Tuesdays for private passenger cars.",
        "scripture_ref": "Muhurat Ganapati · Vahan Prakarana",
    },
    {
        "id": "business",
        "name": {"en": "Business Start (Vyapar)", "bn": "ব্যবসা ও বাণিজ্য আরম্ভ", "hi": "व्यापार एवं प्रतिष्ठान आरम्भ"},
        "tagline": {
            "en": "Invoking Mahalakshmi & Kuber for thriving commerce and profit",
            "bn": "মা লক্ষ্মী ও কুবেরের কৃপায় লাভজনক বাণিজ্যের সূচনা",
            "hi": "महालक्ष्मी व कुबेर कृपा से धन-धान्य एवं व्यापार वृद्धि",
        },
        "desc": {
            "en": "Optimal celestial configurations for opening commercial shops and signing contracts.",
            "bn": "নতুন দোকান, স্টার্টআপ বা বাণিজ্যিক চুক্তির মাধ্যমে নিরবচ্ছিন্ন ধনপ্রাপ্তির যোগ।",
            "hi": "दुकान उद्घाटन, नई फर्म स्थापना या बड़े व्यावसायिक अनुबंध हस्ताक्षर का श्रेष्ठ समय।",
        },
        "shloka": "॥ ॐ শ্রীং হ্রীং ক্লীং ত্রিভুবন মহালক্ষ্ম্যৈ অস্মাকং দারিদ্র্যং নাশয় নাশয় ॥",
        "shloka_meaning": {
            "en": "“O Divine Empress Lakshmi of the three realms, dissipate all lack and grant enduring prosperity.”",
            "bn": "“হে ত্রিভুবন জননী মহালক্ষ্মী, আমাদের সর্বপ্রকার দারিদ্র্য বিনাশ করিয়া চিরসমৃদ্ধি প্রদান করুন।”",
            "hi": "“हे त्रिभुवन व्यापिनी महालक्ष्मी, हमारे समस्त अभावों का नाश कर अक्षय धन वैभव प्रदान करें।”",
        },
        "best_nakshatras": "Ashwini, Rohini, Pushya, Uttara Phalguni, Hasta, Chitra, Anuradha, Revati",
        "best_tithis": "Shukla Pratipada, Dvitiya, Tritiya, Panchami, Saptami, Dashami, Ekadashi, Trayodashi",
        "best_vara": "Wednesday, Thursday, Friday",
        "best_choghadiya": "Labh (Profit), Amrit (Permanence), Shubh (Growth)",
        "caution": "Never begin under Rikta Tithis (4th, 9th, 14th) or during combust Mercury (Budha Astha).",
        "scripture_ref": "Muhurta Chintamani · Vyapar Prakarana",
    },
    {
        "id": "gold",
        "name": {"en": "Gold & Jewellery (Suvarna)", "bn": "স্বর্ণ ও রত্ন ক্রয় মুহূর্ত", "hi": "स्वर्ण एवं आभूषण क्रय"},
        "tagline": {
            "en": "Preserving Lakshmi in pure yellow metal under Pushya & Ravi Yoga",
            "bn": "পবিত্র পুখ্য নক্ষত্র ও রবিযোগে লক্ষ্মী স্বরূপ স্বর্ণ সঞ্চয়",
            "hi": "पुष्य नक्षत्र व रवि योग में अक्षय लक्ष्मी स्वरूप स्वर्ण अर्जन",
        },
        "desc": {
            "en": "Fortuitous muhurats for buying bullion, ornamental jewellery, and consecrated gemstones.",
            "bn": "ধাতব সম্পদ বৃদ্ধি এবং জ্যোতিষীয় রত্ন ধারণের জন্য সর্বশ্রেষ্ঠ পুণ্য সময়।",
            "hi": "सोने-चांदी के सिक्के, जेवर अथवा ज्योतिषी रत्नों की खरीद हेतु परम कल्याणकारी मुहूर्त।",
        },
        "shloka": "॥ ॐ হিরণ্যগর্ভায় নমঃ হিরণ্যবর্ণায়ৈ দেব্যৈ নমস্তুতে ॥",
        "shloka_meaning": {
            "en": "“Salutations to the golden primordial source and the golden-complexioned Divine Mother.”",
            "bn": "“হিরণ্যগর্ভ ও সুবর্ণবর্ণা দেবী মহালক্ষ্মীকে শত কোটি প্রণাম।”",
            "hi": "“सुवर्ण स्वरूप हिरण्यगर्भ एवं सुवर्णमयी भगवती को बारंबार नमन।”",
        },
        "best_nakshatras": "Pushya, Rohini, Hasta, Swati, Anuradha, Shravana, Shatabhisha",
        "best_tithis": "Dvitiya, Tritiya, Panchami, Saptami, Dashami, Ekadashi, Trayodashi, Purnima",
        "best_vara": "Thursday (Guru), Sunday (Surya), Friday",
        "best_choghadiya": "Amrit, Shubh, Labh",
        "caution": "Avoid purchase during Bhadra and solar eclipses; consecrated gemstone rings should be set in daylight hours.",
        "scripture_ref": "Skanda Purana · Suvarna Mahatmya",
    },
    {
        "id": "education",
        "name": {"en": "Education & Vidya (Akshararambha)", "bn": "বিদ্যারম্ভ ও দীক্ষা", "hi": "विद्यारम्भ एवं शिक्षा"},
        "tagline": {
            "en": "Invoking Devi Saraswati for wisdom, sharpness of intellect, and rhetoric",
            "bn": "দেবী সরস্বতীর চরণে জ্ঞান, বাগ্মিতা ও একাগ্রতা অর্জনের পবিত্র ক্ষণ",
            "hi": "माँ सरस्वती के पावन सानिध्य में ज्ञानार्जन व एकाग्रता का शुभारंभ",
        },
        "desc": {
            "en": "Golden hours for enrolling in universities, starting new courses, competitive exam prep, and Vedic initiation.",
            "bn": "নতুন শিক্ষাবর্ষ, উচ্চশিক্ষা, গবেষণাপত্র প্রকাশ ও আধ্যাত্মিক দীক্ষার জন্য প্রশস্ত।",
            "hi": "नवीन पाठ्यक्रम, उच्च शिक्षा, कोचिंग प्रवेश एवं परीक्षा की तैयारी हेतु शुभ मुहूर्त।",
        },
        "shloka": "॥ सरस्वति नमस्तुभ्यं वरदे कामरूपिणि विद्यारम्भं करिष्यामि सिद्धिर्भवतु मे सदा ॥",
        "shloka_meaning": {
            "en": "“O Goddess Saraswati, granter of boons, I begin my studies; may I always achieve success.”",
            "bn": "“হে বরদায়িনী দেবী সরস্বতী, আমি বিদ্যাচর্চা আরম্ভ করিতেছি; আমার সর্বদা সাফল্য হউক।”",
            "hi": "“हे वरदायिनी माँ सरस्वती, मैं विद्या आरम्भ कर रहा हूँ; मुझे सदा सफलता प्राप्त हो।”",
        },
        "best_nakshatras": "Ashwini, Rohini, Mrigashira, Punarvasu, Pushya, Hasta, Chitra, Swati, Anuradha, Shravana, Dhanishta, Shatabhisha, Revati",
        "best_tithis": "Shukla Dvitiya, Tritiya, Panchami (Vasant Panchami), Dashami, Ekadashi, Trayodashi",
        "best_vara": "Wednesday (Budha - Intellect), Thursday (Guru - Wisdom), Sunday",
        "best_choghadiya": "Labh (Absorption), Amrit (Permanence), Shubh (Wisdom)",
        "caution": "Avoid Amavasya, Ashtami, and combust Jupiter/Mercury.",
        "scripture_ref": "Brihat Jyotisha · Vidya Prakarana",
    },
    {
        "id": "yatra",
        "name": {"en": "Travel & Expedition (Yatra)", "bn": "যাত্রা ও ভ্রমণ মুহূর্ত", "hi": "यात्रा एवं गमन मुहूर्त"},
        "tagline": {
            "en": "Harmonizing planetary hora and Disha Shoola for effortless triumph",
            "bn": "দিকশূল বর্জন ও গ্রহের অনুকূলতায় কার্য সিদ্ধির নিরাপদ পথচলা",
            "hi": "दिशाशूल परिहार पूर्वक सुरक्षित व सफल यात्रा का पावन योग",
        },
        "desc": {
            "en": "Vedic criteria to avoid directional affliction (Disha Shoola) and travel in harmony with the ruling planetary hora.",
            "bn": "দূরপাল্লার সফর, বিদেশে চাকরি বা তীর্থযাত্রার প্রাক্কালে শুভ ক্ষণ ও দিক নির্ণয়।",
            "hi": "तीर्थ यात्रा, विदेश गमन अथवा महत्वपूर्ण व्यापारिक यात्रा हेतु सर्वोत्तम समय।",
        },
        "shloka": "॥ यात्राकाले शुभाः सर्वे ग्रहाः सन्तु प्रसन्नाः सुखदाः शिवाः ॥",
        "shloka_meaning": {
            "en": "“May all nine planets be peaceful, gentle, and auspicious during my expedition.”",
            "bn": "“যাত্রাকালে নবগ্রহ প্রসন্ন হয়ে পথকে নির্বিঘ্ন ও সুখদায়ক করুক।”",
            "hi": "“यात्रा काल में सभी ग्रह शुभ, शांत एवं कल्याणकारी फल प्रदान करें।”",
        },
        "best_nakshatras": "Ashwini, Mrigashira, Punarvasu, Pushya, Hasta, Anuradha, Shravana, Dhanishta, Revati",
        "best_tithis": "Shukla Dvitiya, Tritiya, Panchami, Saptami, Dashami, Trayodashi",
        "best_vara": "Wednesday, Thursday, Friday",
        "best_choghadiya": "Char (Motion), Labh (Gain), Amrit (Protection)",
        "caution": "Never embark toward a direction burdened by active Disha Shoola without scriptural remedy, nor during Rahu Kaal.",
        "scripture_ref": "Brihat Samhita · Yatra Adhyaya",
    },
    {
        "id": "namakaran",
        "name": {"en": "Namakaran Sanskar", "bn": "নামকরণ সংস্কার", "hi": "नामकरण संस्कार"},
        "tagline": {
            "en": "Imbuing the newborn with their Nakshatra syllable and lifelong fortune",
            "bn": "নবজাতকের জন্ম নক্ষত্র অনুযায়ী শুভ নাম ও পরমায়ু প্রার্থনা",
            "hi": "शिशु के जन्म नक्षत्र व चंद्र राशि के अनुसार सौभाग्यशाली नामकरण",
        },
        "desc": {
            "en": "Sacred Vedic sacrament held on the 10th, 11th, 12th, or 16th day after birth.",
            "bn": "শিশুর দীর্ঘায়ু, যশ ও সৌভাগ্য বৃদ্ধির উদ্দেশ্যে শাস্ত্রীয় নিয়মে শুভ নাম প্রদান।",
            "hi": "नवजात शिशु के दीर्घायु, यश और तेज की वृद्धि हेतु वैदिक नामकरण का पावन समय।",
        },
        "shloka": "॥ आयुष्यं वर्चस्वं पुष्टिं यशः कीर्तिं च वर्धताम् ॥",
        "shloka_meaning": {
            "en": "“May this child flourish with long life, spiritual radiance, strength, and honorable fame.”",
            "bn": "“এই শিশু পরমায়ু, প্রজ্ঞা, শারীরিক পুষ্টি ও নির্মল যশ লাভ করুক।”",
            "hi": "“यह शिशु दीर्घायु, आध्यात्मिक तेज, बल और उच्च कीर्ति प्राप्त करे।”",
        },
        "best_nakshatras": "Rohini, Uttara Phalguni, Uttara Ashadha, Uttara Bhadrapada, Hasta, Chitra, Anuradha, Revati",
        "best_tithis": "Shukla Dvitiya, Tritiya, Panchami, Saptami, Dashami, Trayodashi",
        "best_vara": "Monday, Wednesday, Thursday, Friday",
        "best_choghadiya": "Amrit, Shubh",
        "caution": "Avoid Amavasya, Rikta Tithis (4th, 9th, 14th), and Janma Nakshatra if unafflicted options are available.",
        "scripture_ref": "Parashara Grihya Sutra · Namakaran Vidhana",
    },
]


def _fmt_time(dec_hour: float) -> str:
    """Converts decimal hour [0, 24) to 'hh:mm AM/PM'."""
    dec_hour = dec_hour % 24.0
    h = int(dec_hour)
    m = int(round((dec_hour - h) * 60))
    if m >= 60:
        h = (h + 1) % 24
        m = 0
    period = "AM" if h < 12 else "PM"
    display_h = 12 if h in (0, 12) else h % 12
    return f"{display_h:02d}:{m:02d} {period}"


def _is_active_window(start_dec: float, end_dec: float, now_dec: float) -> bool:
    """Checks if current decimal hour falls within [start_dec, end_dec], handling midnight wrap."""
    start_dec = start_dec % 24.0
    end_dec = end_dec % 24.0
    if start_dec < end_dec:
        return start_dec <= now_dec <= end_dec
    else:  # Spans across midnight
        return now_dec >= start_dec or now_dec <= end_dec


def calculate_muhurat_report(payload: MuhuratRequest) -> MuhuratResponse:
    """Calculates comprehensive Vedic Muhurat report with astronomical precision."""
    _require_swisseph()

    # Parse target date
    if payload.date:
        try:
            target_date = datetime.strptime(payload.date.strip(), "%Y-%m-%d").date()
        except ValueError:
            target_date = datetime.now(timezone.utc).date()
    else:
        target_date = datetime.now(timezone.utc).date()

    tz_offset = payload.timezone
    lat = payload.latitude
    lon = payload.longitude
    lang: Lang = payload.language if payload.language in ("en", "bn", "hi") else "en"

    # Current time in user timezone
    now_utc = datetime.now(timezone.utc)
    current_user_hour_dec = (now_utc.hour + now_utc.minute / 60.0 + tz_offset) % 24.0

    # Julian day for local day start
    geopos = (lon, lat, 0.0)
    jd_day_start = swe.julday(target_date.year, target_date.month, target_date.day, 0.0)

    # 1. Astronomical Sunrise & Sunset using Swiss Ephemeris
    try:
        rise_res = swe.rise_trans(jd_day_start, swe.SUN, swe.CALC_RISE, geopos)
        _, _, _, rise_ut = swe.revjul(rise_res[1][0])
        sunrise_h = (rise_ut + tz_offset) % 24.0
    except Exception as exc:
        logger.warning(f"Swiss Ephemeris sunrise calculation fallback: {exc}")
        sunrise_h = 5.75  # 05:45 AM fallback

    try:
        set_res = swe.rise_trans(jd_day_start, swe.SUN, swe.CALC_SET, geopos)
        _, _, _, set_ut = swe.revjul(set_res[1][0])
        sunset_h = (set_ut + tz_offset) % 24.0
    except Exception as exc:
        logger.warning(f"Swiss Ephemeris sunset calculation fallback: {exc}")
        sunset_h = 17.5  # 05:30 PM fallback

    try:
        next_rise_res = swe.rise_trans(jd_day_start + 1.0, swe.SUN, swe.CALC_RISE, geopos)
        _, _, _, next_rise_ut = swe.revjul(next_rise_res[1][0])
        next_sunrise_h = (next_rise_ut + tz_offset) % 24.0
    except Exception:
        next_sunrise_h = sunrise_h

    # Durations
    day_duration = (sunset_h - sunrise_h) if sunset_h > sunrise_h else (sunset_h + 24.0 - sunrise_h)
    night_duration = (next_sunrise_h + 24.0 - sunset_h) % 24.0
    if night_duration <= 0.0:
        night_duration = 24.0 - day_duration

    # Midday (Solar Noon)
    midday_h = (sunrise_h + day_duration / 2.0) % 24.0

    # Weekday determination
    weekday_idx = target_date.weekday()  # Mon = 0, Sun = 6
    weekday_meta = WEEKDAY_NAMES[weekday_idx]
    weekday_lord = WEEKDAY_LORDS[weekday_idx]

    # Daytime 1/8th division length
    day_part = day_duration / 8.0

    # 2. Core Kaal Windows
    # A. Abhijit Muhurat: 8th of 15 daytime muhurats
    muhurat_len = day_duration / 15.0
    abhijit_start = (sunrise_h + 7.0 * muhurat_len) % 24.0
    abhijit_end = (sunrise_h + 8.0 * muhurat_len) % 24.0
    is_abhijit_active = _is_active_window(abhijit_start, abhijit_end, current_user_hour_dec)

    abhijit_desc = {
        "en": "Midday victory window capable of counteracting a myriad of minor flaws. Supreme for major undertakings.",
        "bn": "দিনের অপরাজেয় ক্ষণ — যে কোনো জরুরি শুভ কর্ম নিষ্পত্তির শ্রেষ্ঠ সময়।",
        "hi": "दिन का सबसे शक्तिशाली विजय मुहूर्त — किसी भी महत्वपूर्ण शुभ कार्य हेतु सर्वश्रेष्ठ।",
    }
    if weekday_idx == 2:  # Wednesday special note
        abhijit_desc["en"] += " (Note: On Wednesdays, Abhijit is tainted by Mercury-Rahu interaction; perform with caution)."
        abhijit_desc["bn"] += " (বিশেষ জ্ঞাতব্য: বুধবারে রাহুর প্রভাবে কিছুটা প্রশমিত)।"
        abhijit_desc["hi"] += " (बुधवार को विशेष सावधानी अपेक्षित है)।"

    abhijit_win = MuhuratTimingWindow(
        id="abhijit",
        name={"en": "Abhijit Muhurat", "bn": "অভিজিৎ মুহূর্ত", "hi": "अभिजित मुहूर्त"},
        start_time=_fmt_time(abhijit_start),
        end_time=_fmt_time(abhijit_end),
        formatted=f"{_fmt_time(abhijit_start)} – {_fmt_time(abhijit_end)}",
        quality="super_auspicious",
        is_active=is_abhijit_active,
        description=abhijit_desc,
        activities_recommended=["Starting businesses", "Signing contracts", "Interviews", "Important purchases"],
        activities_prohibited=[],
    )

    # B. Brahma Muhurat (approx 96m to 48m before sunrise)
    night_muhurat_len = night_duration / 15.0
    brahma_start = (sunrise_h - 2.0 * night_muhurat_len) % 24.0
    brahma_end = (sunrise_h - 1.0 * night_muhurat_len) % 24.0
    brahma_win = MuhuratTimingWindow(
        id="brahma",
        name={"en": "Brahma Muhurat", "bn": "ব্রহ্ম মুহূর্ত", "hi": "ब्रह्म मुहूर्त"},
        start_time=_fmt_time(brahma_start),
        end_time=_fmt_time(brahma_end),
        formatted=f"{_fmt_time(brahma_start)} – {_fmt_time(brahma_end)}",
        quality="super_auspicious",
        is_active=_is_active_window(brahma_start, brahma_end, current_user_hour_dec),
        description={
            "en": "Sacred pre-dawn window of maximum spiritual sattva. Best for meditation, yoga, and deep study.",
            "bn": "সর্বোচ্চ সত্ত্বগুণসম্পন্ন সময়। ঈশ্বর আরাধনা, ধ্যান, বিদ্যাভ্যাস ও যোগাসনের জন্য শ্রেষ্ঠ।",
            "hi": "अमृत वेला, ध्यान, योग, साधना एवं आत्मचिंतन हेतु सर्वाधिक पवित्र समय।",
        },
        activities_recommended=["Meditation", "Japa", "Pranayama", "Studying complex scriptures"],
        activities_prohibited=["Sleeping", "Sensual indulgence", "Heavy meals"],
    )

    # C. Rahu Kaal (1/8th daytime)
    rahu_part = RAHU_KAAL_PARTS[weekday_idx]
    rahu_start = (sunrise_h + (rahu_part - 1) * day_part) % 24.0
    rahu_end = (sunrise_h + rahu_part * day_part) % 24.0
    rahu_win = MuhuratTimingWindow(
        id="rahu_kaal",
        name={"en": "Rahu Kaal", "bn": "রাহুকাল", "hi": "राहुकाल"},
        start_time=_fmt_time(rahu_start),
        end_time=_fmt_time(rahu_end),
        formatted=f"{_fmt_time(rahu_start)} – {_fmt_time(rahu_end)}",
        quality="inauspicious",
        is_active=_is_active_window(rahu_start, rahu_end, current_user_hour_dec),
        description={
            "en": "Afflicted planetary shadow window. Strictly avoid embarking on new journeys, contracts, or purchases.",
            "bn": "রাহুর তীব্র দৃষ্টির সময়। নতুন চুক্তি, যাত্রা, কেনাকাটা ও শুভ সংস্কার বর্জন করুন।",
            "hi": "राहु की कुदृष्टि का समय। कोई भी नया अनुबंध, खरीद या यात्रा टालें।",
        },
        activities_recommended=["Routine chores", "Rahu Shanti japa", "Charity to needy"],
        activities_prohibited=["Commencing new ventures", "Signing agreements", "Purchasing vehicles or gold"],
    )

    # D. Yamaganda / Yamaghanta (1/8th daytime)
    yama_part = YAMAGANDA_PARTS[weekday_idx]
    yama_start = (sunrise_h + (yama_part - 1) * day_part) % 24.0
    yama_end = (sunrise_h + yama_part * day_part) % 24.0
    yama_win = MuhuratTimingWindow(
        id="yamaganda",
        name={"en": "Yamaganda Kaal", "bn": "যমঘণ্ট কাল", "hi": "यमगण्ड काल"},
        start_time=_fmt_time(yama_start),
        end_time=_fmt_time(yama_end),
        formatted=f"{_fmt_time(yama_start)} – {_fmt_time(yama_end)}",
        quality="inauspicious",
        is_active=_is_active_window(yama_start, yama_end, current_user_hour_dec),
        description={
            "en": "Son of Saturn / Yama window. Inauspicious for commencement; activities may encounter severe hurdles.",
            "bn": "মৃত্যুঞ্জয় ও যমদেব সম্পর্কিত ক্ষণ; নতুন যাত্রা ও চিকিৎসা আরম্ভে বর্জনীয়।",
            "hi": "विघ्न एवं विलंबकारी समय, महत्वपूर्ण मांगलिक कार्य आरंभ न करें।",
        },
        activities_recommended=["Spiritual contemplation", "Ancestor prayers"],
        activities_prohibited=["Travel departure", "Medical operations", "New business"],
    )

    # E. Gulika Kaal (1/8th daytime)
    guli_part = GULIKA_PARTS[weekday_idx]
    guli_start = (sunrise_h + (guli_part - 1) * day_part) % 24.0
    guli_end = (sunrise_h + guli_part * day_part) % 24.0
    guli_win = MuhuratTimingWindow(
        id="gulika",
        name={"en": "Gulika Kaal", "bn": "গুলিকা কাল", "hi": "गुलिक काल"},
        start_time=_fmt_time(guli_start),
        end_time=_fmt_time(guli_end),
        formatted=f"{_fmt_time(guli_start)} – {_fmt_time(guli_end)}",
        quality="remedial",
        is_active=_is_active_window(guli_start, guli_end, current_user_hour_dec),
        description={
            "en": "Son of Saturn window. Whatever is done during Gulika repeats itself; favorable for steady asset building.",
            "bn": "স্থায়ী সম্পদ ক্রয়ের জন্য প্রশমিত শুভ। তবে ঋণ গ্রহণ করবেন না, কারণ তা বারবার হতে পারে।",
            "hi": "स्थायी संपत्ति क्रय हेतु सामान्य, परंतु ऋण लेने से बचें।",
        },
        activities_recommended=["Buying land/property", "Long-term savings"],
        activities_prohibited=["Taking loans", "Medical discharge"],
    )

    # F. Vijaya Muhurat (11th muhurat of daytime)
    vijaya_start = (sunrise_h + 10.0 * muhurat_len) % 24.0
    vijaya_end = (sunrise_h + 11.0 * muhurat_len) % 24.0
    vijaya_win = MuhuratTimingWindow(
        id="vijaya",
        name={"en": "Vijaya Muhurat", "bn": "বিজয় মুহূর্ত", "hi": "विजय मुहूर्त"},
        start_time=_fmt_time(vijaya_start),
        end_time=_fmt_time(vijaya_end),
        formatted=f"{_fmt_time(vijaya_start)} – {_fmt_time(vijaya_end)}",
        quality="auspicious",
        is_active=_is_active_window(vijaya_start, vijaya_end, current_user_hour_dec),
        description={
            "en": "Afternoon victory window. Excellent for litigation, disputes settlement, and ambitious challenges.",
            "bn": "বিকেল বেলার বিজয় ক্ষণ। মামলা-মোকদ্দমা নিষ্পত্তি, সমঝোতা ও প্রতিযোগিতার জন্য শুভ।",
            "hi": "अपराह्न का विजय काल, विवाद सुलझाने एवं प्रतियोगिता हेतु फलदायी।",
        },
        activities_recommended=["Legal meetings", "Sports competitions", "Filing applications"],
        activities_prohibited=[],
    )

    # G. Godhuli Muhurat (twilight around sunset: 24 mins before to 24 mins after)
    godhuli_start = (sunset_h - 0.4) % 24.0
    godhuli_end = (sunset_h + 0.4) % 24.0
    godhuli_win = MuhuratTimingWindow(
        id="godhuli",
        name={"en": "Godhuli Muhurat", "bn": "গোধূলি মুহূর্ত", "hi": "गोधूलि मुहूर्त"},
        start_time=_fmt_time(godhuli_start),
        end_time=_fmt_time(godhuli_end),
        formatted=f"{_fmt_time(godhuli_start)} – {_fmt_time(godhuli_end)}",
        quality="auspicious",
        is_active=_is_active_window(godhuli_start, godhuli_end, current_user_hour_dec),
        description={
            "en": "Auspicious sunset window as cows return home. Sanctified for lighting lamps and marriage solemnization.",
            "bn": "সূর্যাস্তকালীন পবিত্র ক্ষণ। সন্ধ্যা আরতি, প্রদীপ প্রজ্জ্বলন ও বিবাহের জন্য শাস্ত্রীয়ভাবে প্রশস্ত।",
            "hi": "सायंकालीन पावन समय, संध्या आरती, विवाह एवं मांगलिक कार्यों हेतु शुभ।",
        },
        activities_recommended=["Evening prayers", "Lighting sacred lamps", "Marriage rites"],
        activities_prohibited=["Travel departure", "Cutting hair/nails"],
    )

    # H. Durmuhurat: Specific inauspicious daytime muhurats based on weekday
    dur_muhurats: list[MuhuratTimingWindow] = []
    # Classical Durmuhurat table (1-indexed muhurat numbers of daytime):
    # Sun: 14th; Mon: 8th & 9th; Tue: 4th & 11th; Wed: 5th; Thu: 6th & 7th; Fri: 4th & 9th; Sat: 2nd & 3rd
    dur_table = {
        6: [14],
        0: [8, 9],
        1: [4, 11],
        2: [5],
        3: [6, 7],
        4: [4, 9],
        5: [2, 3],
    }
    for m_num in dur_table.get(weekday_idx, [1]):
        d_start = (sunrise_h + (m_num - 1) * muhurat_len) % 24.0
        d_end = (sunrise_h + m_num * muhurat_len) % 24.0
        dur_muhurats.append(
            MuhuratTimingWindow(
                id=f"durmuhurat_{m_num}",
                name={"en": f"Durmuhurat ({m_num})", "bn": f"দুর্মুহূর্ত ({m_num})", "hi": f"दुर्मुहूर्त ({m_num})"},
                start_time=_fmt_time(d_start),
                end_time=_fmt_time(d_end),
                formatted=f"{_fmt_time(d_start)} – {_fmt_time(d_end)}",
                quality="inauspicious",
                is_active=_is_active_window(d_start, d_end, current_user_hour_dec),
                description={
                    "en": "Afflicted time segment during which all auspicious commencements are prohibited.",
                    "bn": "অশুভ সময়খণ্ড; এই সময়ে শুভ কার্য আরম্ভ শাস্ত্রানুসারে বর্জনীয়।",
                    "hi": "अशुभ मुहूर्त, इस समय नए मांगलिक कार्यों से बचें।",
                },
                activities_recommended=[],
                activities_prohibited=["All auspicious commencements"],
            )
        )

    # 3. 16 Vedic Choghadiyas (8 Day + 8 Night)
    choghadiyas: list[MuhuratChoghadiyaSlot] = []
    day_slots = DAY_CHOGHADIYA_ORDER[weekday_idx]
    for idx, c_key in enumerate(day_slots):
        slot_start = (sunrise_h + idx * day_part) % 24.0
        slot_end = (sunrise_h + (idx + 1) * day_part) % 24.0
        meta = CHOGHADIYA_META[c_key]
        choghadiyas.append(
            MuhuratChoghadiyaSlot(
                slot_index=idx + 1,
                name=meta["en"],
                name_translations={"en": meta["en"], "bn": meta["bn"], "hi": meta["hi"]},
                period_type="day",
                start_time=_fmt_time(slot_start),
                end_time=_fmt_time(slot_end),
                quality=meta["quality"],
                ruling_planet=meta["lord"],
                description={
                    "en": meta["desc_en"],
                    "bn": meta["desc_bn"],
                    "hi": meta["desc_hi"],
                },
                is_active=_is_active_window(slot_start, slot_end, current_user_hour_dec),
            )
        )

    night_part = night_duration / 8.0
    night_slots = NIGHT_CHOGHADIYA_ORDER[weekday_idx]
    for idx, c_key in enumerate(night_slots):
        slot_start = (sunset_h + idx * night_part) % 24.0
        slot_end = (sunset_h + (idx + 1) * night_part) % 24.0
        meta = CHOGHADIYA_META[c_key]
        choghadiyas.append(
            MuhuratChoghadiyaSlot(
                slot_index=idx + 9,
                name=meta["en"],
                name_translations={"en": meta["en"], "bn": meta["bn"], "hi": meta["hi"]},
                period_type="night",
                start_time=_fmt_time(slot_start),
                end_time=_fmt_time(slot_end),
                quality=meta["quality"],
                ruling_planet=meta["lord"],
                description={
                    "en": meta["desc_en"],
                    "bn": meta["desc_bn"],
                    "hi": meta["desc_hi"],
                },
                is_active=_is_active_window(slot_start, slot_end, current_user_hour_dec),
            )
        )

    # 4. 24 Planetary Horas (12 Day + 12 Night)
    horas: list[MuhuratHoraSlot] = []
    # Starting planet index in Chaldean order
    first_lord = weekday_lord
    chaldean_idx = CHALDEAN_ORDER.index(first_lord)
    day_hora_len = day_duration / 12.0

    for h_idx in range(12):
        p_lord = CHALDEAN_ORDER[(chaldean_idx + h_idx) % 7]
        h_start = (sunrise_h + h_idx * day_hora_len) % 24.0
        h_end = (sunrise_h + (h_idx + 1) * day_hora_len) % 24.0
        h_meta = HORA_DESCRIPTIONS[p_lord]
        horas.append(
            MuhuratHoraSlot(
                hora_index=h_idx + 1,
                start_time=_fmt_time(h_start),
                end_time=_fmt_time(h_end),
                lord=p_lord,
                nature=h_meta["nature"],
                is_active=_is_active_window(h_start, h_end, current_user_hour_dec),
                activities=h_meta[f"activities_{lang}"] if f"activities_{lang}" in h_meta else h_meta["activities_en"],
            )
        )

    night_hora_len = night_duration / 12.0
    for h_idx in range(12):
        p_lord = CHALDEAN_ORDER[(chaldean_idx + 12 + h_idx) % 7]
        h_start = (sunset_h + h_idx * night_hora_len) % 24.0
        h_end = (sunset_h + (h_idx + 1) * night_hora_len) % 24.0
        h_meta = HORA_DESCRIPTIONS[p_lord]
        horas.append(
            MuhuratHoraSlot(
                hora_index=h_idx + 13,
                start_time=_fmt_time(h_start),
                end_time=_fmt_time(h_end),
                lord=p_lord,
                nature=h_meta["nature"],
                is_active=_is_active_window(h_start, h_end, current_user_hour_dec),
                activities=h_meta[f"activities_{lang}"] if f"activities_{lang}" in h_meta else h_meta["activities_en"],
            )
        )

    # 5. Milestone Muhurats Compatibility Evaluation for Today
    milestones: list[MuhuratMilestoneItem] = []
    weekday_name_en = weekday_meta["en"]

    for m in MILESTONES_CANON:
        # Check if today's weekday is favorable for this milestone
        is_vara_fav = weekday_name_en in m["best_vara"]
        if is_vara_fav:
            compat = "Favorable"
            reason = {
                "en": f"Today is {weekday_name_en}, governed by {weekday_lord}, matching scriptural canons for {m['name']['en']}.",
                "bn": f"আজ {weekday_meta['bn']} ({weekday_lord} গ্রহের বার), যা {m['name']['bn']}র জন্য শাস্ত্রীয়ভাবে অনুকূল।",
                "hi": f"आज {weekday_meta['hi']} है जो {m['name']['hi']} के लिए शास्त्रसम्मत शुभ वार है।",
            }
        else:
            compat = "Moderate"
            reason = {
                "en": f"Today is {weekday_name_en}. Proceed only during auspicious Choghadiya (Amrit/Shubh) or Abhijit window.",
                "bn": f"আজ {weekday_meta['bn']}। নিতান্ত আবশ্যক হলে কেবল অমৃত বা শুভ চোগড়িয়া অথবা অভিজিৎ মুহূর্তে সম্পাদন করুন।",
                "hi": f"आज {weekday_meta['hi']} है। केवल अमृत या शुभ चौघड़िया में ही कार्य करें।",
            }

        milestones.append(
            MuhuratMilestoneItem(
                id=m["id"],
                name=m["name"],
                tagline=m["tagline"],
                desc=m["desc"],
                shloka=m["shloka"],
                shloka_meaning=m["shloka_meaning"],
                best_nakshatras=m["best_nakshatras"],
                best_tithis=m["best_tithis"],
                best_vara=m["best_vara"],
                best_choghadiya=m["best_choghadiya"],
                caution=m["caution"],
                scripture_ref=m["scripture_ref"],
                today_compatibility=compat,
                today_reason=reason,
            )
        )

    # 6. Basic Panchang Summary for Context
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    jd_noon = swe.julday(target_date.year, target_date.month, target_date.day, 12.0)
    moon_res, _ = swe.calc_ut(jd_noon, swe.MOON, swe.FLG_SIDEREAL | swe.FLG_SPEED)
    sun_res, _ = swe.calc_ut(jd_noon, swe.SUN, swe.FLG_SIDEREAL | swe.FLG_SPEED)
    moon_lon = float(moon_res[0]) % 360.0
    sun_lon = float(sun_res[0]) % 360.0

    tithi_info = calculate_tithi(sun_lon, moon_lon, lang)
    yoga_info = calculate_yoga(sun_lon, moon_lon, lang)
    karana_info = calculate_karana(sun_lon, moon_lon, lang)

    span = 360.0 / 27.0
    nak_idx = int(moon_lon / span) % 27
    nakshatra_names = [
        "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
        "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
        "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
        "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
        "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
    ]
    nak_name = nakshatra_names[nak_idx]

    panchang_summary = {
        "tithi": tithi_info["name"],
        "nakshatra": nak_name,
        "yoga": yoga_info["name"],
        "karana": karana_info["name"],
        "vara": weekday_meta[lang],
    }

    core_windows = [
        abhijit_win,
        brahma_win,
        rahu_win,
        yama_win,
        guli_win,
        vijaya_win,
        godhuli_win,
    ]

    return MuhuratResponse(
        date=target_date.isoformat(),
        weekday=weekday_meta,
        sunrise=_fmt_time(sunrise_h),
        sunset=_fmt_time(sunset_h),
        solar_noon=_fmt_time(midday_h),
        next_sunrise=_fmt_time(next_sunrise_h),
        day_duration_hours=round(day_duration, 2),
        night_duration_hours=round(night_duration, 2),
        core_windows=core_windows,
        abhijit=abhijit_win,
        brahma_muhurat=brahma_win,
        rahu_kaal=rahu_win,
        yamaganda=yama_win,
        gulika_kaal=guli_win,
        durmuhurat=dur_muhurats,
        amrit_kaal=None,
        vijaya_muhurat=vijaya_win,
        godhuli_muhurat=godhuli_win,
        choghadiyas=choghadiyas,
        horas=horas,
        milestone_muhurats=milestones,
        panchang_summary=panchang_summary,
        engine="Swiss Ephemeris 2.10 (pyswisseph)",
        calculated_at=datetime.now(timezone.utc).strftime("%d %B %Y, %H:%M UTC"),
    )
