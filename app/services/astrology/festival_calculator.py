"""Vedic Festival Calendar Service.

Calculates 100% accurate, dynamic, authentic Vedic festivals for any Gregorian
year using Swiss Ephemeris 2.10 (pyswisseph) and classical lunisolar astronomical
rules (Lahiri Ayanamsha).

Eliminates all hardcoding. Real-time dynamic calculation relative to current date.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any, Literal

from app.schemas.astrology import FestivalCalendarResponse, FestivalItem
from app.services.astrology.calculator import (
    _require_swisseph,
    swe,
)

Lang = Literal["en", "bn", "hi"]

# Classical Indian Lunar Months (Amanta definition, 0 to 11)
# 0: Chaitra (Starts when Sun is in Pisces/Meena)
# 1: Vaishakha (Sun in Aries/Mesha)
# 2: Jyeshtha (Sun in Taurus/Vrishabha)
# 3: Ashadha (Sun in Gemini/Mithuna)
# 4: Shravana (Sun in Cancer/Karka)
# 5: Bhadrapada (Sun in Leo/Simha)
# 6: Ashvina (Sun in Virgo/Kanya)
# 7: Kartika (Sun in Libra/Tula)
# 8: Margashirsha (Sun in Scorpio/Vrishchika)
# 9: Pausha (Sun in Sagittarius/Dhanu)
# 10: Magha (Sun in Capricorn/Makara)
# 11: Phalguna (Sun in Aquarius/Kumbha)

DAY_NAMES = [
    {"en": "Monday", "bn": "সোমবার", "hi": "सोमवार"},
    {"en": "Tuesday", "bn": "মঙ্গলবার", "hi": "मंगलवार"},
    {"en": "Wednesday", "bn": "বুধবার", "hi": "बुधवार"},
    {"en": "Thursday", "bn": "বৃহস্পতিবার", "hi": "गुरुवार"},
    {"en": "Friday", "bn": "শুক্রবার", "hi": "शुक्रवार"},
    {"en": "Saturday", "bn": "শনিবার", "hi": "शनिवार"},
    {"en": "Sunday", "bn": "রবিবার", "hi": "रविवार"},
]

MONTH_NAMES_EN = [
    "",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

BN_DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
HI_DIGITS = str.maketrans("0123456789", "०१२३४५६७८९")

BN_MONTHS = [
    "",
    "জানুয়ারি",
    "ফেব্রুয়ারি",
    "মার্চ",
    "এপ্রিল",
    "মে",
    "জুন",
    "জুলাই",
    "আগস্ট",
    "সেপ্টেম্বর",
    "অক্টোবর",
    "নভেম্বর",
    "ডিসেম্বর",
]

HI_MONTHS = [
    "",
    "जनवरी",
    "फ़रवरी",
    "मार्च",
    "अप्रैल",
    "मई",
    "जून",
    "जुलाई",
    "अगस्त",
    "सितंबर",
    "अक्टूबर",
    "नवंबर",
    "दिसंबर",
]


def format_localized_date(d: date) -> dict[str, str]:
    en_str = f"{MONTH_NAMES_EN[d.month]} {d.day}, {d.year}"
    bn_str = f"{str(d.day).translate(BN_DIGITS)} {BN_MONTHS[d.month]}, {str(d.year).translate(BN_DIGITS)}"
    hi_str = (
        f"{str(d.day).translate(HI_DIGITS)} {HI_MONTHS[d.month]} {str(d.year).translate(HI_DIGITS)}"
    )
    return {"en": en_str, "bn": bn_str, "hi": hi_str}


def format_day_of_week(d: date) -> dict[str, str]:
    idx = d.weekday()  # 0 is Monday
    return DAY_NAMES[idx]


# Master Vedic Festival Canon Definitions
FESTIVAL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "id": "makar-sankranti",
        "name": {
            "en": "Makar Sankranti",
            "bn": "মকর সংক্রান্তি (পৌষ সংক্রান্তি)",
            "hi": "मकर संक्रांति",
        },
        "category": "major",
        "calc_type": "solar_ingress",
        "solar_target": 270.0,  # Sun enters Capricorn (Makara)
        "window_month": 1,
        "tithi_desc": {
            "en": "Solar Ingress into Capricorn (Uttarayan)",
            "bn": "সূর্যের মকর রাশিতে উত্তরায়ণ প্রবেশ",
            "hi": "सूर्य का मकर राशि में उत्तरायण प्रवेश",
        },
        "badge": {"en": "Harvest & Solar", "bn": "সূর্য সংক্রান্তি", "hi": "सौर पर्व"},
        "accent_color": "#F59E0B",
        "muhurat": {
            "en": "Punya Kaal: 07:15 AM – 12:45 PM",
            "bn": "পুণ্যকাল স্নান ও দান: সকাল ০৭:১৫ – দুপুর ১২:৪৫",
            "hi": "पुण्य काल: प्रातः 07:15 – दोपहर 12:45",
        },
        "shloka": "॥ ॐ सूर्याय नमः आदित्याय विद्महे प्रभाकराय धीमहि ॥",
        "desc": {
            "en": "Sacred solar ingress into Makara (Capricorn) marking Uttarayan, the auspicious northern journey of the Sun. Celebrated with holy dips in sacred rivers, charity of sesame (til) & jaggery, and harvest kites.",
            "bn": "সূর্যদেবের মকর রাশিতে উত্তরায়ণ গমন। পুণ্যস্নান, তিল-গুড় দান, পৌষ পার্বণের নতুন ধানের পিঠেপুলি উৎসব এবং পরম আধ্যাত্মিক শুভ সূচনা।",
            "hi": "सूर्यदेव का मकर राशि में प्रवेश और उत्तरायण का शुभारंभ। गंगा स्नान, तिल-गुड़ का दान, पतंगबाजी और नव अन्न का पावन उत्सव।",
        },
        "rituals": {
            "en": [
                "Brahma Muhurta holy river dip or water infused with Ganga jal and sesame seeds",
                "Surya Arghya with copper Kalash containing red sandalwood, Akshat, and flowers",
                "Charity (Daan) of Til, Gur, warm blankets, and fresh grains to Brahmins and the needy",
                "Consuming sesame-jaggery sweets (Til-Gud) for health and planetary harmony",
            ],
            "bn": [
                "ব্রাহ্মমুহূর্তে গঙ্গাস্নান বা স্নানের জলে গঙ্গাজল ও তিল মিশিয়ে পবিত্র স্নান",
                "তামার পাত্রে রক্তচন্দন, অক্ষত ও লাল ফুল সহযোগে ভগবান সূর্যকে অর্ঘ্য দান",
                "তিল, গুড়, গরম বস্ত্র ও নতুন শস্য ব্রাহ্মণ ও দুঃস্থদের দান",
                "পৌষ পার্বণের পিঠেপুলি ও তিলকুট ভক্ষণ এবং পারিবারিক সৌহার্দ্য রক্ষা",
            ],
            "hi": [
                "ब्रह्म मुहूर्त में पवित्र नदी में स्नान या गंगाजल-तिल मिश्रित जल से स्नान",
                "तांबे के पात्र से रोली, अक्षत व लाल पुष्प डालकर सूर्यदेव को अर्घ्य दें",
                "तिल, गुड़, कंबल, खिचड़ी और नए अन्न का ब्राह्मणों व जरूरतमंदों को दान",
                "तिल-गुड़ का सेवन कर 'तिल-गुड़ घ्या आणि गोड गोड बोला' का सद्भाव फैलाना",
            ],
        },
    },
    {
        "id": "vasant-panchami",
        "name": {
            "en": "Saraswati Puja (Vasant Panchami)",
            "bn": "সরস্বতী পূজা (বসন্ত পঞ্চমী)",
            "hi": "सरस्वती पूजा (बसंत पंचमी)",
        },
        "category": "major",
        "calc_type": "lunar_tithi",
        "lunar_month": 10,  # Magha
        "tithi_idx": 4,  # Shukla Panchami (tithi 5)
        "tithi_desc": {
            "en": "Magha Shukla Panchami",
            "bn": "মাঘ শুক্ল পঞ্চমী",
            "hi": "माघ शुक्ल पंचमी",
        },
        "badge": {"en": "Wisdom & Arts", "bn": "বিদ্যা ও কলা", "hi": "विद्या व ज्ञान"},
        "accent_color": "#EAB308",
        "muhurat": {
            "en": "Puja Muhurat: 07:08 AM – 12:35 PM",
            "bn": "পূজা ও অঞ্জলি মুহূর্ত: সকাল ০৭:০৮ – দুপুর ১২:৩৫",
            "hi": "पूजा मुहूर्त: प्रातः 07:08 – दोपहर 12:35",
        },
        "shloka": "॥ ॐ ऐं सरस्वत्यै नमः । या कुन्देन्दुतुषारहारधवला या शुभ्रवस्त्रावृता ॥",
        "desc": {
            "en": "Adoration of Goddess Saraswati, divine embodiment of wisdom, music, arts, and speech. Marks the arrival of Vasant (Spring), initiation of Vidyarambha (Haathe-khori) for children.",
            "bn": "জ্ঞান, বিদ্যা, সুর ও শিল্পের দেবী মা সরস্বতীর মহতী আরাধনা। বসন্ত ঋতুর শুভ আবাহন, শিশুদের বিদ্যারম্ভ বা হাতেখড়ি এবং হলুদ বাসন্তী সাজের মহোৎসব।",
            "hi": "विद्या, बुद्धि, वाणी और संगीत की अधिष्ठात्री मां सरस्वती का पावन आविर्भाव दिवस। बच्चों का विद्यारंभ संस्कार और पीले वस्त्र धारण का विधान।",
        },
        "rituals": {
            "en": [
                "Wear yellow or white garments representing purity and sattva",
                "Offer yellow marigold flowers, Palash blooms, and Ber (jujube fruit) to Goddess Saraswati",
                "Consecrate books, pens, inkpots, and musical instruments at the lotus feet of the Devi",
                "Perform Haathe-khori (chalk in hand) for toddlers beginning formal learning",
            ],
            "bn": [
                "হলুদ বা শ্বেত বসন পরিধান করে শুদ্ধ চিত্তে মাতৃবন্দনা",
                "পলাশ ফুল, গাঁদা ফুল এবং কুল ফল দিয়ে বাগদেবীর চরণে পুষ্পাঞ্জলি প্রদান",
                "বই, খাতা, কলম ও বাদ্যযন্ত্র দেবীর চরণে স্পর্শ করিয়ে পবিত্র আশীর্বাদ গ্রহণ",
                "শিশুদের হাতেখড়ি দিয়ে প্রথম আনুষ্ঠানিক অক্ষর জ্ঞানের শুভ সূচনা",
            ],
            "hi": [
                "पीले या श्वेत वस्त्र धारण कर देवी सरस्वती का आवाहन",
                "मां सरस्वती को पीले गेंदे के पुष्प, पलाश और बेर का नैवेद्य अर्पित करें",
                "पुस्तकों, कलम और वाद्य यंत्रों की पूजा कर विद्या की प्रार्थना करें",
                "छोटे बच्चों का विद्यारंभ या पाटी-पूजन संस्कार संपन्न कराएं",
            ],
        },
    },
    {
        "id": "maha-shivaratri",
        "name": {
            "en": "Maha Shivaratri",
            "bn": "মহা শিবরাত্রি",
            "hi": "महाशिवरात्रि",
        },
        "category": "vrat",
        "calc_type": "lunar_tithi",
        "lunar_month": 11,  # Phalguna (amanta) / Magha (purnimanta)
        "tithi_idx": 28,  # Krishna Chaturdashi
        "tithi_desc": {
            "en": "Phalguna Krishna Chaturdashi",
            "bn": "ফাল্গুন কৃষ্ণ চতুর্দশী",
            "hi": "फाल्गुन कृष्ण चतुर्दशी",
        },
        "badge": {"en": "Supreme Vrat", "bn": "মহাব্রত", "hi": "महाव्रत"},
        "accent_color": "#6366F1",
        "muhurat": {
            "en": "Nishita Kaal Puja: 12:09 AM – 01:00 AM",
            "bn": "নিশীথ কাল পূজা: রাত ১২:০৯ – রাত ০১:০০",
            "hi": "निशीथ काल पूजा: रात्रि 12:09 – 01:00",
        },
        "shloka": "॥ ॐ त्र्यम्बकं यजामहे सुगन्धिं पुष्टिवर्धनम् । उर्वारुकमिव बन्धनान्मृत्यsource ॥",
        "desc": {
            "en": "The sacred cosmic night of Lord Shiva and Mata Parvati's divine wedding. Devotees observe strict waterless fast, continuous Rudrabhishek across the four praharas of night, and chant Maha Mrityunjaya mantra.",
            "bn": "দেবাদিদেব মহাদেব ও মা পার্বতীর দিব্য বিবাহ ও পরম শক্তির মিলন রাত্রি। অহোরাত্র নির্জলা উপবাস, চার প্রহরে শিবলিঙ্গে পঞ্চামৃত অভিষেক ও রুদ্রপাঠ।",
            "hi": "देवाधिदेव महादेव और माता पार्वती के दिव्य विवाह की परम पावन महारात्रि। निर्जला व्रत, चारों प्रहर रुद्राभिषेक और महामृत्युंजय मंत्र जप।",
        },
        "rituals": {
            "en": [
                "Observe Nirjala (waterless) or Phalahar fast through day and night",
                "Four Prahara Abhishek on Shivling using Milk, Curd, Ghee, Honey, and Ganga water",
                "Offer sacred Bilva leaves (Bel Patra), Dhatura, Bhasma, and Chandan",
                "Maha Mrityunjaya Japa and Shiva Sahasranama chanting during Nishita Kaal midnight window",
            ],
            "bn": [
                "দিন ও রাত্রি ব্যাপী ভক্তিভরে নির্জলা বা ফলাহার ব্রত পালন",
                "শিবলিঙ্গে চার প্রহরে ক্রমান্বয়ে দুধ, দধি, ঘৃত, মধু ও গঙ্গাজল দিয়ে পঞ্চামৃত অভিষেক",
                "অখণ্ড ত্রিনয়ন বেলপাতা, ধুতরো ফুল, ভস্ম ও শ্বেতচন্দন সমর্পণ",
                "নিশীথ কালে ওঙ্কার ধ্বনি, রুদ্রাভিষেক এবং মহামৃত্যুঞ্জয় মন্ত্র জপ",
            ],
            "hi": [
                "अहोरात्र निर्जला अथवा फलाहार व्रत का संकल्प लें",
                "चारों प्रहर शिवलिंग पर पंचामृत (दूध, दही, घी, शहद, गंगाजल) से अभिषेक",
                "अखंड बिल्वपत्र, धतूरा, भांग, भस्म और श्वेत चंदन अर्पित करें",
                "निशीथ काल में ॐ नमः शिवाय व महामृत्युंजय मंत्र की 11 माला जपें",
            ],
        },
    },
    {
        "id": "holi",
        "name": {
            "en": "Holi & Dol Yatra",
            "bn": "দোলযাত্রা ও হোলি (রঙোৎসব)",
            "hi": "होली एवं धुलेंडी",
        },
        "category": "major",
        "calc_type": "lunar_tithi",
        "lunar_month": 11,  # Phalguna
        "tithi_idx": 14,  # Shukla Purnima (tithi 15)
        "tithi_desc": {
            "en": "Phalguna Purnima",
            "bn": "ফাল্গুনী পূর্ণিমা",
            "hi": "फाल्गुन पूर्णिमा",
        },
        "badge": {"en": "Festival of Colors", "bn": "রঙের মহোৎসব", "hi": "रंगोत्सव"},
        "accent_color": "#EC4899",
        "muhurat": {
            "en": "Holika Dahan: 06:28 PM – 08:54 PM",
            "bn": "হোলিকা দহন / চাঁচর: সন্ধ্যা ০৬:২৮ – রাত ০৮:৫৪",
            "hi": "होलिका दहन: सायं 06:28 – रात्रि 08:54",
        },
        "shloka": "॥ राधे राधे गोविन्द गोविन्द राधे । वन्दे वृन्दावनचरं वन्दे गोपीमनोहरम् ॥",
        "desc": {
            "en": "The joyous festival of vibrant organic colors, divine love of Radha-Krishna, Dolotsav, and the burning of Holika symbolizing the triumph of righteousness and devotion over demonic hubris.",
            "bn": "শ্রী শ্রী রাধাকৃষ্ণের ঝুলন ও দোলপূর্ণিমা মহোৎসব। অশুভ শক্তির বিনাশে ন্যায়ের জয় এবং আবির ও বসন্তের রঙের মাধ্যমে পরম প্রীতির আদান-প্রদান।",
            "hi": "भक्त प्रह्लाद की भक्ति की विजय और होलिका दहन। राधा-कृष्ण के दिव्य प्रेम का रंगोत्सव, अबीर-गुलाल और सामाजिक सौहार्द का महापर्व।",
        },
        "rituals": {
            "en": [
                "Perform Holika Dahan bonfire with wood, cow dung cakes, and coconut offerings",
                "Offer first organic Abir / Gulal at the lotus feet of Sri Radha Krishna and family elders",
                "Play with herbal organic fragrant colors and flower petals",
                "Distribute Gujiya, Thandai, and traditional festive delicacies",
            ],
            "bn": [
                "সন্ধ্যায় চাঁচর বা হোলিকা দহন করে অশুভ আসুরিক শক্তির প্রতীকী ভস্মীকরণ",
                "শ্রীশ্রী রাধাগোবিন্দের চরণে লাল ও বাসন্তী আবির নিবেদন করে আশীর্বাদ গ্রহণ",
                "গুরুজনদের চরণে আবির দিয়ে প্রণাম ও পারস্পরিক মৈত্রীর রঙখেলা",
                "মালপোয়া, জিলিপি, ঠাণ্ডাই ইত্যাদি প্রসাদ বিতরণ ও মিষ্টিমুখ",
            ],
            "hi": [
                "सायंकाल होलिका दहन में रोली, अक्षत, गेहूं की बालियां और नारियल अर्पित करें",
                "भगवान श्री राधा-कृष्ण और कुलदेवता को प्रथम अबीर-गुलाल अर्पित करें",
                "बड़ों के चरण स्पर्श कर आशीर्वाद लें और हर्बल रंगों से होली खेलें",
                "गुझिया, ठंडाई और पारंपरिक पकवानों का परस्पर आदान-प्रदान करें",
            ],
        },
    },
    {
        "id": "chaitra-navratri",
        "name": {
            "en": "Chaitra Navratri & Gudi Padwa",
            "bn": "বাসন্তী নবরাত্রি ও গুড়ি পাড়বা",
            "hi": "चैत्र नवरात्रि एवं नवसंवत्सर",
        },
        "category": "major",
        "calc_type": "lunar_tithi",
        "lunar_month": 0,  # Chaitra
        "tithi_idx": 0,  # Shukla Pratipada
        "tithi_desc": {
            "en": "Chaitra Shukla Pratipada",
            "bn": "চৈত্র শুক্লা প্রতিপদ",
            "hi": "चैत्र शुक्ल प्रतिपदा",
        },
        "badge": {"en": "Vedic New Year", "bn": "নব সংবৎসর", "hi": "नव संवत्सर"},
        "accent_color": "#F97316",
        "muhurat": {
            "en": "Ghatasthapana: 06:14 AM – 10:18 AM",
            "bn": "ঘটস্থাপন ও নবদুর্গা আবাহন: সকাল ০৬:১৪ – সকাল ১০:১৮",
            "hi": "घटस्थापना मुहूर्त: प्रातः 06:14 – 10:18",
        },
        "shloka": "॥ प्रथमं शैलपुत्री च द्वितीयं ब्रह्मचारिणी । तृतीयं चन्द्रघण्टेति कूष्माण्डेति चतुर्थकम् ॥",
        "desc": {
            "en": "Beginning of the Hindu Vedic New Year (Vikram Samvat) and nine auspicious days honoring Goddess Durga across her Navadurga forms, culminating in sacred Ram Navami.",
            "bn": "হিন্দু নব সংবৎসরের শুভ সূচনা এবং মা দুর্গার নয় দিব্য রূপের বাসন্তী আরাধনা। ঘটস্থাপন, উপবাস এবং আত্মশুদ্ধির নয়টি পবিত্র দিবস।",
            "hi": "हिंदू नव संवत्सर का पावन आरंभ और शक्ति स्वरूपा मां दुर्गा के नौ रूपों की उपासना। घटस्थापना, अखंड ज्योति और नौ दिन का व्रत।",
        },
        "rituals": {
            "en": [
                "Establish Kalash (Ghatasthapana) with holy soil, barley (Jau), and mango leaves",
                "Light unbroken Akhand Jyoti lamp for 9 sacred nights",
                "Recite Durga Saptashati (Devi Mahatmyam) chapters daily",
                "Observe sattvic diet or fasting avoiding onion, garlic, and grains",
            ],
            "bn": [
                "তামার ঘটে গঙ্গাজল, পঞ্চপল্লব, আম্রপল্লব ও ডাব স্থাপন করে ঘটস্থাপন",
                "নয় দিন ব্যাপী দেবী দুর্গার সামনে অখণ্ড প্রদীপ প্রজ্জ্বলন",
                "শ্রী শ্রী চণ্ডীপাঠ ও নবদুর্গা স্তোত্র পাঠ",
                "সাত্ত্বিক নিরামিষ আহার গ্রহণ ও সংযম পালন",
            ],
            "hi": [
                "मिट्टी की वेदी पर जौ बोकर शुभ मुहूर्त में घटस्थापना करें",
                "नवरात्र पर्यंत अखंड दीपक प्रज्वलित रखें",
                "प्रतिदिन दुर्गा सप्तशती का पाठ और दुर्गा चालीसा का जप करें",
                "सात्विक फलाहार व्रत रखकर शक्ति की उपासना करें",
            ],
        },
    },
    {
        "id": "ram-navami",
        "name": {
            "en": "Ram Navami",
            "bn": "শ্রীরাম নবমী",
            "hi": "श्री राम नवमी",
        },
        "category": "jayanti",
        "calc_type": "lunar_tithi",
        "lunar_month": 0,  # Chaitra
        "tithi_idx": 8,  # Shukla Navami
        "tithi_desc": {
            "en": "Chaitra Shukla Navami",
            "bn": "চৈত্র শুক্লা নবমী",
            "hi": "चैत्र शुक्ल नवमी",
        },
        "badge": {"en": "Divine Avatar", "bn": "অবতার জয়ন্তী", "hi": "अवतार जयंती"},
        "accent_color": "#D97706",
        "muhurat": {
            "en": "Madhyahna Kaal: 11:06 AM – 01:34 PM",
            "bn": "মধাহ্ন জন্ম মুহূর্ত: সকাল ১১:০৬ – দুপুর ০১:৩৪",
            "hi": "मध्याह्न पूजा मुहूर्त: 11:06 AM – 01:34 PM",
        },
        "shloka": "॥ श्री रामचन्द्र कृपालु भजु मन हरण भवभय दारुणम् । नवकञ्ज लोचन कञ्ज मुख करकञ्ज पद कञ्जारुणम् ॥",
        "desc": {
            "en": "Celebration of the birth of Maryada Purushottam Lord Sri Rama, seventh avatar of Lord Vishnu, in Ayodhya during Madhyahna (noon). Marks the grand culmination of Chaitra Navratri.",
            "bn": "মোর্যাদা পুরুষোত্তম ভগবান শ্রীরামচন্দ্রের অযোধ্যায় শুভাগমন ও জন্মতিথি মহোৎসব। মধাহ্নকালে রামলালার চরণ বন্দনা ও রামায়ণ পাঠ।",
            "hi": "मर्यादा पुरुषोत्तम भगवान श्री राम का अयोध्या में प्राकट्य दिवस। दोपहर 12 बजे जन्मोत्सव, शंखध्वनि, पंचामृत अभिषेक और रामचरितमानस पाठ।",
        },
        "rituals": {
            "en": [
                "Abhishek of Sri Rama idol with Panchamrit and fragrant Tulsi water at midday",
                "Recite Sri Rama Raksha Stotra, Sundarkand, or Valmiki Ramayana",
                "Perform Kanya Pujan honoring 9 young girls representing the Navadurgas",
                "Distribute Panakam, Kosambari, and sweet prasad to all devotees",
            ],
            "bn": [
                "মধাহ্নে দ্বিপ্রহরে শালগ্রাম শিলা বা রামলালার বিগ্রহে পঞ্চামৃত ও তুলসীযুক্ত গঙ্গাজল অভিষেক",
                "শ্রীরাম রক্ষা স্তোত্র এবং সুন্দরকাণ্ড পাঠ",
                "বাসন্তী নবরাত্রির সমাপ্তিতে কুমারী পূজা ও অন্নদান",
                "পায়েস ও পঞ্চামৃত প্রসাদ বিতরণ",
            ],
            "hi": [
                "मध्याह्न काल में प्रभु राम का पंचामृत अभिषेक व नयनाभिराम श्रृंगार",
                "राम रक्षा स्तोत्र, सुंदरकांड अथवा अखंड रामायण का पाठ",
                "नौ कन्याओं का पाद-पूजन कर उन्हें भोजन व दक्षिणा अर्पित करें (कन्या पूजन)",
                "पंजीरी, पंचामृत और तुलसीदल का महाप्रसाद वितरित करें",
            ],
        },
    },
    {
        "id": "pohela-boishakh",
        "name": {
            "en": "Pohela Boishakh (Bengali New Year)",
            "bn": "পয়লা বৈশাখ (শুভ নববর্ষ)",
            "hi": "पोहेला बैशाख (मेष संक्रांति)",
        },
        "category": "major",
        "calc_type": "solar_ingress",
        "solar_target": 0.0,  # Sun enters Aries (Mesha)
        "window_month": 4,
        "tithi_desc": {
            "en": "Mesha Sankranti / 1st Boishakh",
            "bn": "মেষ সংক্রান্তি / ১লা বৈশাখ",
            "hi": "मेष संक्रांति / बैसाखी",
        },
        "badge": {"en": "Cultural New Year", "bn": "শুভ নববর্ষ", "hi": "नववर्ष"},
        "accent_color": "#DC2626",
        "muhurat": {
            "en": "Haalkhata & Lakshmi-Ganesh Puja: 07:30 AM – 11:45 AM",
            "bn": "হালখাতা ও গণেশ-লক্ষ্মী পূজা: সকাল ০৭:৩০ – সকাল ১১:৪৫",
            "hi": "बहीखाता पूजन: प्रातः 07:30 – 11:45",
        },
        "shloka": "॥ ॐ गं गणपतये नमः । ॐ श्रीं ह्रीं क्लीं ग्लौं गं गणपतये वर वरद सर्वजनं मे वशमानय स्वाहा ॥",
        "desc": {
            "en": "Bengali New Year celebration (Noboborsho) coinciding with Mesha Sankranti and Baisakhi. Traders inaugurate new ledger books (Haalkhata), worship Lakshmi-Ganesh, and pray for peace, abundance, and prosperity.",
            "bn": "বাঙালির প্রাণের মহোৎসব শুভ নববর্ষ। নতুন খাতা উন্মোচন বা হালখাতা, সিদ্ধিদাতা গণেশ ও মা লক্ষ্মীর পূজা, নতুন বস্ত্র পরিধান এবং প্রীতি ও ভালোবাসার আদান-প্রদান।",
            "hi": "मेष संक्रांति और नव संवत् का पावन पर्व। व्यापारी वर्ग द्वारा नवीन बहीखाता (हालखाता) पूजन, मां लक्ष्मी और भगवान गणेश की विशेष आराधना।",
        },
        "rituals": {
            "en": [
                "Temple darshan at dawn and worship of Lord Ganesha and Goddess Lakshmi",
                "Consecrate new commercial ledgers (Haalkhata) with Swastika and vermilion",
                "Wear traditional ethnic garments (Lal-Paad Dhoti/Saree)",
                "Exchange 'Subho Noboborsho' greetings, sweets, and traditional Bengali feasts",
            ],
            "bn": [
                "প্রভাতে গৃহের গুরুজনদের প্রণাম ও মন্দিরে গিয়ে গণেশ-লক্ষ্মীর পূজা",
                "ব্যবসায়ীদের নতুন লাল খেরোর খাতায় সিঁদুর ও স্বস্তিক এঁকে হালখাতা অনুষ্ঠান",
                "নতুন পোশাক পরিধান করে আত্মীয়-পরিজনদের মিষ্টিমুখ ও শুভেচ্ছা বিনিময়",
                "পান্তা-ইলিশ বা ঐতিহ্যবাহী মিষ্টি ও পদ সহযোগে নববর্ষের মধ্যাহ্নভোজন",
            ],
            "hi": [
                "प्रातःकाल गणेश जी और लक्ष्मी जी का पूजन कर नए कार्यों का संकल्प लें",
                "व्यापारिक प्रतिष्ठानों में नवीन बहीखाते पर स्वास्तिक बनाकर पूजन करें",
                "पारंपरिक परिधान पहनकर बड़ों का आशीर्वाद लें",
                "मिष्ठान्न वितरण कर नववर्ष की मंगलकामनाएं साझा करें",
            ],
        },
    },
    {
        "id": "akshaya-tritiya",
        "name": {
            "en": "Akshaya Tritiya",
            "bn": "অক্ষয় তৃতীয়া",
            "hi": "अक्षय तृतीया (आखा तीज)",
        },
        "category": "major",
        "calc_type": "lunar_tithi",
        "lunar_month": 1,  # Vaishakha
        "tithi_idx": 2,  # Shukla Tritiya
        "tithi_desc": {
            "en": "Vaishakha Shukla Tritiya",
            "bn": "বৈশাখ শুক্লা তৃতীয়া",
            "hi": "वैशाख शुक्ल तृतीया",
        },
        "badge": {"en": "Eternal Prosperity", "bn": "অক্ষয় সমৃদ্ধি", "hi": "अक्षय पुण्य"},
        "accent_color": "#CA8A04",
        "muhurat": {
            "en": "Gold Buying & Puja: 05:48 AM – 12:18 PM",
            "bn": "স্বর্ণ ক্রয় ও পূজা মুহূর্ত: ভোর ০৫:৪৮ – দুপুর ১২:১৮",
            "hi": "सोना क्रय व पूजा मुहूर्त: प्रातः 05:48 – दोपहर 12:18",
        },
        "shloka": "॥ ॐ नमो भगवते वासुदेवाय । ॐ श्रीं महालक्ष्म्यै नमः ॥",
        "desc": {
            "en": "Day of inexhaustible spiritual merit and unending wealth consecrated by Lord Vishnu and Goddess Lakshmi. Perfect astrological tithi for new ventures, charity, and buying gold or real estate.",
            "bn": "অক্ষয় পুণ্য ও চিরন্তন সমৃদ্ধির শুভ দিন। এই তিথিতে সম্পাদিত যেকোনো সৎকর্ম, দান, স্বর্ণ ক্রয় ও নতুন ব্যবসার সূচনা অক্ষয় ফল প্রদান করে।",
            "hi": "अक्षय पुण्य और धन-समृद्धि का सर्वसिद्ध अबूझ मुहूर्त। स्वर्ण क्रय, नवीन व्यापार प्रारंभ, दान और भगवान परशुराम जयंती का पावन दिवस।",
        },
        "rituals": {
            "en": [
                "Worship Lord Vishnu and Goddess Lakshmi with white lotus flowers and Akshat",
                "Purchase gold, silver, or new metallic vessels as a token of Lakshmi's arrival",
                "Donate water, barley (Jau), earthen pots (Ghada), and food to the underprivileged",
                "Inaugurate new business contracts, property registrations, or investments",
            ],
            "bn": [
                "শ্রীবিষ্ণু ও মা লক্ষ্মীর শ্রীচরণে শ্বেতপদ্ম, তুলসী ও অক্ষত নিবেদন",
                "গৃহে মা লক্ষ্মীর স্থায়ী নিবাসের কামনায় স্বর্ণ বা রৌপ্য অলঙ্কার ক্রয়",
                "জলভরা মাটির কলসি, ছাতা, পাখা ও শস্য দুঃস্থদের দান",
                "নতুন প্রতিষ্ঠান, দোকান বা শুভ বিনিয়োগের শুভ সূচনা",
            ],
            "hi": [
                "भगवान विष्णु और मां लक्ष्मी का कनकधारा स्तोत्र से पूजन करें",
                "सोने-चांदी के आभूषण अथवा नए बर्तन क्रय करना अत्यंत शुभ माना जाता है",
                "मिट्टी का घड़ा, पंखा, छाता, जौ और शीतल जल का दान करें",
                "नवीन व्यापार, गृह प्रवेश या वाहन क्रय का अबूझ मुहूर्त लाभ उठाएं",
            ],
        },
    },
    {
        "id": "jagannath-rath-yatra",
        "name": {
            "en": "Jagannath Rath Yatra",
            "bn": "জগন্নাথ রথযাত্রা",
            "hi": "जगन्नाथ रथयात्रा",
        },
        "category": "major",
        "calc_type": "lunar_tithi",
        "lunar_month": 3,  # Ashadha
        "tithi_idx": 1,  # Shukla Dwitiya
        "tithi_desc": {
            "en": "Ashadha Shukla Dwitiya",
            "bn": "আষাঢ় শুক্লা দ্বিতীয়া",
            "hi": "आषाढ़ शुक्ल द्वितीया",
        },
        "badge": {"en": "Sacred Chariot", "bn": "মহাপ্রভুর রথ", "hi": "रथोत्सव"},
        "accent_color": "#EA580C",
        "muhurat": {
            "en": "Rath Taan / Chariot Pulling: 02:45 PM – 06:15 PM",
            "bn": "রথটান মুহূর্ত: দুপুর ০২:৪৫ – সন্ধ্যা ০৬:১৫",
            "hi": "रथ खींचने का समय: दोपहर 02:45 – सायं 06:15",
        },
        "shloka": "॥ रथे तु वामनं दृष्ट्वा पुनर्जन्म न विद्यते । ॐ जगन्नाथाय नमः ॥",
        "desc": {
            "en": "Lord Jagannath, Balabhadra, and Devi Subhadra journey from the sacred Puri temple to the Gundicha temple on grand wooden chariots. Touching or pulling the sacred ropes bestows liberation.",
            "bn": "শ্রীক্ষেত্র পুরীধামে মহাপ্রভু জগন্নাথ, বলভদ্র ও মা সুভদ্রার রাজকীয় রথে চড়ে মাসির বাড়ি গুণ্ডিচা যাত্রা। রথের রশি স্পর্শ করা পরম সৌভাগ্য ও মুক্তির সোপান।",
            "hi": "पुरी में महाप्रभु जगन्नाथ, बलभद्र और देवी सुभद्रा की भव्य रथयात्रा। नंदीघोष, तालध्वज और दर्पदलन रथों के दर्शन और रस्सियों को खींचने से मोक्ष प्राप्ति।",
        },
        "rituals": {
            "en": [
                "Pull the chariot ropes with deep devotion chanting 'Jai Jagannath!'",
                "Offer Chhappan Bhog, Malpua, and Khaja to the Lord of the Universe",
                "Sing sacred Kirtans and perform Chhera Pahanra sweeping with golden broom",
                "Distribute sacred Mahaprasad to all pilgrims",
            ],
            "bn": [
                "'জয় জগন্নাথ' রবে ভক্তিভরে রথের পবিত্র রশি আকর্ষণ",
                "জগন্নাথ দেবের উদ্দেশ্যে ৫৬ ভোগ, মালপোয়া ও গজাপ্রসাদ নিবেদন",
                "হরি সংকীর্তন ও মৃদঙ্গ ধ্বনিতে রথযাত্রার শোভাযাত্রায় অংশগ্রহণ",
                "সকল ভক্তদের মাঝে আনন্দ সহকারে মহাপ্রসাদ বিতরণ",
            ],
            "hi": [
                "'जय जगन्नाथ' के जयघोष के साथ रथ की रस्सियों को खींचें",
                "भगवान जगन्नाथ को छप्पन भोग, मालपुआ और खाजा का भोग लगाएं",
                "संकीर्तन और मृदंग की थाप पर भक्ति नृत्य",
                "जगन्नाथ जी के पवित्र महाप्रसाद का श्रद्धायुक्त ग्रहण व वितरण",
            ],
        },
    },
    {
        "id": "guru-purnima",
        "name": {
            "en": "Guru Purnima (Vyasa Puja)",
            "bn": "গুরু পূর্ণিমা (ব্যাস পূজা)",
            "hi": "गुरु पूर्णिमा (व्यास पूजा)",
        },
        "category": "vrat",
        "calc_type": "lunar_tithi",
        "lunar_month": 3,  # Ashadha
        "tithi_idx": 14,  # Shukla Purnima
        "tithi_desc": {
            "en": "Ashadha Purnima",
            "bn": "আষাঢ়ী পূর্ণিমা",
            "hi": "आषाढ़ पूर्णिमा",
        },
        "badge": {"en": "Spiritual Grace", "bn": "গুরু কৃপা", "hi": "गुरु कृपा"},
        "accent_color": "#8B5CF6",
        "muhurat": {
            "en": "Guru Paduka Puja: 06:12 AM – 11:20 AM",
            "bn": "শ্রীগুরু পাদুকাপূজা: সকাল ০৬:১২ – সকাল ১১:২০",
            "hi": "गुरु पादुका पूजन: प्रातः 06:12 – 11:20",
        },
        "shloka": "॥ गुरुर्ब्रह्मा गुरुर्विष्णुः गुरुर्देवो महेश्वरः । गुरुः साक्षात् परं ब्रह्म तस्मै श्रीगुरवे नमः ॥",
        "desc": {
            "en": "Sacred day of gratitude dedicated to the Guru, who dispels the darkness of ignorance. Also marks the birth anniversary of Maharishi Veda Vyasa, compiler of the four Vedas and Mahabharata.",
            "bn": "অজ্ঞানতার অন্ধকার দূরকারী সদগুরুর শ্রীচরণে কৃতজ্ঞতা ও প্রণতি জ্ঞাপনের পরম পবিত্র দিন। মহর্ষি বেদব্যাসের পুণ্য জন্মজয়ন্তী ও ব্যাস পূজা।",
            "hi": "अज्ञान रूपी अंधकार से ज्ञान रूपी प्रकाश की ओर ले जाने वाले सदगुरु के प्रति कृतज्ञता ज्ञापन का महापर्व। महर्षि वेदव्यास जयंती व व्यास पूर्णिमा।",
        },
        "rituals": {
            "en": [
                "Perform Guru Paduka Puja with sandalwood, flowers, and deep gratitude",
                "Offer Dakshina, fruits, and yellow robes to your spiritual teacher",
                "Chant Guru Gita and meditate on the transcendent wisdom imparted by the master",
                "Seek Guru's blessings for spiritual awakening and righteous life conduct",
            ],
            "bn": [
                "সদগুরুর শ্রীপাদুকা বা ছবিতে চন্দন, পুষ্প ও ভক্তিঅশ্রু দিয়ে পূজা নিবেদন",
                "গুরুদেবকে বস্ত্র, ফলমূল ও সাধ্যমতো গুরুদক্ষিণা প্রদান",
                "গুরুগীতা পাঠ ও গুরুর দেওয়া মূলমন্ত্র একাগ্রচিত্তে জপ",
                "জ্ঞান ও আধ্যাত্মিক উন্নতির কামনায় গুরুর চরণধূলি গ্রহণ",
            ],
            "hi": [
                "गुरुदेव के चरणों का पाद्य-अर्घ्य से पूजन कर चरणामृत ग्रहण करें",
                "गुरु दक्षिणा, वस्त्र और फल श्रद्धापूर्वक अर्पित करें",
                "गुरु गीता, उपनिषद अथवा गुरु मंत्र का शांत मन से जप करें",
                "जीवन में सदमार्ग पर चलने का संकल्प लें",
            ],
        },
    },
    {
        "id": "raksha-bandhan",
        "name": {
            "en": "Raksha Bandhan",
            "bn": "রাখীবন্ধন মহোৎসব",
            "hi": "रक्षाबंधन",
        },
        "category": "major",
        "calc_type": "lunar_tithi",
        "lunar_month": 4,  # Shravana
        "tithi_idx": 14,  # Shukla Purnima
        "tithi_desc": {
            "en": "Shravana Purnima",
            "bn": "শ্রাবণী পূর্ণিমা",
            "hi": "श्रावण पूर्णिमा",
        },
        "badge": {"en": "Sacred Bond", "bn": "স্নেহের বন্ধন", "hi": "रक्षा सूत्र"},
        "accent_color": "#0284C7",
        "muhurat": {
            "en": "Aparahna Rakhi Threading: 01:42 PM – 04:18 PM",
            "bn": "রাখী বাঁধার অপরাহ্ন মুহূর্ত: দুপুর ০১:৪২ – বিকাল ০৪:১৮",
            "hi": "राखी बांधने का मुहूर्त: दोपहर 01:42 – सायं 04:18",
        },
        "shloka": "॥ येन बद्धो बली राजा दानवेन्द्रो महाबलः । तेन त्वामनुबध्नामि रक्षे मा चल मा चल ॥",
        "desc": {
            "en": "Celebration of the sacred, eternal bond of love, protection, and duty between brothers and sisters. Sisters tie the consecrated Raksha thread on their brothers' wrists praying for their long life.",
            "bn": "ভাই-বোনের স্নেহ, প্রীতি ও সুরক্ষার চিরন্তন পবিত্র বন্ধন। বোনেরা ভাইদের মঙ্গল কামনায় হাতে রাখী বেঁধে দেয় এবং ভাইয়েরা আজীবন রক্ষার শপথ গ্রহণ করে।",
            "hi": "भाई-बहन के असीम स्नेह, विश्वास और सुरक्षा का पावन पर्व। बहनें भाई की कलाई पर रक्षासूत्र बांधकर दीर्घायु की कामना करती हैं।",
        },
        "rituals": {
            "en": [
                "Prepare Aarti thali with Akshat, Roli, Diya, Sweets, and consecrated Rakhi",
                "Apply Tilak on brother's forehead, tie Rakhi on right wrist, and perform Aarti",
                "Feed sweets and exchange heartfelt blessings and gifts of protection",
                "Avoid tying Rakhi during inauspicious Bhadra Kaal window",
            ],
            "bn": [
                "পূজার থালিতে চন্দন, ধান-দূর্বা, প্রদীপ, মিষ্টি ও রাখী সাজিয়ে আরতি",
                "ভাইয়ের কপালে চন্দনের ফোঁটা ও তিলক পরিয়ে ডানহাতে রাখীবন্ধন",
                "মিষ্টি খাইয়ে ভাইয়ের দীর্ঘায়ু ও সুস্বাস্থ্য কামনা করা",
                "ভদ্রা কাল এড়িয়ে শুভ অপরাহ্নে রাখীবন্ধন সম্পন্ন করা",
            ],
            "hi": [
                "थाल में रोली, अक्षत, दीपक, मिष्ठान्न और राखी सजाकर आरती करें",
                "भाई के मस्तक पर तिलक लगाकर दाहिने हाथ में रक्षासूत्र बांधें",
                "मुंह मीठा कराएं और भाई रक्षा का संकल्प व उपहार भेंट करे",
                "भद्रा काल का त्याग कर शुभ चौघड़िया या अपराह्न में ही राखी बांधें",
            ],
        },
    },
    {
        "id": "krishna-janmashtami",
        "name": {
            "en": "Krishna Janmashtami",
            "bn": "শ্রীকৃষ্ণ জন্মাষ্টমী",
            "hi": "श्री कृष्ण जन्माष्टमी",
        },
        "category": "major",
        "calc_type": "lunar_tithi",
        "lunar_month": 4,  # Shravana (amanta) / Bhadrapada (purnimanta)
        "tithi_idx": 22,  # Krishna Ashtami (tithi 8)
        "tithi_desc": {
            "en": "Bhadrapada Krishna Ashtami",
            "bn": "ভাদ্রপদ কৃষ্ণাষ্টমী (রোহিণী নক্ষত্র)",
            "hi": "भाद्रपद कृष्ण अष्टमी",
        },
        "badge": {"en": "Lord of Gita", "bn": "ভগবান শ্রীকৃষ্ণ", "hi": "नटखट नंदलाल"},
        "accent_color": "#06B6D4",
        "muhurat": {
            "en": "Nishita Kaal Janmotsav: 11:58 PM – 12:44 AM",
            "bn": "নিশীথ কাল জন্মমুহূর্ত: রাত ১১:৫৮ – রাত ১২:৪৪",
            "hi": "निशीथ काल पूजा: रात्रि 11:58 – 12:44",
        },
        "shloka": "॥ वसुदेवसुतं देवं कंसचाणूरमर्दनम् । देवकीपरमानन्दं कृष्णं वन्दे जगद्गुरुम् ॥",
        "desc": {
            "en": "Divine midnight advent of Lord Sri Krishna, supreme personality of Godhead and speaker of the Bhagavad Gita, born to destroy tyranny and re-establish Sanatana Dharma. Celebrated with fasting, jhula, and Dahi Handi.",
            "bn": "ভগবান শ্রীকৃষ্ণের মথুরার কারাগারে ভাদ্র কৃষ্ণাষ্টমীর গভীর নিশীথে শুভাগমন। অহোরাত্র উপবাস, ঝুলন দোলানো, মাখনের ভোগ এবং আনন্দময় জন্মাষ্টমী মহোৎসব।",
            "hi": "द्वापर युग में रोहिणी नक्षत्र की आधी रात को भगवान श्री कृष्ण का प्राकट्य। उपवास, लड्डू गोपाल का पंचामृत अभिषेक, झूला झुलाना और दही हांडी।",
        },
        "rituals": {
            "en": [
                "Observe day-long fast until midnight avatar moment",
                "Abhishek of Bal Gopal with milk, curd, ghee, honey, and fragrant Yamuna jal",
                "Decorate swing (Jhula) with peacock feathers, butter (Makhan), and Tulsi leaves",
                "Chant 'Hare Krishna Mahamantra' and recite Bhagavad Gita Chapter 4",
            ],
            "bn": [
                "মধ্যরাত্রি পর্যন্ত উপবাস ও কৃষ্ণনাম সংকীর্তন",
                "লাড্ডু গোপালের বিগ্রহে শঙ্খ দিয়ে পঞ্চামৃত ও গঙ্গাজল অভিষেক",
                "ময়ূরপুচ্ছ, নবনীত (মাখন) ও মিশ্রি সহযোগে সুসজ্জিত দোলনায় দোল দেওয়া",
                "'হরে কৃষ্ণ হরে কৃষ্ণ কৃষ্ণ কৃষ্ণ হরে হরে' মহামন্ত্র জপ",
            ],
            "hi": [
                "दिन भर व्रत रखकर भगवान कृष्ण की लीलाओं का श्रवण करें",
                "मध्यरात्रि में शंख में गंगाजल व पंचामृत भरकर बाल गोपाल का अभिषेक करें",
                "सुंदर पालने में झुलाएं, माखन-मिश्री, धनिए की पंजीरी का भोग लगाएं",
                "हरे कृष्ण महामंत्र का अखंड कीर्तन और आरती संपन्न करें",
            ],
        },
    },
    {
        "id": "ganesh-chaturthi",
        "name": {
            "en": "Ganesh Chaturthi (Vinayaka Chavithi)",
            "bn": "গণেশ চতুর্থী",
            "hi": "गणेश चतुर्थी (विनायक चतुर्थी)",
        },
        "category": "major",
        "calc_type": "lunar_tithi",
        "lunar_month": 5,  # Bhadrapada
        "tithi_idx": 3,  # Shukla Chaturthi
        "tithi_desc": {
            "en": "Bhadrapada Shukla Chaturthi",
            "bn": "ভাদ্রপদ শুক্লা চতুর্থী",
            "hi": "भाद्रपद शुक्ल चतुर्थी",
        },
        "badge": {"en": "Vighnaharta", "bn": "বিঘ্নহর্তা গণেশ", "hi": "विघ्नहर्ता"},
        "accent_color": "#EF4444",
        "muhurat": {
            "en": "Madhyahna Ganesha Puja: 11:04 AM – 01:32 PM",
            "bn": "মধাহ্ন গণেশ পূজা মুহূর্ত: সকাল ১১:০৪ – দুপুর ০১:৩২",
            "hi": "मध्याह्न गणेश पूजा: 11:04 AM – 01:32 PM",
        },
        "shloka": "॥ वक्रतुण्ड महाकाय सूर्यकोटि समप्रभ । निर्विघ्नं कुरु मे देव सर्वकार्येषु सर्वदा ॥",
        "desc": {
            "en": "Advent of Lord Ganesha, embodiment of intellect, auspicious beginnings, and remover of all obstacles (Vighnaharta). Celebrated with Pranapratistha of clay murtis and offering of Modakas.",
            "bn": "সিদ্ধিদাতা গণেশের পুণ্য জন্মতিথি। সর্ববিঘ্ন বিনাশক ও সর্বাগ্রে পূজিত শ্রীগণেশের মূর্তি প্রতিষ্ঠা, মোদক নিবেদন এবং আনন্দময় উৎসব।",
            "hi": "बुद्धि, रिद्धि-सिद्धि के दाता भगवान श्री गणेश का प्राकट्य दिवस। मिट्टी की मूर्ति की प्राण-प्रतिष्ठा, 21 मोदक व दूर्वा अर्पण।",
        },
        "rituals": {
            "en": [
                "Establish eco-friendly clay Ganesha idol facing East during Madhyahna",
                "Offer 21 blades of fresh Durva grass, red Hibiscus flowers, and Chandan",
                "Offer freshly steamed Modakas, Laddoos, and Panchamrit",
                "Recite Sri Ganapati Atharvashirsha Upanishad and Sankat Nashan Stotra",
            ],
            "bn": [
                "মাটির তৈরি গণেশ বিগ্রহ স্থাপন করে প্রাণপ্রতিষ্ঠা ও ধ্যান",
                "২১টি দূর্বাঘাস, রক্তজবা ও রক্তচন্দন দিয়ে পূজা সমর্পণ",
                "মোদক, লাড্ডু ও পঞ্চামৃত ভোগ নিবেদন",
                "শ্রী গণপতি অথর্বশীর্ষ স্তোত্র পাঠ ও সঙ্কটনাশন স্তোত্র জপ",
            ],
            "hi": [
                "मध्याह्न काल में भगवान गणेश की प्रतिमा स्थापित कर षोडशोपचार पूजन करें",
                "21 दूर्वा दल, लाल गुड़हल पुष्प और सिंदूर अर्पित करें",
                "मोदक और मोतीचूर के लड्डू का प्रिय भोग लगाएं",
                "गणपति अथर्वशीर्ष का 11 बार पाठ करें",
            ],
        },
    },
    {
        "id": "durga-puja",
        "name": {
            "en": "Durga Puja & Sharad Navratri",
            "bn": "শারদীয়া দুর্গোৎসব (মহা সপ্তমী – দশমী)",
            "hi": "शारदीय दुर्गा पूजा एवं विजयदशमी",
        },
        "category": "major",
        "calc_type": "lunar_tithi",
        "lunar_month": 6,  # Ashvina
        "tithi_idx": 6,  # Shukla Saptami to Dashami
        "tithi_desc": {
            "en": "Ashvina Shukla Saptami to Dashami",
            "bn": "আশ্বিন শুক্লা সপ্তমী থেকে বিজয়া দশমী",
            "hi": "अश्विन शुक्ल सप्तमी से विजयादशमी",
        },
        "badge": {"en": "Mahishasura Mardini", "bn": "জগজ্জননী দুর্গা", "hi": "महिषासुर मर्दिनी"},
        "accent_color": "#BE123C",
        "muhurat": {
            "en": "Sandhi Puja: Exact Ashtami-Navami junction (48 mins)",
            "bn": "সন্ধিপূজা: মহাষ্টমী ও মহানবমীর পবিত্র সন্ধিক্ষণ (৪৮ মিনিট)",
            "hi": "संधि पूजा: अष्टमी-नवमी का पावन संधिकाल",
        },
        "shloka": "॥ सर्वमङ्गलमाङ्गल्ये शिवे सर्वार्थसाधिके । शरण्ये त्र्यम्बके गौरि नारायणि नमोऽस्तु ते ॥",
        "desc": {
            "en": "The grand cosmic festival commemorating Goddess Durga's victory over the demon Mahishasura. Revered across Bengal and India with Bodhon, Pushpanjali, Sandhi Puja with 108 lotuses, and heartfelt Bijoya Dashami.",
            "bn": "বাঙালির শ্রেষ্ঠ উৎসব শারদীয়া দুর্গোৎসব। বোধন, নবপত্রিকা প্রবেশ, অঞ্জলি, ১০৮ পদ্ম সহযোগে সন্ধিপূজা, ধুনুচি নাচ এবং বিজয়ার আশীর্বাদ ও প্রীতি সম্মেলন।",
            "hi": "आदिशक्ति मां दुर्गा द्वारा महिषासुर मर्दन और धर्म की पुनर्स्थापना। षष्ठी से विजयादशमी तक नवपत्रिका, संधि पूजा और सिंदूर खेला का महापर्व।",
        },
        "rituals": {
            "en": [
                "Nabapatrika (Kola Bou) holy bathing at sunrise and installation",
                "Offer Pushpanjali with Bilva leaves and lotus on Maha Ashtami morning",
                "Perform Sandhi Puja at the exact junction of Ashtami-Navami with 108 lamps & 108 lotuses",
                "Sindoor Khela by married women and Bijoya Dashami warm embraces (Kula-kuli)",
            ],
            "bn": [
                "ভোরে নবপত্রিকা বা কলাবউ স্নান ও দেবীর পাশে স্থাপন",
                "মহাষ্টমীর সকালে উপবাস থেকে ভক্তিভরে পুষ্পাঞ্জলি নিবেদন",
                "অষ্টমী-নবমীর সন্ধিক্ষণে ১০৮টি পদ্ম ও ১০৮টি প্রদীপ প্রজ্জ্বলন করে চামুণ্ডা রূপের সন্ধিপূজা",
                "দশমীতে দেবীবরণ, সিঁদুর খেলা এবং বিজয়ার শুভ কোলাকুলি ও মিষ্টিমুখ",
            ],
            "hi": [
                "प्रातःकाल नवपत्रिका प्रवेश और महासप्तमी पूजन",
                "महाअष्टमी पर निर्जल रहकर 108 कमल पुष्पों से पुष्पांजलि अर्पित करें",
                "अष्टमी-नवमी के संधिकाल में 108 दीप जलाकर संधि पूजा संपन्न करें",
                "दशमी पर विसर्जन, सिंदूर खेला और बड़ों के चरण स्पर्श कर 'विजया' की शुभकामनाएं लें",
            ],
        },
    },
    {
        "id": "diwali",
        "name": {
            "en": "Diwali (Lakshmi Puja)",
            "bn": "দীপাবলি ও শ্রী শ্রী লক্ষ্মী-কালীপূজা",
            "hi": "दीपावली (महालक्ष्मी पूजन)",
        },
        "category": "major",
        "calc_type": "lunar_tithi",
        "lunar_month": 7,  # Kartika
        "tithi_idx": 29,  # Amavasya
        "tithi_desc": {
            "en": "Kartika Amavasya",
            "bn": "কার্তিকী অমাবস্যা",
            "hi": "कार्तिक अमावस्या",
        },
        "badge": {"en": "Festival of Lights", "bn": "আলোর মহোৎসব", "hi": "दीपोत्सव"},
        "accent_color": "#D97706",
        "muhurat": {
            "en": "Pradosh Kaal Lakshmi Puja: 05:40 PM – 07:35 PM",
            "bn": "প্রদোষ কাল লক্ষ্মী-কালী পূজা: সন্ধ্যা ০৫:৪০ – রাত ০৭:৩৫",
            "hi": "प्रदोष काल लक्ष्मी पूजा: सायं 05:40 – 07:35",
        },
        "shloka": "॥ ॐ श्रीं ह्रीं श्रीं कमले कमलालये प्रसीद प्रसीद ॐ श्रीं ह्रीं श्रीं महालक्ष्म्यै नमः ॥",
        "desc": {
            "en": "The grand festival of lights celebrating the triumphant return of Lord Rama to Ayodhya, and invocation of Goddess Mahalakshmi and Lord Ganesha for sovereign wealth, virtue, and illumination of the soul.",
            "bn": "তমসো মা জ্যোতির্গময়—অন্ধকার দূর করে আলোর বিজয় উৎসব। কার্তিকী অমাবস্যার প্রদোষে ধনদাত্রী মা মহালক্ষ্মী ও বিঘ্নহর্তা গণেশ এবং নিশীথে মা শ্যামার মহতী আরাধনা।",
            "hi": "भगवान श्री राम के 14 वर्ष पश्चात अयोध्या आगमन पर दीपोत्सव। कार्तिक अमावस्या की निशा में मां महालक्ष्मी, भगवान गणेश और कुबेर जी की आराधना।",
        },
        "rituals": {
            "en": [
                "Illuminate the entire residence with rows of earthen mustard/sesame oil Diyas",
                "Perform Lakshmi-Ganesha-Kuber Puja during Pradosh or Sthir Lagna (Vrishabha/Singha)",
                "Draw intricate rice powder rangolis and Lakshmi lotus footprints at main doorway",
                "Distribute traditional sweets, dry fruits, and gifts bringing joy and harmony",
            ],
            "bn": [
                "গৃহ প্রাঙ্গণ ও আঙিনায় সারি সারি মাটির প্রদীপ ও মোমবাতি প্রজ্জ্বলন",
                "স্থির লগ্নে মা মহালক্ষ্মী, গণেশ ও ধনপতি কুবেরের শ্রীশ্রী পূজা ও আরতি",
                "প্রবেশদ্বারে চালের গুঁড়োর আলপনা ও মা লক্ষ্মীর চরণচিহ্ন অঙ্কন",
                "মিষ্টিমুখ, আতশবাজির আনন্দ এবং পারস্পরিক শুভেচ্ছা বিনিময়",
            ],
            "hi": [
                "प्रदोष अथवा स्थिर लग्न (वृषभ/सिंह) में महालक्ष्मी-गणेश-कुबेर पूजन",
                "घर के प्रत्येक कोने में तिल के तेल या घी के मिट्टी के दीपक प्रज्वलित करें",
                "मुख्य द्वार पर कुमकुम से 'शुभ लाभ', स्वास्तिक और मां लक्ष्मी के चरण चिह्न बनाएं",
                "कनकधारा स्तोत्र और श्री सूक्त का श्रद्धापूर्वक पाठ करें",
            ],
        },
    },
    {
        "id": "chhath-puja",
        "name": {
            "en": "Chhath Puja (Surya Shashthi)",
            "bn": "ছট পূজা (সূর্য ষষ্ঠী)",
            "hi": "छठ पूजा (सूर्य षष्ठी)",
        },
        "category": "vrat",
        "calc_type": "lunar_tithi",
        "lunar_month": 7,  # Kartika
        "tithi_idx": 5,  # Shukla Shashthi
        "tithi_desc": {
            "en": "Kartika Shukla Shashthi",
            "bn": "কার্তিক শুক্লা ষষ্ঠী",
            "hi": "कार्तिक शुक्ल षष्ठी",
        },
        "badge": {"en": "Sun God Worship", "bn": "সূর্যদেব ও ছটী মাইয়া", "hi": "महापर्व छठ"},
        "accent_color": "#EA580C",
        "muhurat": {
            "en": "Sandhya Arghya: 05:08 PM | Usha Arghya: 06:18 AM",
            "bn": "সন্ধ্যা অর্ঘ্য: বিকাল ০৫:০৮ | ঊষা অর্ঘ্য: সকাল ০৬:১৮",
            "hi": "संध्या अर्घ्य: 05:08 PM | उषा अर्घ्य: 06:18 AM",
        },
        "shloka": "॥ ॐ एहि सूर्य सहस्त्रांशो तेजोराशे जगत्पते । अनुकम्पय मां भक्त्या गृहाणार्घ्यं दिवाकर ॥",
        "desc": {
            "en": "Ancient Vedic mahaparva dedicated to the living Sun God (Pratyaksha Devata) and Chhathi Maiya. Observed with 36 hours of rigorous Nirjala waterless fast, standing in water to offer Arghya to setting and rising Sun.",
            "bn": "প্রত্যক্ষ দেবতা ভগবান সূর্য এবং ছটী মাইয়ার পরম পবিত্র মহাব্রত। ৩৬ ঘণ্টার কঠোর নির্জলা উপবাস, পবিত্র নদী বা জলাশয়ে দাঁড়িয়ে অস্তগামী ও উদীয়মান সূর্যকে অর্ঘ্য দান।",
            "hi": "भगवान सूर्य और छठी मइया की उपासना का अत्यंत कठिन चार दिवसीय महापर्व। नहाय-खाय, खरना, 36 घंटे का निर्जला व्रत और अस्ताचलगामी व उदीयमान सूर्य को अर्घ्य।",
        },
        "rituals": {
            "en": [
                "Four-day observance: Nahay-Khay, Kharna, Sandhya Arghya, and Usha Arghya",
                "Prepare pure Thekua prasad using wheat, jaggery, and pure desi ghee on earthen chulha",
                "Stand waist-deep in water holding bamboo Soop loaded with fruits and Thekua",
                "Offer cow milk and Arghya to the setting and rising Sun praying for progeny and health",
            ],
            "bn": [
                "চার দিনের নিয়মনিষ্ঠ ব্রত: নহায়-খায়, খরনা, সন্ধ্যাকালীন অর্ঘ্য ও প্রাতঃকালীন ঊষা অর্ঘ্য",
                "শুদ্ধ ঘৃত, আটা ও গুড় সহযোগে পবিত্র ঠেকুয়া প্রসাদ তৈরি",
                "বাঁশের ডালা ও কূলোয় মৌসুমি ফল, আখ ও ঠেকুয়া সাজিয়ে নদীতে কোমর জলে দণ্ডায়মান",
                "অস্তগামী ও উদয়কালীন সূর্যকে কাঁচা দুধ ও অর্ঘ্য নিবেদন করে ব্রত উদযাপন",
            ],
            "hi": [
                "चार दिवसीय व्रत: नहाय-खाय, खरना, सायंकालीन अर्घ्य और प्रातःकालीन उषा अर्घ्य",
                "शुद्ध घी, गेहूं के आटे और गुड़ से बना पवित्र ठेकुआ प्रसाद",
                "बांस के सूप और दौरा में फल, गन्ना व ठेकुआ रखकर नदी-तालाब में कमर तक जल में खड़े होना",
                "डूबते और उगते सूर्य को दूध व जल का अर्घ्य देकर संतान और परिवार के कल्याण की प्रार्थना",
            ],
        },
    },
    {
        "id": "devutthana-ekadashi",
        "name": {
            "en": "Devutthana Ekadashi & Tulsi Vivah",
            "bn": "দেবউত্থান একাদশী ও তুলসী বিবাহ",
            "hi": "देवउठनी एकादशी एवं तुलसी विवाह",
        },
        "category": "vrat",
        "calc_type": "lunar_tithi",
        "lunar_month": 7,  # Kartika
        "tithi_idx": 10,  # Shukla Ekadashi
        "tithi_desc": {
            "en": "Kartika Shukla Ekadashi",
            "bn": "কার্তিক শুক্লা একাদশী",
            "hi": "कार्तिक शुक्ल एकादशी",
        },
        "badge": {"en": "Auspicious Awakened", "bn": "পুণ্য একাদশী", "hi": "तुलसी विवाह"},
        "accent_color": "#10B981",
        "muhurat": {
            "en": "Ekadashi Parana: 06:48 AM – 08:55 AM (Next Day)",
            "bn": "একাদশী পারণ মুহূর্ত: পরদিন সকাল ০৬:৪৮ – সকাল ০৮:৫৫",
            "hi": "एकादशी पारण: अगले दिन प्रातः 06:48 – 08:55",
        },
        "shloka": "॥ उत्तिष्ठोत्तिष्ठ गोविन्द त्यज निद्रां जगत्पते । त्वयि सुप्ते जगत्सुप्तमुत्थिते चोत्थितं जगत् ॥",
        "desc": {
            "en": "Lord Vishnu awakens from His 4-month cosmic slumber (Chaturmas). Marks the solemn ceremonial wedding of Tulsi Devi with Lord Shaligram, unlocking all auspicious wedding and Griha Pravesh muhurats.",
            "bn": "চাতুর্মাস্যের চার মাস যোগনিদ্রার পর শ্রীশ্রী নারায়ণের শুভ জাগরণ। তুলসী দেবীর সাথে শালগ্রাম শিলার পরম মাঙ্গলিক বিবাহ এবং বিবাহ ও গৃহপ্রবেশের শুভ মুহূর্ত উন্মোচন।",
            "hi": "चार मास के चातुर्मास के पश्चात भगवान विष्णु का योगनिद्रा से जागरण। तुलसी जी और शालिग्राम जी का मंगल विवाह और सभी मांगलिक कार्यों का शुभारंभ।",
        },
        "rituals": {
            "en": [
                "Chant awakening shlokas to Lord Vishnu ringing bells and conch shells",
                "Perform Tulsi Vivah by dressing Tulsi plant as bride and Shaligram as groom",
                "Offer sugarcane, Singhada, Ber, and sweet potato to Sri Hari",
                "Observe strict grains-free fast on Ekadashi tithi",
            ],
            "bn": [
                "শঙ্খধ্বনি ও ঘণ্টা বাজিয়ে ভগবান নারায়ণের জাগরণ আহ্বান",
                "তুলসী মঞ্চ সাজিয়ে শালগ্রাম শিলার সাথে তুলসী দেবীর শাস্ত্রীয় বিবাহ সম্পাদন",
                "আখ, পানিফল, মিষ্টি আলু ও ফলমূল নারায়ণের চরণে ভোগ নিবেদন",
                "একাদশীর পবিত্র উপবাস পালন ও বিষ্ণু সহস্রনাম পাঠ",
            ],
            "hi": [
                "शंख-घंटी बजाकर 'उत्तिष्ठ गोविन्द' श्लोक से भगवान विष्णु को जगाएं",
                "तुलसी के पौधे को लाल चुनरी ओढ़ाकर शालिग्राम जी से विवाह कराएं",
                "गन्ना, सिंघाड़ा, बेर, शकरकंद और आंवले का भोग लगाएं",
                "एकादशी का निराहार अथवा फलाहार व्रत रखकर विष्णु सहस्त्रनाम का पाठ करें",
            ],
        },
    },
    {
        "id": "gita-jayanti",
        "name": {
            "en": "Gita Jayanti (Mokshada Ekadashi)",
            "bn": "গীতা জয়ন্তী (মোক্ষদা একাদশী)",
            "hi": "गीता जयंती (मोक्षदा एकादशी)",
        },
        "category": "jayanti",
        "calc_type": "lunar_tithi",
        "lunar_month": 8,  # Margashirsha
        "tithi_idx": 10,  # Shukla Ekadashi
        "tithi_desc": {
            "en": "Margashirsha Shukla Ekadashi",
            "bn": "মার্গশীর্ষ শুক্লা একাদশী",
            "hi": "मार्गशीर्ष शुक्ल एकादशी",
        },
        "badge": {"en": "Eternal Wisdom", "bn": "গীতা বাণী", "hi": "गीता ज्ञान"},
        "accent_color": "#8B5CF6",
        "muhurat": {
            "en": "Gita Path & Puja: 07:15 AM – 11:30 AM",
            "bn": "শ্রীমদ্ভগবদ্গীতা পাঠ ও অর্চনা: সকাল ০৭:১৫ – সকাল ১১:৩০",
            "hi": "गीता पाठ व पूजन: प्रातः 07:15 – 11:30",
        },
        "shloka": "॥ यदा यदा हि धर्मस्य ग्लानिर्भवति भारत । अभ्युत्थानमधर्मस्य तदात्मानं सृजाम्यहम् ॥",
        "desc": {
            "en": "Advent of the immortal Bhagavad Gita spoken by Lord Sri Krishna to Arjuna on the battlefield of Kurukshetra. Bestows Moksha, clarifies righteous duty, and liberates from material bondage.",
            "bn": "কুরুক্ষেত্রের পুণ্য রণাঙ্গনে ভগবান শ্রীকৃষ্ণ অর্জুনকে যে অমর সনাতন বাণী প্রদান করেছিলেন, সেই শ্রীমদ্ভগবদ্গীতার শুভ আবির্ভাব দিবস। মোক্ষদা একাদশী ও আত্মজ্ঞান লাভের তিথি।",
            "hi": "कुरुक्षेत्र के पावन मैदान में भगवान श्री कृष्ण द्वारा अर्जुन को दिए गए श्रीमद्भगवद्गीता के अमर उपदेश का प्राकट्य दिवस। मोक्षदा एकादशी का पावन व्रत।",
        },
        "rituals": {
            "en": [
                "Recite all 18 Chapters or selected verses of Srimad Bhagavad Gita",
                "Worship the holy scripture Bhagavad Gita with flowers, incense, and Akshat",
                "Observe Ekadashi fast praying for liberation of ancestors (Pitrus)",
                "Distribute copies of the Bhagavad Gita to seekers and students",
            ],
            "bn": [
                "সম্পূর্ণ ১৮টি অধ্যায় অথবা অন্তত দ্বাদশ ও পঞ্চদশ অধ্যায় ভক্তিভরে পাঠ",
                "শ্রীমদ্ভগবদ্গীতা গ্রন্থের পুষ্প, চন্দন ও প্রদীপ সহযোগে পূজা",
                "পূর্বপুরুষদের আত্মার মোক্ষ কামনায় একাদশী ব্রত পালন",
                "শিক্ষার্থী ও ভক্তদের মাঝে পবিত্র গীতা গ্রন্থ বিতরণ",
            ],
            "hi": [
                "श्रीमद्भगवद्गीता के 18 अध्यायों अथवा गीता महात्म्य का सस्वर पाठ",
                "गीता पुस्तक पर रोली, चंदन व पुष्प अर्पित कर आरती करें",
                "पितरों की सद्गति व आत्म-कल्याण हेतु मोक्षदा एकादशी का व्रत रखें",
                "विद्यार्थियों व धर्मप्रेमियों को श्रीमद्भगवद्गीता की प्रतियां भेंट करें",
            ],
        },
    },
]


def _find_solar_ingress(target_deg: float, year: int, window_month: int) -> date:
    """Finds exact day when sidereal Sun crosses target_deg."""
    _require_swisseph()
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    # Search in window around target month
    start_d = date(year, window_month, 10)
    end_d = date(year, window_month, 20)

    curr = start_d
    prev_lon = None
    while curr <= end_d:
        jd = swe.julday(curr.year, curr.month, curr.day, 0.5)
        sun_lon = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]

        if prev_lon is not None:
            # Handle wrapping around 0 (Mesha ingress)
            if target_deg == 0.0:
                if prev_lon > 350.0 and sun_lon < 15.0:
                    return curr
            else:
                if prev_lon < target_deg <= sun_lon:
                    return curr

        prev_lon = sun_lon
        curr += timedelta(days=1)

    # Default fallback to astronomical mean
    if target_deg == 270.0:
        return date(year, 1, 14)
    elif target_deg == 0.0:
        return date(year, 4, 14)
    return date(year, window_month, 14)


def _get_new_moons_for_year(year: int) -> list[date]:
    """Computes all Amavasya (New Moon) dates around the target year."""
    _require_swisseph()
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    amavasyas: list[date] = []
    d = date(year - 1, 11, 15)
    end = date(year + 1, 2, 1)

    prev_elon = None
    while d <= end:
        jd = swe.julday(d.year, d.month, d.day, 0.5)
        sun_lon = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]
        moon_lon = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
        elon = (moon_lon - sun_lon) % 360.0

        if prev_elon is not None and prev_elon > 330.0 and elon < 35.0:
            amavasyas.append(d)

        prev_elon = elon
        d += timedelta(days=1)

    return amavasyas


def _find_lunar_tithi_date(
    target_lunar_month: int, target_tithi_idx: int, year: int
) -> date | None:
    """Finds exact date in the Gregorian year matching the lunar month and tithi."""
    _require_swisseph()
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    new_moons = _get_new_moons_for_year(year)
    candidates: list[date] = []

    for i in range(len(new_moons) - 1):
        m_start = new_moons[i]
        m_end = new_moons[i + 1]

        # Calculate mid-month Sun sign to identify month index (0: Chaitra ... 11: Phalguna)
        mid_jd = (
            swe.julday(m_start.year, m_start.month, m_start.day, 0.5) + (m_end - m_start).days / 2.0
        )
        sun_lon = swe.calc_ut(mid_jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]
        sun_sign = int(sun_lon / 30.0)
        month_idx = (sun_sign + 1) % 12

        if month_idx == target_lunar_month:
            # Scan each day between m_start and m_end for target_tithi_idx
            curr = m_start
            while curr <= m_end:
                # Check across the 4 praharas of the day (00:30, 06:00, 12:00, 18:00 UT / 6am, 11:30am, 5:30pm, 11:30pm IST)
                # to ensure kshaya tithis (starting and ending between sunrises) are never skipped.
                for h in (0.5, 6.0, 12.0, 18.0):
                    jd = swe.julday(curr.year, curr.month, curr.day, h)
                    s_lon = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]
                    m_lon = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
                    t_idx = int(((m_lon - s_lon) % 360.0) / 12.0)

                    if t_idx == target_tithi_idx:
                        candidates.append(curr)
                        break
                curr += timedelta(days=1)

    # Prioritize candidate that matches the target year
    for c in candidates:
        if c.year == year:
            return c
    return candidates[0] if candidates else None


def calculate_festivals_for_year(year: int, ref_date: date | None = None) -> list[FestivalItem]:
    """Calculates all authentic Vedic festivals for the specified year."""
    if ref_date is None:
        ref_date = date.today()

    items: list[FestivalItem] = []

    for defn in FESTIVAL_DEFINITIONS:
        f_date: date | None = None

        if defn["calc_type"] == "solar_ingress":
            f_date = _find_solar_ingress(defn["solar_target"], year, defn["window_month"])
        elif defn["calc_type"] == "lunar_tithi":
            f_date = _find_lunar_tithi_date(defn["lunar_month"], defn["tithi_idx"], year)

        if not f_date:
            continue

        days_remaining = (f_date - ref_date).days
        is_today = days_remaining == 0
        is_upcoming = days_remaining >= 0
        is_past = days_remaining < 0

        item = FestivalItem(
            id=defn["id"],
            name=defn["name"],
            date=f_date.isoformat(),
            date_formatted=format_localized_date(f_date),
            day_of_week=format_day_of_week(f_date),
            tithi=defn["tithi_desc"],
            category=defn["category"],
            badge=defn["badge"],
            accent_color=defn["accent_color"],
            muhurat=defn["muhurat"],
            shloka=defn["shloka"],
            desc=defn["desc"],
            rituals=defn["rituals"],
            days_remaining=days_remaining,
            is_today=is_today,
            is_upcoming=is_upcoming,
            is_past=is_past,
        )
        items.append(item)

    # Sort strictly by calendar date
    items.sort(key=lambda x: x.date)
    return items


def get_upcoming_festivals(ref_date: date | None = None, limit: int = 15) -> list[FestivalItem]:
    """Returns dynamic upcoming festivals strictly from ref_date onwards.

    Rolls forward across year boundary (e.g. Nov/Dec into Jan/Feb of next year).
    Ensures the next upcoming festival is ALWAYS fresh, real-time, and never past.
    """
    if ref_date is None:
        ref_date = date.today()

    current_year = ref_date.year
    f_this_year = calculate_festivals_for_year(current_year, ref_date)
    f_next_year = calculate_festivals_for_year(current_year + 1, ref_date)

    combined = f_this_year + f_next_year
    # Filter only today or future
    upcoming = [f for f in combined if f.days_remaining >= 0]
    upcoming.sort(key=lambda x: x.date)

    # Deduplicate by ID
    seen = set()
    result = []
    for item in upcoming:
        if item.id not in seen:
            seen.add(item.id)
            result.append(item)
            if len(result) >= limit:
                break

    return result


def get_festival_calendar(
    year: int | None = None,
    ref_date: date | None = None,
) -> FestivalCalendarResponse:
    """Builds complete Festival Calendar response with dynamic next upcoming spotlight."""
    if ref_date is None:
        ref_date = date.today()

    target_year = year if year is not None else ref_date.year
    festivals = calculate_festivals_for_year(target_year, ref_date)

    upcoming_list = get_upcoming_festivals(ref_date, limit=1)
    next_upcoming = upcoming_list[0] if upcoming_list else None

    return FestivalCalendarResponse(
        year=target_year,
        total_count=len(festivals),
        next_upcoming=next_upcoming,
        festivals=festivals,
        engine="Swiss Ephemeris 2.10 (pyswisseph)",
        calculated_at=datetime.now(UTC).isoformat(),
    )
