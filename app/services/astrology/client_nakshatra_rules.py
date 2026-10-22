"""Nakshatra rules recovered from the client's own resource documents.

PROVENANCE
----------
The client supplied three scanned books under `Resource Documents/Kundli/`. All
three arrived as page images with no text layer, so nothing in them was usable
until they were put through OCR (macOS Vision, 2x render, 850 pages, output in
`Resource Documents/_extracted/kundli-ocr/`). That recovered about 124,000 words.

  [P1]  Predicting Through Nakshatras - Part 1, Saptarishis Publications, 308 pp.
        Covers nakshatras 1-9, Ashwini to Ashlesha.
  [P2]  Nakshatra Based Predictive Techniques - Part 2, Saptarishis Publications,
        401 pp. Covers nakshatras 10-18, Magha to Jyeshtha.
  [KP]  Jyotish - Vedic Astrology Secret Revealed: Kaal Purusha, 141 pp.

Both nakshatra books carry an "Appendix 2 - Quick Reference" listing every
technique in the volume; that appendix is the source used here, cross-checked
against the body text. The per-nakshatra header blocks (lord, deity, symbol, pada
placement) were read from the chapter openers.

TWO LIMITS THE CLIENT NEEDS TO KNOW
-----------------------------------
1. Part 3 was never supplied. Nakshatras 19-27, Mula through Revati, therefore have
   NO client-sourced techniques at all - a third of the zodiac. See
   `MISSING_FROM_CLIENT_RESOURCES`.
2. These are commercial copyrighted books. Per the standing project decision -
   take the rule, never the wording - every technique below is restated in our own
   words. No sentence is reproduced from the source. `source` cites where each rule
   came from so the client's astrologer can check it against the book.

WHAT IS NOT IN THESE BOOKS
--------------------------
Gana, Yoni, Nadi, Varna, Vashya, Paya, Tarabala and the name syllables do not
appear in them. Those come from the classical Avakahada Chakra and are verified
separately against the client's own sample report - see `tests/test_astrology_nakshatra.py`.
"""

from __future__ import annotations

from typing import Any, Literal

Lang = Literal["en", "bn", "hi"]

NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

# --------------------------------------------------------------------------------------
# Chapter-opener reference blocks, transcribed from [P1] and [P2].
# Only nakshatras 1-18 are present, because Part 3 was not supplied. These are kept
# so the canonical table in nakshatra_rules.py can be checked against the client's
# own books rather than against our word alone.
# --------------------------------------------------------------------------------------
BOOK_REFERENCE: dict[int, dict[str, Any]] = {
    0:  {"lord": "Ketu",    "deity": "Ashwini Kumaras", "symbol": "Horse's Head",            "padas": "4 padas in Aries",                 "source": "P1 ch.1"},
    1:  {"lord": "Venus",   "deity": "Yama",            "symbol": "Yoni",                    "padas": "4 padas in Aries",                 "source": "P1 ch.2"},
    2:  {"lord": "Sun",     "deity": "Agni",            "symbol": "Razor / Flame",           "padas": "1 pada in Aries, 3 in Taurus",     "source": "P1 ch.3"},
    3:  {"lord": "Moon",    "deity": "Brahma",          "symbol": "Cart",                    "padas": "4 padas in Taurus",                "source": "P1 ch.4"},
    4:  {"lord": "Mars",    "deity": "Soma",            "symbol": "Deer's Head",             "padas": "2 padas in Taurus, 2 in Gemini",   "source": "P1 ch.5"},
    5:  {"lord": "Rahu",    "deity": "Rudra",           "symbol": "Teardrop",                "padas": "4 padas in Gemini",                "source": "P1 ch.6"},
    6:  {"lord": "Jupiter", "deity": "Aditi",           "symbol": "Quiver of Arrows",        "padas": "3 padas in Gemini, 1 in Cancer",   "source": "P1 ch.7"},
    7:  {"lord": "Saturn",  "deity": "Brihaspati",      "symbol": "Cow's Udder",             "padas": "4 padas in Cancer",                "source": "P1 ch.8"},
    8:  {"lord": "Mercury", "deity": "Nagas",           "symbol": "Coiled Serpent",          "padas": "4 padas in Cancer",                "source": "P1 ch.9"},
    9:  {"lord": "Ketu",    "deity": "Pitris",          "symbol": "Royal Throne, Palanquin", "padas": "4 padas in Leo",                   "source": "P2 ch.1"},
    10: {"lord": "Venus",   "deity": "Bhaga",           "symbol": "Front legs of a cot",     "padas": "4 padas in Leo",                   "source": "P2 ch.2"},
    11: {"lord": "Sun",     "deity": "Aryaman",         "symbol": "Back legs of a cot",      "padas": "1 pada in Leo, 3 in Virgo",        "source": "P2 ch.3"},
    12: {"lord": "Moon",    "deity": "Savitr",          "symbol": "Open Hand",               "padas": "4 padas in Virgo",                 "source": "P2 ch.4"},
    13: {"lord": "Mars",    "deity": "Tvashtar",        "symbol": "Bright Jewel / Pearl",    "padas": "2 padas in Virgo, 2 in Libra",     "source": "P2 ch.5"},
    14: {"lord": "Rahu",    "deity": "Vayu",            "symbol": "Young shoot in the wind", "padas": "4 padas in Libra",                 "source": "P2 ch.6"},
    15: {"lord": "Jupiter", "deity": "Indra-Agni",      "symbol": "Triumphal Archway",       "padas": "3 padas in Libra, 1 in Scorpio",   "source": "P2 ch.7"},
    16: {"lord": "Saturn",  "deity": "Mitra",           "symbol": "Lotus Flower",            "padas": "4 padas in Scorpio",               "source": "P2 ch.8"},
    17: {"lord": "Mercury", "deity": "Indra",           "symbol": "Circular Amulet",         "padas": "4 padas in Scorpio",               "source": "P2 ch.9"},
}

MISSING_FROM_CLIENT_RESOURCES: dict[str, Any] = {
    "nakshatra_indices": list(range(18, 27)),
    "nakshatra_names": NAKSHATRA_NAMES[18:],
    "reason": (
        "Predicting Through Nakshatras Part 3, which covers Mula to Revati, was not "
        "among the files supplied. Parts 1 and 2 were. Until Part 3 arrives, no "
        "client-sourced technique can be shown for these nine nakshatras."
    ),
    "note": {
        "en": (
            "The predictive techniques shown here come from the two nakshatra volumes "
            "supplied for this project, which together cover Ashwini to Jyeshtha. The "
            "volume covering Mula to Revati has not been supplied, so no technique is "
            "available for this birth star yet."
        ),
        "bn": (
            "এখানে প্রদর্শিত ভবিষ্যদ্বাণীর কৌশলগুলি এই প্রকল্পের জন্য প্রদত্ত দুটি নক্ষত্র-গ্রন্থ "
            "থেকে নেওয়া, যেগুলি অশ্বিনী থেকে জ্যেষ্ঠা পর্যন্ত বিস্তৃত। মূলা থেকে রেবতী পর্যন্ত "
            "খণ্ডটি এখনও দেওয়া হয়নি, তাই এই নক্ষত্রের জন্য কোনো কৌশল এখনও উপলব্ধ নয়।"
        ),
        "hi": (
            "यहाँ दर्शाई गई भविष्यकथन तकनीकें इस परियोजना हेतु प्रदत्त दो नक्षत्र-ग्रंथों से ली गई "
            "हैं, जो अश्विनी से ज्येष्ठा तक को समाहित करते हैं। मूला से रेवती तक का खंड अभी "
            "उपलब्ध नहीं कराया गया, अतः इस नक्षत्र हेतु कोई तकनीक अभी उपलब्ध नहीं है।"
        ),
    },
}


# --------------------------------------------------------------------------------------
# Condition vocabulary
#
# Every technique carries a machine-evaluable `when` clause, so a rule is only shown
# when the chart actually satisfies it. The vocabulary is deliberately small and maps
# directly onto what the calculator already computes.
#
#   moon            the birth star itself - always true for the native's nakshatra
#   any_planet      one of the nine grahas occupies this nakshatra
#   key_planet      a focal planet occupies it. The books use "key" and "focal" for
#                   the Sun, the Moon, the lagna lord, or the lagna itself.
#   lagna           the ascendant degree falls in this nakshatra
#   planet          one of the named planets occupies it
#   house_lord      the lord of one of the named houses occupies it
#   afflicted       a malefic occupies it, a malefic aspects it, or its lord sits
#                   with a malefic
#   aspected        any planet casts a Vedic aspect onto it
#   in_houses       a planet in this nakshatra also sits in one of the named houses
#   always          the rule is about the nakshatra itself, not a placement
# --------------------------------------------------------------------------------------
NATURAL_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}

# Whole-sign rulerships, matching the client's 12 Rashis table.
SIGN_LORDS = [
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter",
]

# Special Vedic aspects, as houses counted forward from the planet's own position.
# Every graha aspects the 7th; these are the additional ones.
SPECIAL_ASPECTS = {
    "Mars": (4, 8),
    "Jupiter": (5, 9),
    "Saturn": (3, 10),
    "Rahu": (5, 9),
    "Ketu": (5, 9),
}


def _t(en: str, bn: str, hi: str) -> dict[str, str]:
    return {"en": en, "bn": bn, "hi": hi}


# --------------------------------------------------------------------------------------
# The techniques. Each entry:
#   nak        nakshatra index (0-based)
#   no         technique number as the book's appendix numbers it
#   when       condition clause, evaluated against the chart
#   theme      short label for grouping in the UI
#   rule       the rule restated in our own words, in three languages
#   source     book and technique number, so it can be checked against the original
# --------------------------------------------------------------------------------------
TECHNIQUES: list[dict[str, Any]] = [
    # ---- 1. Ashwini -------------------------------------------------------------
    {"nak": 0, "no": 1, "when": {"any_planet": True}, "theme": "travel",
     "rule": _t("A graha placed here, or a house lord placed here, tends to bring travel into the matters that graha or house governs.",
                "এখানে স্থিত গ্রহ, বা এখানে স্থিত কোনো ভাবাধিপতি, সেই গ্রহ বা ভাবের বিষয়ে ভ্রমণ যোগ করে।",
                "यहाँ स्थित ग्रह, अथवा यहाँ स्थित कोई भावाधिपति, उस ग्रह या भाव के विषयों में यात्रा जोड़ता है।"),
     "source": "P1 Ashwini, technique 1"},
    {"nak": 0, "no": 2, "when": {"aspected": True}, "theme": "lesson",
     "rule": _t("A graha casting an aspect here sets a lesson in self-improvement in the area that graha governs.",
                "এখানে দৃষ্টিপাতকারী গ্রহ সেই গ্রহের বিষয়ে আত্মোন্নতির একটি শিক্ষা নির্দেশ করে।",
                "यहाँ दृष्टि डालने वाला ग्रह उस ग्रह के विषय में आत्मोन्नति का एक पाठ निर्धारित करता है।"),
     "source": "P1 Ashwini, technique 2"},
    {"nak": 0, "no": 3, "when": {"afflicted": True}, "theme": "vehicles",
     "rule": _t("When this star is afflicted, caution with vehicles and road travel is advised.",
                "এই নক্ষত্র পীড়িত হলে যানবাহন ও সড়কপথে সতর্কতা বাঞ্ছনীয়।",
                "यह नक्षत्र पीड़ित होने पर वाहन एवं सड़क यात्रा में सावधानी वांछनीय है।"),
     "source": "P1 Ashwini, technique 3"},
    {"nak": 0, "no": 5, "when": {"afflicted": True}, "theme": "timing",
     "rule": _t("With this star afflicted, arriving on time is a recurring struggle however much effort is made.",
                "এই নক্ষত্র পীড়িত হলে যথাসময়ে পৌঁছানো বারবার কঠিন হয়, যত চেষ্টাই করা হোক।",
                "यह नक्षत्र पीड़ित होने पर समय पर पहुँचना बार-बार कठिन रहता है, चाहे कितना भी प्रयास हो।"),
     "source": "P1 Ashwini, technique 5"},
    {"nak": 0, "no": 6, "when": {"any_planet": True}, "theme": "mediation",
     "rule": _t("Whether this star is afflicted or well placed, the native tends to end up bringing people together or driving them apart.",
                "এই নক্ষত্র পীড়িত হোক বা সুস্থিত, জাতক প্রায়ই মানুষকে মেলানো বা বিচ্ছিন্ন করার ভূমিকায় পড়ে।",
                "यह नक्षत्र पीड़ित हो अथवा सुस्थित, जातक प्रायः लोगों को जोड़ने या अलग करने की भूमिका में आता है।"),
     "source": "P1 Ashwini, technique 6"},

    # ---- 2. Bharani -------------------------------------------------------------
    {"nak": 1, "no": 1, "when": {"any_planet": True}, "theme": "relatives",
     "rule": _t("The relative signified by a graha placed here is held to a stricter standard than others, and carries at least one reversal or betrayal.",
                "এখানে স্থিত গ্রহ দ্বারা নির্দেশিত আত্মীয় অন্যদের তুলনায় কঠোরতর বিচারের মুখে পড়ে, এবং অন্তত একটি বিপর্যয় বা প্রতারণা বহন করে।",
                "यहाँ स्थित ग्रह द्वारा दर्शाया गया संबंधी औरों की तुलना में कठोर मानदंड झेलता है, तथा कम से कम एक उलटफेर या विश्वासघात वहन करता है।"),
     "source": "P1 Bharani, technique 1"},
    {"nak": 1, "no": 2, "when": {"house_lord": list(range(1, 13))}, "theme": "secrets",
     "rule": _t("When a house lord sits here, the relative that house signifies keeps things to themselves, sometimes a private habit.",
                "কোনো ভাবাধিপতি এখানে থাকলে সেই ভাবের নির্দেশিত আত্মীয় গোপনীয়তা রক্ষা করে, কখনও কোনো ব্যক্তিগত অভ্যাস থাকে।",
                "कोई भावाधिपति यहाँ हो तो उस भाव का संबंधी बातें अपने तक रखता है, कभी कोई निजी आदत भी।"),
     "source": "P1 Bharani, technique 2"},
    {"nak": 1, "no": 3, "when": {"any_planet": True}, "theme": "body",
     "rule": _t("This star governs the lower foot and ankle; a graha placed here, especially when afflicted, can point to trouble there for the relative it signifies.",
                "এই নক্ষত্র পায়ের নিম্নাংশ ও গোড়ালি নিয়ন্ত্রণ করে; এখানে স্থিত গ্রহ, বিশেষত পীড়িত হলে, সেই আত্মীয়ের ওই অঞ্চলে সমস্যা নির্দেশ করতে পারে।",
                "यह नक्षत्र पाँव के निचले भाग एवं टखने का स्वामी है; यहाँ स्थित ग्रह, विशेषतः पीड़ित होने पर, उस संबंधी को वहाँ कष्ट दे सकता है।"),
     "source": "P1 Bharani, technique 3"},
    {"nak": 1, "no": 4, "when": {"planet": ["Mercury", "Rahu", "Moon", "Venus", "Mars"], "in_houses": [7, 8, 12]}, "theme": "relationships",
     "rule": _t("Mercury, Rahu, Moon, Venus or Mars placed here and tied to the 7th, 8th or 12th makes attachments intense but short-lived.",
                "বুধ, রাহু, চন্দ্র, শুক্র বা মঙ্গল এখানে থেকে সপ্তম, অষ্টম বা দ্বাদশ ভাবের সঙ্গে যুক্ত হলে সম্পর্ক তীব্র কিন্তু স্বল্পস্থায়ী হয়।",
                "बुध, राहु, चंद्र, शुक्र अथवा मंगल यहाँ होकर सप्तम, अष्टम या द्वादश भाव से जुड़ें तो संबंध तीव्र किंतु अल्पकालिक होते हैं।"),
     "source": "P1 Bharani, technique 4"},
    {"nak": 1, "no": 5, "when": {"any_planet": True}, "theme": "suddenness",
     "rule": _t("Results from a graha placed here arrive abruptly rather than building up.",
                "এখানে স্থিত গ্রহের ফল ধীরে না এসে আকস্মিকভাবে আসে।",
                "यहाँ स्थित ग्रह का फल क्रमशः नहीं, अकस्मात् आता है।"),
     "source": "P1 Bharani, technique 5"},
    {"nak": 1, "no": 6, "when": {"key_planet": True}, "theme": "turning point",
     "rule": _t("A woman, not necessarily a partner, changes how the native sees the world, often by an unorthodox lesson.",
                "কোনো নারী, যিনি প্রেমিকা হতেই হবে এমন নয়, জাতকের জগৎ-দৃষ্টি বদলে দেন, প্রায়ই অপ্রচলিত শিক্ষার মাধ্যমে।",
                "कोई स्त्री, जो प्रेमिका ही हो यह आवश्यक नहीं, जातक की विश्व-दृष्टि बदल देती है, प्रायः अपरंपरागत पाठ द्वारा।"),
     "source": "P1 Bharani, technique 6"},
    {"nak": 1, "no": 7, "when": {"any_planet": True}, "theme": "transformation",
     "rule": _t("A graha here brings one significant loss or reversal in the matters it governs, which becomes the turning point.",
                "এখানে স্থিত গ্রহ তার নিয়ন্ত্রিত বিষয়ে একটি উল্লেখযোগ্য ক্ষতি বা বিপর্যয় আনে, যা মোড় ঘোরায়।",
                "यहाँ स्थित ग्रह अपने विषयों में एक उल्लेखनीय हानि या उलटफेर लाता है, जो मोड़ बन जाता है।"),
     "source": "P1 Bharani, technique 7"},

    # ---- 3. Krittika ------------------------------------------------------------
    {"nak": 2, "no": 1, "when": {"any_planet": True}, "theme": "division",
     "rule": _t("Matters governed by a graha placed here tend to divide into two.",
                "এখানে স্থিত গ্রহের বিষয়সমূহ দুই ভাগে বিভক্ত হওয়ার প্রবণতা রাখে।",
                "यहाँ स्थित ग्रह के विषय दो भागों में विभाजित होने की प्रवृत्ति रखते हैं।"),
     "source": "P1 Krittika, technique 1"},
    {"nak": 2, "no": 2, "when": {"house_lord": [7, 8, 5], "planet": ["Venus"]}, "theme": "relationships",
     "rule": _t("The 7th, 8th or 5th lord, or Venus, placed here can show a relationship marked by rejection or by divided attention.",
                "সপ্তম, অষ্টম বা পঞ্চম ভাবাধিপতি, অথবা শুক্র এখানে থাকলে প্রত্যাখ্যান বা বিভক্ত মনোযোগ-চিহ্নিত সম্পর্ক নির্দেশ করতে পারে।",
                "सप्तम, अष्टम या पंचम भावाधिपति, अथवा शुक्र यहाँ हो तो अस्वीकृति या बँटे ध्यान वाला संबंध दर्शा सकता है।"),
     "source": "P1 Krittika, technique 2"},
    {"nak": 2, "no": 3, "when": {"key_planet": True}, "theme": "age event",
     "rule": _t("A significant event tends to fall around the 27th year.",
                "প্রায় ২৭তম বর্ষে একটি উল্লেখযোগ্য ঘটনা ঘটার প্রবণতা থাকে।",
                "लगभग 27वें वर्ष में एक उल्लेखनीय घटना घटने की प्रवृत्ति रहती है।"),
     "source": "P1 Krittika, technique 3"},
    {"nak": 2, "no": 4, "when": {"house_lord": [9, 5], "planet": ["Sun", "Jupiter"]}, "theme": "father and child",
     "rule": _t("The 9th or 5th lord, or the Sun or Jupiter, placed here shows a karmic settling of accounts between father and child, not necessarily about money.",
                "নবম বা পঞ্চম ভাবাধিপতি, অথবা সূর্য বা বৃহস্পতি এখানে থাকলে পিতা ও সন্তানের মধ্যে কর্মগত হিসাব-নিকাশ নির্দেশ করে, যা অর্থবিষয়ক হতেই হবে এমন নয়।",
                "नवम या पंचम भावाधिपति, अथवा सूर्य या बृहस्पति यहाँ हो तो पिता एवं संतान के बीच कर्मगत लेन-देन दर्शाता है, जो धन-संबंधी ही हो यह आवश्यक नहीं।"),
     "source": "P1 Krittika, technique 4"},

    # ---- 4. Rohini --------------------------------------------------------------
    {"nak": 3, "no": 1, "when": {"key_planet": True, "afflicted": True}, "theme": "reputation",
     "rule": _t("With this star afflicted, the native is at least once blamed for something they did not do.",
                "এই নক্ষত্র পীড়িত হলে জাতক অন্তত একবার এমন কিছুর জন্য অভিযুক্ত হন যা তিনি করেননি।",
                "यह नक्षत्र पीड़ित होने पर जातक कम से कम एक बार ऐसी बात के लिए दोषी ठहराया जाता है जो उसने की नहीं।"),
     "source": "P1 Rohini, technique 1"},
    {"nak": 3, "no": 3, "when": {"key_planet": True}, "theme": "relationships",
     "rule": _t("A tendency to measure a partner against earlier ones, in looks, habits or household matters.",
                "সঙ্গীকে পূর্ববর্তী সম্পর্কের সঙ্গে তুলনা করার প্রবণতা - চেহারা, অভ্যাস বা ঘরকন্নার বিষয়ে।",
                "साथी की तुलना पिछले संबंधों से करने की प्रवृत्ति - रूप, आदतों या गृहस्थी के विषयों में।"),
     "source": "P1 Rohini, technique 3"},
    {"nak": 3, "no": 5, "when": {"key_planet": True}, "theme": "originality",
     "rule": _t("Authorship and attribution become a live theme: either the native's work is copied, or questions of credit and signature arise around them.",
                "কর্তৃত্ব ও স্বীকৃতি একটি সক্রিয় বিষয় হয়ে ওঠে: হয় জাতকের কাজ নকল হয়, নয়তো কৃতিত্ব ও স্বাক্ষর নিয়ে প্রশ্ন ওঠে।",
                "कर्तृत्व एवं श्रेय एक सक्रिय विषय बन जाता है: या तो जातक का कार्य नकल होता है, या श्रेय एवं हस्ताक्षर पर प्रश्न उठते हैं।"),
     "source": "P1 Rohini, technique 5"},

    # ---- 5. Mrigashira ----------------------------------------------------------
    {"nak": 4, "no": 1, "when": {"key_planet": True}, "theme": "children",
     "rule": _t("Children of the native tend to come into their fortune later in life.",
                "জাতকের সন্তানেরা জীবনের পরবর্তী পর্যায়ে ভাগ্যোদয় পায়।",
                "जातक की संतानें जीवन के उत्तरार्ध में भाग्योदय पाती हैं।"),
     "source": "P2 Mrigashira, technique 1"},
    {"nak": 4, "no": 2, "when": {"key_planet": True}, "theme": "children",
     "rule": _t("Raising children is an area of friction rather than ease.",
                "সন্তান প্রতিপালন স্বচ্ছন্দ নয়, বরং সংঘর্ষের ক্ষেত্র।",
                "संतान-पालन सहज नहीं, बल्कि टकराव का क्षेत्र रहता है।"),
     "source": "P2 Mrigashira, technique 2"},
    {"nak": 4, "no": 4, "when": {"key_planet": True}, "theme": "sport",
     "rule": _t("An affinity for sports built on pursuit and running.",
                "ধাওয়া ও দৌড়ভিত্তিক ক্রীড়ার প্রতি আকর্ষণ।",
                "पीछा करने एवं दौड़ने पर आधारित खेलों के प्रति रुझान।"),
     "source": "P2 Mrigashira, technique 4"},
    {"nak": 4, "no": 6, "when": {"any_planet": True}, "theme": "direction sense",
     "rule": _t("Unafflicted, a strong sense of direction and place; afflicted, the opposite - getting lost and arriving late.",
                "অপীড়িত হলে দিকজ্ঞান ও স্থানবোধ প্রবল; পীড়িত হলে বিপরীত - পথ হারানো ও দেরিতে পৌঁছানো।",
                "अपीड़ित होने पर दिशाबोध एवं स्थानबोध प्रबल; पीड़ित होने पर विपरीत - राह भटकना एवं देर से पहुँचना।"),
     "source": "P2 Mrigashira, technique 6"},
    {"nak": 4, "no": 7, "when": {"house_lord": [5]}, "theme": "property",
     "rule": _t("The 5th lord placed here brings friction when property is divided.",
                "পঞ্চম ভাবাধিপতি এখানে থাকলে সম্পত্তি বিভাজনে সংঘাত আনে।",
                "पंचम भावाधिपति यहाँ हो तो संपत्ति विभाजन में टकराव लाता है।"),
     "source": "P2 Mrigashira, technique 7"},

    # ---- 6. Ardra ---------------------------------------------------------------
    {"nak": 5, "no": 1, "when": {"any_planet": True}, "theme": "animals",
     "rule": _t("The relative signified by a graha here has a pronounced relationship with animals, one way or the other.",
                "এখানে স্থিত গ্রহ দ্বারা নির্দেশিত আত্মীয়ের প্রাণীর সঙ্গে স্পষ্ট সম্পর্ক থাকে, কোনো না কোনোভাবে।",
                "यहाँ स्थित ग्रह द्वारा दर्शाए संबंधी का पशुओं से स्पष्ट संबंध रहता है, किसी न किसी रूप में।"),
     "source": "P1 Ardra, technique 1"},
    {"nak": 5, "no": 2, "when": {"key_planet": True}, "theme": "sacrifice",
     "rule": _t("A theme of self-sacrifice runs through the life.",
                "আত্মত্যাগের একটি ধারা জীবনজুড়ে চলে।",
                "आत्म-बलिदान की एक धारा जीवन भर चलती है।"),
     "source": "P1 Ardra, technique 2"},
    {"nak": 5, "no": 3, "when": {"any_planet": True, "in_houses": [6, 10]}, "theme": "disclosure",
     "rule": _t("A graha here tied to the 10th or 6th can put the native in the position of exposing what others would keep hidden.",
                "এখানে স্থিত গ্রহ দশম বা ষষ্ঠ ভাবের সঙ্গে যুক্ত হলে জাতককে গোপন বিষয় প্রকাশের ভূমিকায় বসাতে পারে।",
                "यहाँ स्थित ग्रह दशम या षष्ठ भाव से जुड़े तो जातक को छिपी बातें उजागर करने की भूमिका में ला सकता है।"),
     "source": "P1 Ardra, technique 3"},

    # ---- 7. Punarvasu -----------------------------------------------------------
    {"nak": 6, "no": 1, "when": {"key_planet": True}, "theme": "technology",
     "rule": _t("A pull towards technology and computing, strongest when Rahu is the graha involved.",
                "প্রযুক্তি ও কম্পিউটিং-এর প্রতি টান, রাহু জড়িত থাকলে সবচেয়ে প্রবল।",
                "प्रौद्योगिकी एवं कंप्यूटिंग की ओर झुकाव, राहु संलग्न हो तो सर्वाधिक प्रबल।"),
     "source": "P1 Punarvasu, technique 1"},
    {"nak": 6, "no": 2, "when": {"key_planet": True}, "theme": "stability",
     "rule": _t("Fortune and stability arrive, but only after a long period of searching.",
                "ভাগ্য ও স্থিতি আসে, তবে দীর্ঘ অন্বেষণের পরেই।",
                "भाग्य एवं स्थिरता आती है, किंतु लंबी खोज के उपरांत ही।"),
     "source": "P1 Punarvasu, technique 2"},
    {"nak": 6, "no": 3, "when": {"key_planet": True}, "theme": "food",
     "rule": _t("A declared concern with healthy eating that coexists with the opposite habit.",
                "স্বাস্থ্যকর খাদ্যের প্রতি ঘোষিত সচেতনতা, যার পাশাপাশি বিপরীত অভ্যাসও চলে।",
                "स्वास्थ्यप्रद भोजन के प्रति घोषित सजगता, जिसके साथ विपरीत आदत भी चलती है।"),
     "source": "P1 Punarvasu, technique 3"},
    {"nak": 6, "no": 4, "when": {"key_planet": True}, "theme": "care",
     "rule": _t("Where the native cares for someone, they take on a parental role towards them.",
                "যার প্রতি জাতক যত্নশীল হন, তার প্রতি পিতৃ-মাতৃসুলভ ভূমিকা গ্রহণ করেন।",
                "जिसकी भी जातक देखभाल करता है, उसके प्रति माता-पिता जैसी भूमिका ले लेता है।"),
     "source": "P1 Punarvasu, technique 4"},

    # ---- 8. Pushya --------------------------------------------------------------
    {"nak": 7, "no": 1, "when": {"key_planet": True}, "theme": "occult",
     "rule": _t("Contact with occult practice is likely, more so when the nodes influence this star.",
                "গুহ্যচর্চার সংস্পর্শ সম্ভাব্য, রাহু-কেতুর প্রভাব থাকলে আরও বেশি।",
                "गूढ़ साधना का संपर्क संभावित, राहु-केतु का प्रभाव हो तो और अधिक।"),
     "source": "P1 Pushya, technique 1"},
    {"nak": 7, "no": 2, "when": {"key_planet": True}, "theme": "remedy",
     "rule": _t("Recitation of the Narayana Kavach is named as the primary remedy for this star.",
                "এই নক্ষত্রের জন্য নারায়ণ কবচ পাঠকে প্রধান প্রতিকার হিসেবে নির্দেশ করা হয়েছে।",
                "इस नक्षत्र हेतु नारायण कवच का पाठ प्रमुख उपाय बताया गया है।"),
     "source": "P1 Pushya, technique 2"},
    {"nak": 7, "no": 3, "when": {"key_planet": True, "lagna": True}, "theme": "politics",
     "rule": _t("Manoeuvring for advantage is a live theme, either practised by the native or directed at them.",
                "সুবিধার জন্য কূটকৌশল একটি সক্রিয় বিষয় - জাতক নিজে করেন, অথবা তাঁর প্রতি প্রযুক্ত হয়।",
                "लाभ हेतु चालबाज़ी एक सक्रिय विषय रहता है - जातक स्वयं करे, या उस पर प्रयुक्त हो।"),
     "source": "P1 Pushya, technique 3"},
    {"nak": 7, "no": 4, "when": {"key_planet": True}, "theme": "fostering",
     "rule": _t("Themes of fostering appear - either raising a child not one's own, or having been raised by someone other than a parent.",
                "পালনের বিষয় দেখা যায় - হয় নিজের নয় এমন সন্তান প্রতিপালন, নয়তো পিতামাতা ছাড়া অন্যের কাছে বড় হওয়া।",
                "पालन-पोषण के विषय दिखते हैं - या तो अपनी न होने वाली संतान का पालन, या माता-पिता के अतिरिक्त किसी और द्वारा पाला जाना।"),
     "source": "P1 Pushya, technique 4"},

    # ---- 9. Ashlesha ------------------------------------------------------------
    {"nak": 8, "no": 1, "when": {"any_planet": True}, "theme": "age event",
     "rule": _t("A graha placed here tends to deliver its result between the ages of 18 and 20.",
                "এখানে স্থিত গ্রহ সাধারণত ১৮ থেকে ২০ বছর বয়সের মধ্যে ফল দেয়।",
                "यहाँ स्थित ग्रह प्रायः 18 से 20 वर्ष की आयु के बीच फल देता है।"),
     "source": "P1 Ashlesha, technique 1"},
    {"nak": 8, "no": 2, "when": {"always": True}, "theme": "speech",
     "rule": _t("This star sits at the gandanta, the junction point. Its central discipline is speech: speaking ill of others is the one habit that costs most here.",
                "এই নক্ষত্র গণ্ডান্তে, সন্ধিস্থলে অবস্থিত। এর মূল সংযম বাক্যে: পরনিন্দাই এখানে সবচেয়ে ব্যয়বহুল অভ্যাস।",
                "यह नक्षत्र गंडांत, संधिस्थल पर स्थित है। इसका मूल संयम वाणी में है: परनिंदा ही यहाँ सर्वाधिक महँगी आदत है।"),
     "source": "P1 Ashlesha, technique 2"},
    {"nak": 8, "no": 3, "when": {"key_planet": True}, "theme": "psychic",
     "rule": _t("Experiences the native reads as psychic or uncanny are reported with this placement.",
                "এই অবস্থানে জাতক অতীন্দ্রিয় বা অস্বাভাবিক বলে বোধ করেন এমন অভিজ্ঞতা জানা যায়।",
                "इस स्थिति में जातक अतींद्रिय या असामान्य मानी जाने वाली अनुभूतियाँ बताते हैं।"),
     "source": "P1 Ashlesha, technique 3"},
    {"nak": 8, "no": 5, "when": {"any_planet": True}, "theme": "transformation",
     "rule": _t("Whichever area of life this star falls in undergoes a major transformation, in either direction.",
                "এই নক্ষত্র জীবনের যে ক্ষেত্রে পড়ে, সেখানে বড় রূপান্তর ঘটে - যেকোনো দিকে।",
                "यह नक्षत्र जीवन के जिस क्षेत्र में पड़े, वहाँ बड़ा रूपांतरण होता है - किसी भी दिशा में।"),
     "source": "P1 Ashlesha, technique 5"},

    # ---- 10. Magha --------------------------------------------------------------
    {"nak": 9, "no": 1, "when": {"always": True}, "theme": "age event",
     "rule": _t("This star becomes more prominent in the chart from around the age of 21, whether or not a graha occupies it.",
                "প্রায় ২১ বছর বয়স থেকে এই নক্ষত্র কুণ্ডলীতে অধিক সক্রিয় হয়, এখানে গ্রহ থাকুক বা না থাকুক।",
                "लगभग 21 वर्ष की आयु से यह नक्षत्र कुंडली में अधिक सक्रिय होता है, चाहे यहाँ ग्रह हो या न हो।"),
     "source": "P2 Magha, technique 1"},
    {"nak": 9, "no": 2, "when": {"key_planet": True}, "theme": "authority",
     "rule": _t("A strong pull towards positions of authority, which becomes a liability if this star or its lord is afflicted.",
                "কর্তৃত্বের পদের প্রতি প্রবল টান, যা এই নক্ষত্র বা তার অধিপতি পীড়িত হলে দুর্বলতায় পরিণত হয়।",
                "अधिकार-पदों की ओर प्रबल खिंचाव, जो यह नक्षत्र या इसका अधिपति पीड़ित होने पर दुर्बलता बन जाता है।"),
     "source": "P2 Magha, technique 2"},
    {"nak": 9, "no": 3, "when": {"any_planet": True, "lagna": True}, "theme": "authority",
     "rule": _t("A fall from a position of standing is indicated, most clearly when the graha involved is a malefic.",
                "প্রতিষ্ঠিত অবস্থান থেকে পতন নির্দেশিত, বিশেষত জড়িত গ্রহ পাপগ্রহ হলে।",
                "प्रतिष्ठित स्थान से पतन संकेतित, विशेषतः संलग्न ग्रह पापग्रह हो तो।"),
     "source": "P2 Magha, technique 3"},
    {"nak": 9, "no": 4, "when": {"afflicted": True}, "theme": "finance",
     "rule": _t("With this star or its lord afflicted, at least one severe loss in markets or speculative investment is indicated.",
                "এই নক্ষত্র বা তার অধিপতি পীড়িত হলে বাজার বা ফাটকা বিনিয়োগে অন্তত একটি বড় ক্ষতি নির্দেশিত।",
                "यह नक्षत्र या इसका अधिपति पीड़ित हो तो बाज़ार या सट्टा निवेश में कम से कम एक बड़ी हानि संकेतित।"),
     "source": "P2 Magha, technique 4"},
    {"nak": 9, "no": 5, "when": {"afflicted": True}, "theme": "spirituality",
     "rule": _t("When afflicted, particularly by Jupiter or Rahu, a long attachment to a mistaken idea of spiritual progress.",
                "পীড়িত হলে, বিশেষত বৃহস্পতি বা রাহু দ্বারা, আধ্যাত্মিক অগ্রগতির ভ্রান্ত ধারণায় দীর্ঘ আসক্তি।",
                "पीड़ित होने पर, विशेषतः बृहस्पति या राहु से, आध्यात्मिक प्रगति की भ्रांत धारणा में लंबी आसक्ति।"),
     "source": "P2 Magha, technique 5"},
    {"nak": 9, "no": 6, "when": {"afflicted": True}, "theme": "lineage",
     "rule": _t("Affliction here, especially involving the nodes, points to an inherited family burden.",
                "এখানে পীড়ন, বিশেষত রাহু-কেতু জড়িত থাকলে, উত্তরাধিকারসূত্রে পাওয়া পারিবারিক ভার নির্দেশ করে।",
                "यहाँ पीड़न, विशेषतः राहु-केतु संलग्न हों, तो वंशानुगत पारिवारिक भार दर्शाता है।"),
     "source": "P2 Magha, technique 6"},

    # ---- 11. Purva Phalguni -----------------------------------------------------
    {"nak": 10, "no": 1, "when": {"always": True}, "theme": "age event",
     "rule": _t("An important relationship, or a clear activation of this star, falls around the age of 24, give or take a year.",
                "একটি গুরুত্বপূর্ণ সম্পর্ক, বা এই নক্ষত্রের স্পষ্ট সক্রিয়তা, প্রায় ২৪ বছর বয়সে ঘটে, এক বছর এদিক-ওদিক।",
                "एक महत्वपूर्ण संबंध, या इस नक्षत्र की स्पष्ट सक्रियता, लगभग 24 वर्ष की आयु में आती है, एक वर्ष आगे-पीछे।"),
     "source": "P2 Purva Phalguni, technique 1"},
    {"nak": 10, "no": 2, "when": {"key_planet": True}, "theme": "paperwork",
     "rule": _t("At least once, documentation or paperwork becomes a source of real trouble.",
                "অন্তত একবার নথিপত্র বা কাগজপত্র প্রকৃত সমস্যার কারণ হয়।",
                "कम से कम एक बार दस्तावेज़ या कागज़ी कार्य वास्तविक परेशानी का कारण बनता है।"),
     "source": "P2 Purva Phalguni, technique 2"},
    {"nak": 10, "no": 3, "when": {"planet": ["Mars"]}, "theme": "property",
     "rule": _t("Mars placed here or aspecting it can raise property disputes.",
                "মঙ্গল এখানে স্থিত বা দৃষ্টিপাত করলে সম্পত্তি নিয়ে বিরোধ তুলতে পারে।",
                "मंगल यहाँ स्थित हो या दृष्टि डाले तो संपत्ति विवाद उठा सकता है।"),
     "source": "P2 Purva Phalguni, technique 3"},
    {"nak": 10, "no": 5, "when": {"key_planet": True}, "theme": "remedy",
     "rule": _t("Fire rituals are named as the appropriate remedial practice for this star.",
                "এই নক্ষত্রের উপযুক্ত প্রতিকার হিসেবে হোম-যজ্ঞের নির্দেশ রয়েছে।",
                "इस नक्षत्र हेतु उपयुक्त उपाय के रूप में हवन-यज्ञ निर्दिष्ट है।"),
     "source": "P2 Purva Phalguni, technique 5"},
    {"nak": 10, "no": 6, "when": {"key_planet": True}, "theme": "home",
     "rule": _t("Unafflicted, a well-situated home and a marked appreciation of good lodging.",
                "অপীড়িত হলে সুস্থিত গৃহ এবং উত্তম বাসস্থানের প্রতি স্পষ্ট অনুরাগ।",
                "अपीड़ित होने पर सुस्थित गृह एवं उत्तम निवास के प्रति स्पष्ट अनुराग।"),
     "source": "P2 Purva Phalguni, technique 6"},
    {"nak": 10, "no": 8, "when": {"key_planet": True}, "theme": "eyes",
     "rule": _t("Recurring trouble with the eyes - weak sight, infection, or eyewear repeatedly lost or broken.",
                "চোখ নিয়ে বারবার সমস্যা - দুর্বল দৃষ্টি, সংক্রমণ, বা চশমা বারবার হারানো বা ভাঙা।",
                "नेत्रों की बार-बार समस्या - दुर्बल दृष्टि, संक्रमण, या चश्मा बार-बार खोना या टूटना।"),
     "source": "P2 Purva Phalguni, technique 8"},
    {"nak": 10, "no": 10, "when": {"key_planet": True}, "theme": "display",
     "rule": _t("A liking for display and ceremony.",
                "আড়ম্বর ও জাঁকজমকের প্রতি অনুরাগ।",
                "आडंबर एवं भव्यता के प्रति अनुराग।"),
     "source": "P2 Purva Phalguni, technique 10"},
    {"nak": 10, "no": 12, "when": {"key_planet": True}, "theme": "setbacks",
     "rule": _t("A relaxed approach to planning brings several major course corrections across the life.",
                "পরিকল্পনায় শিথিলতা জীবনে একাধিক বড় মোড়-বদল আনে।",
                "योजना में शिथिलता जीवन में कई बड़े मोड़ लाती है।"),
     "source": "P2 Purva Phalguni, technique 12"},

    # ---- 12. Uttara Phalguni ----------------------------------------------------
    {"nak": 11, "no": 1, "when": {"afflicted": True}, "theme": "relationships",
     "rule": _t("Malefics occupying or aspecting this star can strain relationships with a partner or close friends.",
                "পাপগ্রহ এখানে স্থিত বা দৃষ্টিপাত করলে সঙ্গী বা ঘনিষ্ঠ বন্ধুর সঙ্গে সম্পর্কে টান পড়ে।",
                "पापग्रह यहाँ स्थित हों या दृष्टि डालें तो साथी या निकट मित्रों से संबंध में तनाव आता है।"),
     "source": "P2 Uttara Phalguni, technique 1"},
    {"nak": 11, "no": 2, "when": {"key_planet": True}, "theme": "spirituality",
     "rule": _t("Ambition in spiritual matters can lead towards the wrong kind of practice; under benefic influence it turns instead to the health sciences.",
                "আধ্যাত্মিক বিষয়ে উচ্চাকাঙ্ক্ষা ভুল পথে নিয়ে যেতে পারে; শুভগ্রহের প্রভাবে তা স্বাস্থ্যবিজ্ঞানের দিকে মোড় নেয়।",
                "आध्यात्मिक विषयों में महत्वाकांक्षा गलत साधना की ओर ले जा सकती है; शुभ ग्रह के प्रभाव में यह स्वास्थ्य-विज्ञान की ओर मुड़ती है।"),
     "source": "P2 Uttara Phalguni, technique 2"},
    {"nak": 11, "no": 3, "when": {"key_planet": True}, "theme": "wealth",
     "rule": _t("When a wealth-giving graha connects to this star, money becomes central to a partnership - for better or worse.",
                "ধনদায়ক গ্রহ এই নক্ষত্রের সঙ্গে যুক্ত হলে সম্পর্কে অর্থ কেন্দ্রীয় হয়ে ওঠে - ভালো বা মন্দ দুইভাবেই।",
                "धनदायक ग्रह इस नक्षत्र से जुड़े तो संबंध में धन केंद्रीय हो जाता है - भले या बुरे, दोनों रूपों में।"),
     "source": "P2 Uttara Phalguni, technique 3"},

    # ---- 13. Hasta --------------------------------------------------------------
    {"nak": 12, "no": 1, "when": {"key_planet": True}, "theme": "skill",
     "rule": _t("Marked dexterity with material and with argument; afflicted by a malefic, the same skill turns to manipulation.",
                "বস্তু ও যুক্তি - উভয়েই স্পষ্ট নৈপুণ্য; পাপগ্রহ দ্বারা পীড়িত হলে সেই দক্ষতাই কারসাজিতে পরিণত হয়।",
                "वस्तु एवं तर्क - दोनों में स्पष्ट निपुणता; पापग्रह से पीड़ित होने पर वही कौशल चालाकी बन जाता है।"),
     "source": "P2 Hasta, technique 1"},
    {"nak": 12, "no": 2, "when": {"key_planet": True}, "theme": "age event",
     "rule": _t("A significant event tends to fall in the 24th running year.",
                "২৪তম চলতি বর্ষে একটি উল্লেখযোগ্য ঘটনা ঘটার প্রবণতা থাকে।",
                "24वें चालू वर्ष में एक उल्लेखनीय घटना घटने की प्रवृत्ति रहती है।"),
     "source": "P2 Hasta, technique 2"},
    {"nak": 12, "no": 3, "when": {"house_lord": [9], "afflicted": True}, "theme": "father",
     "rule": _t("With this star afflicted, or the 9th lord placed here and afflicted, the father's circumstances are unsettled during the native's first four years.",
                "এই নক্ষত্র পীড়িত হলে, বা নবম ভাবাধিপতি এখানে স্থিত ও পীড়িত হলে, জাতকের প্রথম চার বছরে পিতার অবস্থা অস্থির থাকে।",
                "यह नक्षत्र पीड़ित हो, या नवम भावाधिपति यहाँ स्थित एवं पीड़ित हो, तो जातक के प्रथम चार वर्षों में पिता की स्थिति अस्थिर रहती है।"),
     "source": "P2 Hasta, technique 3"},

    # ---- 14. Chitra -------------------------------------------------------------
    {"nak": 13, "no": 1, "when": {"key_planet": True}, "theme": "health",
     "rule": _t("Recurring complaints centred on the stomach or the head.",
                "পেট বা মাথা কেন্দ্রিক বারবার সমস্যা।",
                "पेट या सिर केंद्रित बार-बार की शिकायतें।"),
     "source": "P2 Chitra, technique 1"},
    {"nak": 13, "no": 3, "when": {"key_planet": True}, "theme": "precision",
     "rule": _t("A fine eye for detail and for working through complexity, giving a sharp and attentive mind.",
                "সূক্ষ্মতা ও জটিলতা উদ্ধারে তীক্ষ্ণ দৃষ্টি, যা মনকে ধারালো ও মনোযোগী করে।",
                "सूक्ष्मता एवं जटिलता सुलझाने में तीक्ष्ण दृष्टि, जो मन को पैना एवं सजग बनाती है।"),
     "source": "P2 Chitra, technique 3"},
    {"nak": 13, "no": 4, "when": {"afflicted": True}, "theme": "order",
     "rule": _t("Afflicted, order is hard to maintain, and deliberately building order is the remedy; unafflicted, the native is systematic by nature.",
                "পীড়িত হলে শৃঙ্খলা রক্ষা কঠিন, এবং সচেতনভাবে শৃঙ্খলা গড়াই প্রতিকার; অপীড়িত হলে জাতক স্বভাবতই সুশৃঙ্খল।",
                "पीड़ित होने पर व्यवस्था बनाए रखना कठिन, एवं सचेत रूप से व्यवस्था बनाना ही उपाय; अपीड़ित होने पर जातक स्वभावतः व्यवस्थित।"),
     "source": "P2 Chitra, technique 4"},
    {"nak": 13, "no": 5, "when": {"afflicted": True}, "theme": "incompleteness",
     "rule": _t("Afflicted, one area of life stays unfinished or divided, rarely fully resolved.",
                "পীড়িত হলে জীবনের একটি ক্ষেত্র অসমাপ্ত বা বিভক্ত থেকে যায়, কদাচিৎ পূর্ণ সমাধান পায়।",
                "पीड़ित होने पर जीवन का एक क्षेत्र अधूरा या बँटा रह जाता है, विरले ही पूर्ण समाधान पाता है।"),
     "source": "P2 Chitra, technique 5"},
    {"nak": 13, "no": 6, "when": {"key_planet": True}, "theme": "creativity",
     "rule": _t("High creative capacity. Directing it towards display afflicts the star; practising detachment lifts the whole chart.",
                "উচ্চ সৃজনক্ষমতা। তা আড়ম্বরের দিকে চালিত করলে নক্ষত্র পীড়িত হয়; নির্লিপ্তি অভ্যাস করলে সমগ্র কুণ্ডলী উন্নত হয়।",
                "उच्च सृजन-क्षमता। उसे आडंबर की ओर मोड़ने पर नक्षत्र पीड़ित होता है; अनासक्ति का अभ्यास पूरी कुंडली को उठाता है।"),
     "source": "P2 Chitra, technique 6"},

    # ---- 15. Swati --------------------------------------------------------------
    {"nak": 14, "no": 2, "when": {"key_planet": True}, "theme": "mother",
     "rule": _t("A deep unresolved matter involving the mother, or inheritance.",
                "মাতা বা উত্তরাধিকার সংক্রান্ত একটি গভীর অমীমাংসিত বিষয়।",
                "माता अथवा उत्तराधिकार से जुड़ा एक गहरा अनसुलझा विषय।"),
     "source": "P2 Swati, technique 2"},
    {"nak": 14, "no": 3, "when": {"key_planet": True}, "theme": "illusion",
     "rule": _t("One area of life holds a persistent illusion the native keeps returning to, its strength set by Rahu's strength in the chart.",
                "জীবনের একটি ক্ষেত্রে একটি স্থায়ী বিভ্রম থাকে, যেখানে জাতক বারবার ফিরে আসেন; এর তীব্রতা কুণ্ডলীতে রাহুর বলের উপর নির্ভর করে।",
                "जीवन के एक क्षेत्र में एक स्थायी भ्रम रहता है जहाँ जातक बार-बार लौटता है; इसकी तीव्रता कुंडली में राहु के बल पर निर्भर है।"),
     "source": "P2 Swati, technique 3"},
    {"nak": 14, "no": 4, "when": {"key_planet": True}, "theme": "remedy",
     "rule": _t("Breath practice is named as the essential remedy for this star.",
                "এই নক্ষত্রের অপরিহার্য প্রতিকার হিসেবে প্রাণায়াম নির্দেশিত।",
                "इस नक्षत्र हेतु अनिवार्य उपाय के रूप में प्राणायाम निर्दिष्ट है।"),
     "source": "P2 Swati, technique 4"},
    {"nak": 14, "no": 5, "when": {"afflicted": True}, "theme": "breathing",
     "rule": _t("Afflicted, or tied to an afflicted 3rd house or its lord, breathing complaints are indicated.",
                "পীড়িত হলে, বা পীড়িত তৃতীয় ভাব বা তার অধিপতির সঙ্গে যুক্ত হলে, শ্বাসকষ্ট নির্দেশিত।",
                "पीड़ित हो, या पीड़ित तृतीय भाव या उसके अधिपति से जुड़ा हो, तो श्वास संबंधी शिकायत संकेतित।"),
     "source": "P2 Swati, technique 5"},
    {"nak": 14, "no": 6, "when": {"key_planet": True}, "theme": "remedy",
     "rule": _t("Herbal treatment suits this star well, provided the Moon is unafflicted.",
                "চন্দ্র অপীড়িত থাকলে এই নক্ষত্রের জন্য ভেষজ চিকিৎসা উপযোগী।",
                "चंद्र अपीड़ित हो तो इस नक्षत्र हेतु जड़ी-बूटी चिकित्सा उपयुक्त है।"),
     "source": "P2 Swati, technique 6"},
    {"nak": 14, "no": 7, "when": {"afflicted": True}, "theme": "belief",
     "rule": _t("Afflicted, or tied to the 9th house or its lord, belief tends to either change entirely or harden.",
                "পীড়িত হলে, বা নবম ভাব বা তার অধিপতির সঙ্গে যুক্ত হলে, বিশ্বাস হয় সম্পূর্ণ বদলায় নয়তো কঠোর হয়।",
                "पीड़ित हो, या नवम भाव या उसके अधिपति से जुड़ा हो, तो आस्था या तो पूर्णतः बदलती है या कठोर हो जाती है।"),
     "source": "P2 Swati, technique 7"},

    # ---- 16. Vishakha -----------------------------------------------------------
    {"nak": 15, "no": 1, "when": {"key_planet": True}, "theme": "grudges",
     "rule": _t("A grievance tends to be carried for an unusually long time.",
                "কোনো ক্ষোভ অস্বাভাবিক দীর্ঘ সময় ধরে বহন করার প্রবণতা।",
                "कोई शिकायत असामान्य रूप से लंबे समय तक ढोने की प्रवृत्ति।"),
     "source": "P2 Vishakha, technique 1"},
    {"nak": 15, "no": 2, "when": {"key_planet": True}, "theme": "career",
     "rule": _t("Two parallel occupations, or one occupation and a pursuit held with equal seriousness.",
                "দুটি সমান্তরাল পেশা, অথবা একটি পেশা ও একটি সমান গুরুত্বে ধরা চর্চা।",
                "दो समानांतर व्यवसाय, अथवा एक व्यवसाय एवं समान गंभीरता से किया गया एक अभ्यास।"),
     "source": "P2 Vishakha, technique 2"},
    {"nak": 15, "no": 3, "when": {"afflicted": True}, "theme": "ambition",
     "rule": _t("With this star or its lord afflicted, ambition stops weighing the cost of success.",
                "এই নক্ষত্র বা তার অধিপতি পীড়িত হলে উচ্চাকাঙ্ক্ষা সাফল্যের মূল্য বিচার করা ছেড়ে দেয়।",
                "यह नक्षत्र या इसका अधिपति पीड़ित हो तो महत्वाकांक्षा सफलता की कीमत तौलना छोड़ देती है।"),
     "source": "P2 Vishakha, technique 3"},

    # ---- 17. Anuradha -----------------------------------------------------------
    {"nak": 16, "no": 1, "when": {"key_planet": True}, "theme": "age event",
     "rule": _t("A significant event tends to fall in the 26th running year.",
                "২৬তম চলতি বর্ষে একটি উল্লেখযোগ্য ঘটনা ঘটার প্রবণতা থাকে।",
                "26वें चालू वर्ष में एक उल्लेखनीय घटना घटने की प्रवृत्ति रहती है।"),
     "source": "P2 Anuradha, technique 1"},
    {"nak": 16, "no": 2, "when": {"afflicted": True}, "theme": "pride",
     "rule": _t("One decisive event breaks a false sense of pride - most clearly when a malefic occupies this star.",
                "একটি নির্ণায়ক ঘটনা মিথ্যা অহংকার ভেঙে দেয় - বিশেষত পাপগ্রহ এখানে স্থিত হলে।",
                "एक निर्णायक घटना मिथ्या अहंकार तोड़ देती है - विशेषतः पापग्रह यहाँ स्थित हो तो।"),
     "source": "P2 Anuradha, technique 2"},
    {"nak": 16, "no": 3, "when": {"moon": True, "key_planet": True}, "theme": "mother figure",
     "rule": _t("A mother-like figure withdraws support at a decisive moment.",
                "মাতৃসম কোনো ব্যক্তি নির্ণায়ক মুহূর্তে সমর্থন প্রত্যাহার করেন।",
                "माता-तुल्य कोई व्यक्ति निर्णायक क्षण में सहारा हटा लेता है।"),
     "source": "P2 Anuradha, technique 3"},

    # ---- 18. Jyeshtha -----------------------------------------------------------
    {"nak": 17, "no": 1, "when": {"key_planet": True, "afflicted": True}, "theme": "finance",
     "rule": _t("Afflicted, financial setbacks or money let go of, most clearly when the 2nd, 4th, 6th, 7th, 8th, 11th or 12th is involved.",
                "পীড়িত হলে আর্থিক বিপর্যয় বা অর্থ হাতছাড়া হওয়া, বিশেষত দ্বিতীয়, চতুর্থ, ষষ্ঠ, সপ্তম, অষ্টম, একাদশ বা দ্বাদশ ভাব জড়িত থাকলে।",
                "पीड़ित होने पर आर्थिक झटके या धन का हाथ से जाना, विशेषतः द्वितीय, चतुर्थ, षष्ठ, सप्तम, अष्टम, एकादश या द्वादश भाव संलग्न हो तो।"),
     "source": "P2 Jyeshtha, technique 1"},
    {"nak": 17, "no": 2, "when": {"afflicted": True, "in_houses": [7, 8, 12]}, "theme": "reputation",
     "rule": _t("A malefic here tied to the 7th, 8th or 12th, with the rest of the chart agreeing, can draw the native into public controversy.",
                "এখানে পাপগ্রহ সপ্তম, অষ্টম বা দ্বাদশ ভাবের সঙ্গে যুক্ত হলে এবং কুণ্ডলীর বাকি অংশ সমর্থন করলে জাতক প্রকাশ্য বিতর্কে জড়াতে পারেন।",
                "यहाँ पापग्रह सप्तम, अष्टम या द्वादश भाव से जुड़े एवं शेष कुंडली सहमत हो तो जातक सार्वजनिक विवाद में फँस सकता है।"),
     "source": "P2 Jyeshtha, technique 2"},
    {"nak": 17, "no": 4, "when": {"house_lord": [3], "afflicted": True}, "theme": "body",
     "rule": _t("Afflicted, or with an afflicted 3rd lord here, a mark or injury to the middle finger is indicated.",
                "পীড়িত হলে, বা পীড়িত তৃতীয় ভাবাধিপতি এখানে থাকলে, মধ্যমায় চিহ্ন বা আঘাত নির্দেশিত।",
                "पीड़ित हो, या पीड़ित तृतीय भावाधिपति यहाँ हो, तो मध्यमा अंगुली पर चिह्न या चोट संकेतित।"),
     "source": "P2 Jyeshtha, technique 4"},
    {"nak": 17, "no": 5, "when": {"key_planet": True}, "theme": "remedy",
     "rule": _t("Significant results are reported within a year of a ritual bath in the Ganga, in the area the graha here governs.",
                "গঙ্গাস্নানের এক বছরের মধ্যে উল্লেখযোগ্য ফল জানা যায়, এখানে স্থিত গ্রহের নিয়ন্ত্রিত ক্ষেত্রে।",
                "गंगा स्नान के एक वर्ष के भीतर उल्लेखनीय फल बताए गए हैं, यहाँ स्थित ग्रह के क्षेत्र में।"),
     "source": "P2 Jyeshtha, technique 5"},
]


# --------------------------------------------------------------------------------------
# Chart evaluation
# --------------------------------------------------------------------------------------
def _house_of(sign_index: int, asc_sign_index: int) -> int:
    """Whole-sign house number, the basis Vedic technique rules assume."""
    return ((sign_index - asc_sign_index) % 12) + 1


def build_chart_facts(
    planets: list[dict[str, Any]],
    ascendant_sign_index: int,
    ascendant_nakshatra_index: int,
) -> dict[str, Any]:
    """Reduce a computed chart to the facts the technique conditions ask about.

    `planets` entries need: name, sign_index, nakshatra_index, house.
    """
    asc = ascendant_sign_index % 12
    lagna_lord = SIGN_LORDS[asc]

    by_nakshatra: dict[int, list[dict[str, Any]]] = {}
    for p in planets:
        by_nakshatra.setdefault(p["nakshatra_index"], []).append(p)

    # Lord of each house, by whole sign from the ascendant.
    house_lords = {h: SIGN_LORDS[(asc + h - 1) % 12] for h in range(1, 13)}

    # Which nakshatras each graha aspects, by whole-sign aspect from its own sign.
    aspected_nakshatras: dict[int, list[str]] = {}
    for p in planets:
        targets = {7, *SPECIAL_ASPECTS.get(p["name"], ())}
        for offset in targets:
            target_sign = (p["sign_index"] + offset - 1) % 12
            for other in planets:
                if other["sign_index"] == target_sign:
                    aspected_nakshatras.setdefault(other["nakshatra_index"], []).append(p["name"])

    return {
        "planets": planets,
        "by_nakshatra": by_nakshatra,
        "house_lords": house_lords,
        "lagna_lord": lagna_lord,
        "ascendant_sign_index": asc,
        "ascendant_nakshatra_index": ascendant_nakshatra_index,
        "aspected_nakshatras": aspected_nakshatras,
    }


def _is_afflicted(nak_index: int, facts: dict[str, Any]) -> tuple[bool, list[str]]:
    """A nakshatra is afflicted when a malefic sits in it or aspects it.

    The books also count 'the nakshatra lord is afflicted'. That needs the lord's own
    dignity, which this calculator does not yet judge, so only the two mechanical
    tests are applied and the reason is always reported alongside the verdict.
    """
    reasons: list[str] = []
    for p in facts["by_nakshatra"].get(nak_index, []):
        if p["name"] in NATURAL_MALEFICS:
            reasons.append(f"{p['name']} is placed here")
    for name in facts["aspected_nakshatras"].get(nak_index, []):
        if name in NATURAL_MALEFICS:
            reasons.append(f"{name} aspects it")
    return bool(reasons), sorted(set(reasons))


def _matches(technique: dict[str, Any], nak_index: int, facts: dict[str, Any]) -> tuple[bool, list[str]]:
    """Whether a technique's condition holds, and why."""
    when = technique["when"]
    occupants = facts["by_nakshatra"].get(nak_index, [])
    why: list[str] = []
    satisfied = False

    if when.get("always"):
        return True, ["applies to this birth star itself"]

    if when.get("moon") and any(p["name"] == "Moon" for p in occupants):
        satisfied = True
        why.append("the Moon is here")

    if when.get("any_planet") and occupants:
        satisfied = True
        why.append(", ".join(p["name"] for p in occupants) + " placed here")

    if when.get("key_planet"):
        key = {"Sun", "Moon", facts["lagna_lord"]}
        found = [p["name"] for p in occupants if p["name"] in key]
        if facts["ascendant_nakshatra_index"] == nak_index:
            found.append("the ascendant")
        if found:
            satisfied = True
            why.append(", ".join(found) + " (a focal point) here")

    if when.get("lagna") and facts["ascendant_nakshatra_index"] == nak_index:
        satisfied = True
        why.append("the ascendant falls here")

    if when.get("aspected") and facts["aspected_nakshatras"].get(nak_index):
        satisfied = True
        why.append(", ".join(sorted(set(facts["aspected_nakshatras"][nak_index]))) + " aspects it")

    wanted_planets = when.get("planet")
    if wanted_planets:
        found = [p["name"] for p in occupants if p["name"] in wanted_planets]
        if found:
            satisfied = True
            why.append(", ".join(found) + " placed here")

    wanted_houses = when.get("house_lord")
    if wanted_houses:
        names = {p["name"] for p in occupants}
        found = [h for h in wanted_houses if facts["house_lords"][h] in names]
        if found:
            satisfied = True
            why.append(
                ", ".join(f"the {h}th lord" for h in sorted(found)) + " is placed here"
            )

    if when.get("afflicted"):
        afflicted, reasons = _is_afflicted(nak_index, facts)
        if not afflicted:
            return False, []
        satisfied = True
        why.extend(reasons)

    wanted_in_houses = when.get("in_houses")
    if wanted_in_houses:
        found = [p["name"] for p in occupants if p["house"] in wanted_in_houses]
        if not found:
            return False, []
        satisfied = True
        why.append(
            ", ".join(found) + " here sits in house "
            + "/".join(str(p["house"]) for p in occupants if p["house"] in wanted_in_houses)
        )

    return satisfied, why


def evaluate_techniques(
    nak_index: int, facts: dict[str, Any], lang: Lang = "en"
) -> dict[str, Any]:
    """Which of the client's techniques this chart actually satisfies."""
    available = [t for t in TECHNIQUES if t["nak"] == nak_index]
    matched: list[dict[str, Any]] = []
    not_matched: list[dict[str, Any]] = []

    for technique in available:
        ok, why = _matches(technique, nak_index, facts)
        entry = {
            "technique_no": technique["no"],
            "theme": technique["theme"],
            "rule": technique["rule"].get(lang) or technique["rule"]["en"],
            "source": technique["source"],
        }
        if ok:
            entry["because"] = why
            matched.append(entry)
        else:
            not_matched.append(entry)

    afflicted, affliction_reasons = _is_afflicted(nak_index, facts)
    has_source = nak_index < 18

    return {
        "nakshatra_index": nak_index,
        "nakshatra_name": NAKSHATRA_NAMES[nak_index],
        "has_client_source": has_source,
        "matched": matched,
        "not_matched": not_matched,
        "total_available": len(available),
        "is_afflicted": afflicted,
        "affliction_reasons": affliction_reasons,
        "book_reference": BOOK_REFERENCE.get(nak_index),
        "unavailable_note": None
        if has_source
        else (
            MISSING_FROM_CLIENT_RESOURCES["note"].get(lang)
            or MISSING_FROM_CLIENT_RESOURCES["note"]["en"]
        ),
    }


def coverage_summary() -> dict[str, Any]:
    """How much of the zodiac the client's supplied books actually cover."""
    per_nakshatra = {
        i: len([t for t in TECHNIQUES if t["nak"] == i]) for i in range(27)
    }
    return {
        "nakshatras_with_source": sum(1 for v in per_nakshatra.values() if v),
        "nakshatras_total": 27,
        "techniques_total": len(TECHNIQUES),
        "per_nakshatra": per_nakshatra,
        "missing": MISSING_FROM_CLIENT_RESOURCES,
    }
