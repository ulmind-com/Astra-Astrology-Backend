"""Vedic & Chaldean Numerology Engine based entirely on Client's Resource Documents.

Implements:
- Mulank (Driver/Birth Number 1-9) with complete 20-field profile from `new-numro.txt`
- Bhagyank (Conductor/Destiny Number 1-9) with life path purpose
- Chaldean Name Number with letter-by-letter sound vibration & bedroom vastu
- Mobile Number Compatibility, Compound vibrations (10-60), and digit pair analysis
- Vedic 3x3 Grid (3-1-9, 6-7-5, 2-8-4), Planes, Columns, and Missing Number remedies
"""

import re
from typing import Any

# Chaldean Letter to Number Values (1 to 8; 9 is sacred/unassigned)
CHALDEAN_MAP = {
    "A": 1, "I": 1, "J": 1, "Q": 1, "Y": 1,
    "B": 2, "K": 2, "R": 2,
    "C": 3, "G": 3, "L": 3, "S": 3,
    "D": 4, "M": 4, "T": 4,
    "E": 5, "H": 5, "N": 5, "X": 5,
    "U": 6, "V": 6, "W": 6,
    "O": 7, "Z": 7,
    "F": 8, "P": 8,
}

# Mulank Core Master Data from `new-numro.txt`
MULANK_MASTER: dict[int, dict[str, Any]] = {
    1: {
        "planet": "Sun (সূর্য)",
        "planet_hi": "सूर्य",
        "deity": "Surya Dev (সূর্য দেব)",
        "metal": "Gold, Copper (স্বর্ণ, তামা)",
        "colors": ["Brown", "Yellow", "Red", "Golden"],
        "unlucky_colors": ["Black (কালো)"],
        "direction": "East (পূর্ব)",
        "lucky_numbers": [1, 2, 3, 4, 5, 7, 9],
        "unlucky_numbers": [6, 8],
        "beej_mantra": "ॐ ह्रां ह्रीं ह्रौं सः सूर्याय नमः",
        "jap_count": 6000,
        "gemstone": "Ruby (চুনি / মানিক্য)",
        "lucky_days": ["Sunday", "Thursday", "Monday"],
        "lucky_months": ["January", "March", "May", "July", "October"],
        "grains_daan": "গম, লাল বস্ত্র, লাল ফুল এবং চন্দন",
        "health_traits": "রক্তচাপ, হৃৎপিণ্ড, চক্ষু এবং মেরুদণ্ড সংক্রান্ত বিষয়ে সতর্কতা প্রয়োজন।",
        "profession": "প্রশাসনিক সেবা, ম্যানেজমেন্ট, কম্পিউটার ও প্রযুক্তি, প্রকাশনা ও নেতৃত্বমূলক ক্ষেত্র।",
    },
    2: {
        "planet": "Moon (চন্দ্র)",
        "planet_hi": "चंद्रमा",
        "deity": "Lord Shiva (ভগবান শিব)",
        "metal": "Silver (রৌপ্য)",
        "colors": ["White", "Cream", "Light Green"],
        "unlucky_colors": ["Black", "Dark Blue"],
        "direction": "North-West (বায়ব্য কোণ)",
        "lucky_numbers": [1, 2, 3, 5],
        "unlucky_numbers": [8, 9],
        "beej_mantra": "ॐ श्रां श्रीं श्रौं सः चंद्राय नमः",
        "jap_count": 11000,
        "gemstone": "Pearl (মুক্তা)",
        "lucky_days": ["Monday", "Sunday", "Friday"],
        "lucky_months": ["February", "April", "June", "November"],
        "grains_daan": "দুধ, চাল, রূপা, সাদা বস্ত্র এবং কর্পূর",
        "health_traits": "মানসিক অস্থিরতা, অনিদ্রা, জলীয় সমস্যা এবং পেটের সংবেদনশীলতা।",
        "profession": "শিল্প, সাহিত্য, সঙ্গীত, ভ্রমণ, শিক্ষকতা, জল বা তরল ভিত্তিক ব্যবসা ও কাউন্সেলিং।",
    },
    3: {
        "planet": "Jupiter (বৃহস্পতি / দেবগুরু)",
        "planet_hi": "बृहस्पति / गुरु",
        "deity": "Lord Vishnu / Brahma (ভগবান বিষ্ণু)",
        "metal": "Gold, Brass (স্বর্ণ, পিতল)",
        "colors": ["Yellow", "Golden", "Orange"],
        "unlucky_colors": ["Dark Green", "Black"],
        "direction": "North-East (ঈশান কোণ)",
        "lucky_numbers": [1, 2, 3, 5, 7, 9],
        "unlucky_numbers": [6],
        "beej_mantra": "ॐ ग्रां ग्रीं ग्रौं सः गुरवे नमः",
        "jap_count": 19000,
        "gemstone": "Yellow Sapphire (পোখরাজ)",
        "lucky_days": ["Thursday", "Tuesday", "Sunday"],
        "lucky_months": ["March", "June", "September", "December"],
        "grains_daan": "ছোলার ডাল, হলুদ বস্ত্র, হলুদ ফুল, কলা ও বেসন",
        "health_traits": "যকৃৎ (লিভার), চর্বি বৃদ্ধি, স্থূলতা এবং ডায়াবেটিস সংক্রান্ত যত্ন প্রয়োজন।",
        "profession": "আইন, পরামর্শদাতা, শিক্ষকতা, ব্যাংকিং, ধর্মীয় ও দার্শনিক গবেষণা, উচ্চপদস্থ কর্মকর্তা।",
    },
    4: {
        "planet": "Rahu (রাহু)",
        "planet_hi": "राहु",
        "deity": "Lord Bhairav / Saraswati (মা সরস্বতী / কালভৈরব)",
        "metal": "Alloy, Lead (মিশ্র ধাতু, সিসা)",
        "colors": ["Blue", "Grey", "Khaki"],
        "unlucky_colors": ["Black"],
        "direction": "South-West (নৈঋত কোণ)",
        "lucky_numbers": [1, 2, 5, 6, 7],
        "unlucky_numbers": [4, 8, 9],
        "beej_mantra": "ॐ भ्रां भ्रीं भ्रौं सः राहवे नमः",
        "jap_count": 18000,
        "gemstone": "Hessonite (গোমেদ)",
        "lucky_days": ["Saturday", "Wednesday", "Monday"],
        "lucky_months": ["April", "July", "October"],
        "grains_daan": "কালো তিল, সাত ধান্য, সিসা, কম্বল ও সরিষার তেল",
        "health_traits": "হঠাৎ রোগব্যাধি, স্নায়ুতন্ত্রের সমস্যা, উদ্বেগ ও রক্তাল্পতা।",
        "profession": "আইটি, সফটওয়্যার, গবেষণা, জ্যোতিষ, গুপ্তবিদ্যা, রাজনীতি, শেয়ার বাজার ও মিডিয়া।",
    },
    5: {
        "planet": "Mercury (বুধ)",
        "planet_hi": "बुध",
        "deity": "Lord Ganesha (ভগবান গণেশ)",
        "metal": "Bronze, Brass (কাংস্য, পিতল)",
        "colors": ["Green", "Emerald", "Turquoise"],
        "unlucky_colors": ["Red"],
        "direction": "North (উত্তর দিক)",
        "lucky_numbers": [1, 5, 6, 9],
        "unlucky_numbers": [2],
        "beej_mantra": "ॐ ब्रां ब्रीं ब्रौं सः बुधाय नमः",
        "jap_count": 9000,
        "gemstone": "Emerald (পান্না)",
        "lucky_days": ["Wednesday", "Friday", "Thursday"],
        "lucky_months": ["May", "June", "September"],
        "grains_daan": "মুগ ডাল, সবুজ বস্ত্র, সবুজ শাকসবজি ও কাঁসা",
        "health_traits": "চর্মরোগ, স্নায়বিক দুর্বলতা, এলার্জি এবং শ্বাসকষ্ট।",
        "profession": "বাণিজ্য, বিপণন, যোগাযোগ, ব্যাংকিং, চার্টার্ড অ্যাকাউন্ট্যান্ট, সাংবাদিকতা ও ব্যবসা।",
    },
    6: {
        "planet": "Venus (শুক্র)",
        "planet_hi": "शुक्र",
        "deity": "Goddess Lakshmi (মা লক্ষ্মী)",
        "metal": "Silver, Platinum (রৌপ্য, প্ল্যাটিনাম)",
        "colors": ["White", "Pink", "Silver", "Light Blue"],
        "unlucky_colors": ["Yellow", "Orange"],
        "direction": "South-East (অগ্নি কোণ)",
        "lucky_numbers": [1, 5, 6, 9],
        "unlucky_numbers": [3],
        "beej_mantra": "ॐ द्रां द्रीं द्रौं सः शुक्राय नमः",
        "jap_count": 16000,
        "gemstone": "Diamond / White Zircon (হীরা / ওপাল / সাদা জারকন)",
        "lucky_days": ["Friday", "Wednesday"],
        "lucky_months": ["May", "June", "October"],
        "grains_daan": "সুগন্ধি, ঘি, সাদা চাল, চিনি, কর্পূর ও রেশমি বস্ত্র",
        "health_traits": "গলা, মূত্রনালী, হরমোন ভারসাম্য এবং সুগারের সমস্যা।",
        "profession": "ফ্যাশন, চলচ্চিত্র, অভিনয়, রূপচর্চা, রত্ন ব্যবসা, আর্ট ও ইন্টেরিয়র ডিজাইন।",
    },
    7: {
        "planet": "Ketu (কেতু)",
        "planet_hi": "केतु",
        "deity": "Lord Ganesha (ভগবান গণেশ)",
        "metal": "Iron, Alloy (লোহা, পঞ্চধাতু)",
        "colors": ["Smoke Grey", "Light Yellow", "White"],
        "unlucky_colors": ["Dark Red"],
        "direction": "North-East / Center",
        "lucky_numbers": [1, 2, 3, 5, 7],
        "unlucky_numbers": [8, 9],
        "beej_mantra": "ॐ स्रां स्रीं स्रौं सः केतवे नमः",
        "jap_count": 17000,
        "gemstone": "Cat's Eye (লহসুনিয়া / বৈদুর্য)",
        "lucky_days": ["Sunday", "Monday", "Wednesday"],
        "lucky_months": ["July", "August", "September"],
        "grains_daan": "কালো কম্বল, তিল, তিল তেল ও কুকুরকে খাদ্য প্রদান",
        "health_traits": "পেট ফাঁপা, ত্বকের এলার্জি, নিদ্রাহীনতা ও মানসিক বিভ্রান্তি।",
        "profession": "গবেষণা, আধ্যাত্মিক সাধনা, হিলিং, দর্শন, সফটওয়্যার আর্কিটেকচার ও গোয়েন্দা সংস্থা।",
    },
    8: {
        "planet": "Saturn (শনি / কর্মফলদাতা)",
        "planet_hi": "शनि",
        "deity": "Lord Shani / Lord Shiva (শনিদেব / মহাদেব)",
        "metal": "Iron (লোহা)",
        "colors": ["Dark Blue", "Black", "Dark Grey"],
        "unlucky_colors": ["Red", "Golden", "Bright Yellow"],
        "direction": "West (পশ্চিম দিক)",
        "lucky_numbers": [3, 5, 6, 7],
        "unlucky_numbers": [1, 2, 4, 8],
        "beej_mantra": "ॐ प्रां प्रीं प्रौं सः शनैश्चराय नमः",
        "jap_count": 23000,
        "gemstone": "Blue Sapphire (নীলা / এমিথিস্ট)",
        "lucky_days": ["Saturday", "Wednesday", "Friday"],
        "lucky_months": ["January", "August", "December"],
        "grains_daan": "কালো ছাতা, সরিষার তেল, কালো তিল, লোহার পাত্র ও জুতা দান",
        "health_traits": "বাত, জয়েন্টের ব্যথা, দাঁতের সমস্যা এবং দীর্ঘস্থায়ী রোগ।",
        "profession": "খনন, রিয়েল এস্টেট, আইন, ধাতু ও তেল শিল্প, ভারী যন্ত্রপাতি ও শ্রম ব্যবস্থাপনা।",
    },
    9: {
        "planet": "Mars (মঙ্গল / সেনাপতি)",
        "planet_hi": "मंगल",
        "deity": "Lord Hanuman / Kartikeya (হনুমানজি / কার্তিকেয়)",
        "metal": "Copper (তামা)",
        "colors": ["Red", "Coral", "Maroon", "Pink"],
        "unlucky_colors": ["Green"],
        "direction": "South (দক্ষিণ দিক)",
        "lucky_numbers": [1, 2, 3, 5, 9],
        "unlucky_numbers": [4, 7],
        "beej_mantra": "ॐ क्रां क्रीं क्रौं सः भौमाय नमः",
        "jap_count": 10000,
        "gemstone": "Red Coral (লাল প্রবাল / পলা)",
        "lucky_days": ["Tuesday", "Thursday", "Sunday"],
        "lucky_months": ["April", "September", "November"],
        "grains_daan": "মুসুর ডাল, লাল মিষ্টি, গুড়, তামা ও রক্তচন্দন",
        "health_traits": "রক্তাল্পতা, উচ্চ রক্তচাপ, ক্ষত বা আঘাত এবং পেপটিক আলসার।",
        "profession": "প্রতিরক্ষা, পুলিশ, ক্রীড়া, শল্যচিকিৎসক (সার্জন), প্রকৌশল ও রিয়েল এস্টেট।",
    },
}

# Mobile Number Friend / Neutral / Enemy Table (Client Revised Matrix)
MOBILE_FRIENDSHIP_TABLE: dict[int, dict[str, list[int]]] = {
    1: {"friends": [1, 2, 3, 5, 9], "neutrals": [4, 7], "enemies": [6, 8]},
    2: {"friends": [1, 2, 3, 5], "neutrals": [4, 7], "enemies": [6, 8, 9]},
    3: {"friends": [1, 2, 3, 5, 9], "neutrals": [7, 8], "enemies": [6]},
    4: {"friends": [1, 5, 6, 7], "neutrals": [2, 3], "enemies": [4, 8, 9]},
    5: {"friends": [1, 5, 6, 9], "neutrals": [3, 7, 8], "enemies": [2, 4]},
    6: {"friends": [1, 5, 6, 9], "neutrals": [4, 7, 8], "enemies": [3]},
    7: {"friends": [1, 2, 3, 5, 7], "neutrals": [4, 6], "enemies": [8, 9]},
    8: {"friends": [3, 5, 6, 7], "neutrals": [2], "enemies": [1, 4, 8, 9]},
    9: {"friends": [1, 2, 3, 5, 9], "neutrals": [8], "enemies": [4, 6, 7]},
}

# Compound Number Analysis (10 to 60) from Client's Guide
COMPOUND_VIBRATIONS: dict[int, dict[str, str]] = {
    10: {"category": "Auspicous", "title": "Wheel of Fortune", "verdict_bn": "সম্মান, খ্যাতি ও সমৃদ্ধির প্রতীক। কর্মে দ্রুত উত্থান দেয়।"},
    14: {"category": "Auspicious", "title": "Magnetic Communication", "verdict_bn": "ব্যবসা, যোগাযোগ ও বাণিজ্যে চমৎকার প্রবৃদ্ধি দান করে।"},
    15: {"category": "Highly Auspicious", "title": "Prosperity & Charm", "verdict_bn": "অর্থ আকর্ষণ ও সম্মোহনী আকর্ষণের জন্য অত্যন্ত শুভ।"},
    18: {"category": "Challenging", "title": "Conflict & Delay", "verdict_bn": "মতভেদ, মানসিক অস্থিরতা ও আর্থিক বিলম্বের যোগ সৃষ্টি করে।"},
    19: {"category": "Prince of Heaven", "title": "Success & Authority", "verdict_bn": "উচ্চ পদমর্যাদা, নেতৃত্ব ও সার্বিক বিজয়ের প্রতীক।"},
    23: {"category": "Royal Star of the Lion", "title": "Immense Wealth", "verdict_bn": "শীর্ষ ধনবান ও প্রভাবশালী ব্যক্তিদের সহযোগী নম্বর।"},
    24: {"category": "Auspicious", "title": "Harmony & Love", "verdict_bn": "সম্পর্ক রক্ষা, পারিবারিক শান্তি ও দীর্ঘস্থায়ী সাফল্যের নম্বর।"},
    28: {"category": "Challenging", "title": "Trust Issues", "verdict_bn": "বিশ্বাসভঙ্গ ও আর্থিক অস্থিরতার কারণ হতে পারে।"},
    32: {"category": "Auspicious", "title": "Wisdom & Power", "verdict_bn": "সামাজিক যোগাযোগ ও বুদ্ধিমত্তা দিয়ে সাফল্যের চূড়ায় পৌঁছায়।"},
    37: {"category": "Highly Auspicious", "title": "Crown of Good Luck", "verdict_bn": "অপ্রত্যাশিত ভাগ্যোদয়, বন্ধুত্ব ও বিপুল সমৃদ্ধি।"},
    41: {"category": "Auspicious", "title": "Executive Force", "verdict_bn": "উদ্যোক্তা ও স্বাধীন ব্যবসায়ীদের জন্য খুব শুভ।"},
    45: {"category": "Auspicious", "title": "Public Influence", "verdict_bn": "জনসংযোগ, মিডিয়া ও জনপ্রিয়তার যোগ সৃষ্টি করে।"},
}


def _reduce_to_single_digit(n: int) -> int:
    """Reduces an integer repeatedly until a single digit between 1 and 9 is obtained."""
    while n > 9:
        n = sum(int(d) for d in str(n))
    return n


def calculate_mulank(day: int) -> dict[str, Any]:
    """Calculates Mulank (Driver/Psychic Number) from birth day."""
    mulank_num = _reduce_to_single_digit(day)
    data = MULANK_MASTER.get(mulank_num, MULANK_MASTER[1])
    return {
        "number": mulank_num,
        "planet": data["planet"],
        "deity": data["deity"],
        "gemstone": data["gemstone"],
        "lucky_colors": data["colors"],
        "unlucky_colors": data["unlucky_colors"],
        "lucky_numbers": data["lucky_numbers"],
        "unlucky_numbers": data["unlucky_numbers"],
        "beej_mantra": data["beej_mantra"],
        "jap_count": data["jap_count"],
        "lucky_days": data["lucky_days"],
        "direction": data["direction"],
        "grains_daan": data["grains_daan"],
        "health_traits": data["health_traits"],
        "profession": data["profession"],
    }


def calculate_bhagyank(day: int, month: int, year: int) -> dict[str, Any]:
    """Calculates Bhagyank (Conductor/Destiny Number) from full birth date."""
    total = sum(int(d) for d in f"{day}{month}{year}")
    bhagyank_num = _reduce_to_single_digit(total)
    data = MULANK_MASTER.get(bhagyank_num, MULANK_MASTER[1])
    return {
        "number": bhagyank_num,
        "planet": data["planet"],
        "deity": data["deity"],
        "gemstone": data["gemstone"],
        "direction": data["direction"],
        "beej_mantra": data["beej_mantra"],
        "life_path_advice": f"আপনার জীবনের মূল লক্ষ্য পরিচালিত হয় {data['planet']} দ্বারা। {data['profession']}",
    }


def calculate_chaldean_name(full_name: str) -> dict[str, Any]:
    """Calculates Chaldean Name Number and first letter vibration."""
    clean_name = re.sub(r"[^A-Za-z]", "", full_name).upper()
    if not clean_name:
        return {"name_number": 1, "compound_total": 1, "first_letter": "A"}

    compound_total = sum(CHALDEAN_MAP.get(ch, 1) for ch in clean_name)
    name_num = _reduce_to_single_digit(compound_total)
    first_char = clean_name[0]

    return {
        "clean_name": clean_name,
        "compound_total": compound_total,
        "name_number": name_num,
        "first_letter": first_char,
        "first_letter_val": CHALDEAN_MAP.get(first_char, 1),
    }


def calculate_mobile_numerology(mobile_str: str, mulank: int, bhagyank: int) -> dict[str, Any]:
    """Evaluates 10-digit mobile number for compound vibration, pair beneficence, and compatibility."""
    digits = [int(ch) for ch in mobile_str if ch.isdigit()]
    if len(digits) < 10:
        digits = (digits + [1, 2, 3, 4, 5, 6, 7, 8, 9, 0])[:10]

    ten_digits = digits[-10:]
    compound_sum = sum(ten_digits)
    single_digit = _reduce_to_single_digit(compound_sum)

    # Pair detection
    pairs_found: list[str] = []
    digits_str = "".join(str(d) for d in ten_digits)
    benefic_pairs = ["15", "51", "19", "91", "37", "73", "24", "42"]
    malefic_pairs = ["18", "81", "14", "41", "28", "82", "36", "63", "48", "84"]

    found_benefic = [p for p in benefic_pairs if p in digits_str]
    found_malefic = [p for p in malefic_pairs if p in digits_str]

    # Check friendship with Mulank & Bhagyank
    m_info = MOBILE_FRIENDSHIP_TABLE.get(mulank, MOBILE_FRIENDSHIP_TABLE[1])
    b_info = MOBILE_FRIENDSHIP_TABLE.get(bhagyank, MOBILE_FRIENDSHIP_TABLE[1])

    is_friend_m = single_digit in m_info["friends"]
    is_enemy_m = single_digit in m_info["enemies"]
    is_friend_b = single_digit in b_info["friends"]
    is_enemy_b = single_digit in b_info["enemies"]

    status = "অত্যন্ত শুভ ও অনুকূল" if (is_friend_m and not is_enemy_b) else (
        "চ্যালেঞ্জিং বা প্রতিকূল" if (is_enemy_m or is_enemy_b) else "তটস্থ বা মিশ্র ফলদায়ী"
    )

    vib_info = COMPOUND_VIBRATIONS.get(
        compound_sum,
        {"category": "Standard", "title": "Planetary Vibration", "verdict_bn": f"যৌগিক সংখ্যা {compound_sum} এর একক শক্তি {single_digit} গ্রহের অধীন।"}
    )

    return {
        "mobile_number": "".join(str(d) for d in ten_digits),
        "compound_sum": compound_sum,
        "single_digit": single_digit,
        "compatibility_status": status,
        "is_friend_with_mulank": is_friend_m,
        "is_enemy_with_mulank": is_enemy_m,
        "is_friend_with_bhagyank": is_friend_b,
        "is_enemy_with_bhagyank": is_enemy_b,
        "benefic_pairs_present": found_benefic,
        "malefic_pairs_present": found_malefic,
        "compound_verdict": vib_info["verdict_bn"],
    }


def calculate_vedic_grid(day: int, month: int, year: int) -> dict[str, Any]:
    """Calculates Vedic Numerology Grid (3-1-9, 6-7-5, 2-8-4), planes, and missing numbers."""
    mulank = _reduce_to_single_digit(day)
    bhagyank = _reduce_to_single_digit(sum(int(d) for d in f"{day}{month}{year}"))

    all_digits_str = f"{day}{month}{year}{mulank}{bhagyank}"
    counts: dict[int, int] = {i: 0 for i in range(1, 10)}
    for ch in all_digits_str:
        if ch.isdigit() and int(ch) in counts:
            counts[int(ch)] += 1

    # Planes
    mental_plane = bool(counts[3] and counts[1] and counts[9])
    emotional_plane = bool(counts[6] and counts[7] and counts[5])
    practical_plane = bool(counts[2] and counts[8] and counts[4])

    thought_column = bool(counts[3] and counts[6] and counts[2])
    will_column = bool(counts[1] and counts[7] and counts[8])
    action_column = bool(counts[9] and counts[5] and counts[4])

    golden_raj_yoga = bool(counts[4] and counts[5] and counts[6])
    silver_raj_yoga = bool(counts[2] and counts[5] and counts[8])

    missing_nums = [i for i in range(1, 10) if counts[i] == 0]

    return {
        "grid_counts": counts,
        "mulank": mulank,
        "bhagyank": bhagyank,
        "planes": {
            "mental_plane_319": mental_plane,
            "emotional_plane_675": emotional_plane,
            "practical_plane_284": practical_plane,
            "thought_column_362": thought_column,
            "will_column_178": will_column,
            "action_column_954": action_column,
            "golden_raj_yoga_456": golden_raj_yoga,
            "silver_raj_yoga_258": silver_raj_yoga,
        },
        "missing_numbers": missing_nums,
        "summary_bn": f"বৈদিক গ্রিডে মূল শক্তি {mulank} (মূলাঙ্ক) ও {bhagyank} (ভাগ্যাঙ্ক)। "
        + ("মানসিক ও নেতৃত্ব রাজযোগ (৩-১-৯) সক্রিয়। " if mental_plane else "")
        + ("ব্যবহারিক ও ধন যোগ (২-৮-৪) সক্রিয়। " if practical_plane else "")
        + (f"অনুপস্থিত সংখ্যা {missing_nums} এর প্রতিকার হিসেবে সংশ্লিষ্ট দেবোদ্দেশ্যে জপ শুভ।" if missing_nums else "গ্রিড অত্যন্ত সুষম।"),
    }
