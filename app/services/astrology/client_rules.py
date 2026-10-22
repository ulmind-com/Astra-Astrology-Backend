"""Rashi classification rules transcribed verbatim from the client's resource documents.

PROVENANCE — every value in this module is traceable to a client-supplied file:

  [01]  Resource Documents/Rashi Rules/01.pdf  ("Rashi Characteristics", 13 pages)
        The master classification document. Its own opening line states the twelve
        signs are "classified into 15 groups depending on their nature, influences
        and characteristics". All fifteen groups are transcribed below.
  [12R] Resource Documents/Rashi Rules/12 Rashis and Their Planetary Lords.pdf
        Sign -> planetary lord table.
  [RCT] Resource Documents/Rashi Rules/Rashi Characteristics and Traits Overview.pdf
        Per-sign keyword lists (traits, places, body parts).
  [KPB] Resource Documents/Rashi Rules/KP Astrology Basics and Rules.pdf
        The five basic rules of the KP system and the twelve house significations.

Both 01.pdf and KP Astrology Basics and Rules.pdf arrived with their embedded font
CMaps scrambled (a per-glyph substitution). They were decoded losslessly to
Resource Documents/_extracted/rashi/*-decoded.txt. The digit substitution in 01.pdf
resolves as 2->0, 3->1, ':'->2, 6->3, 4->4, 8->5, verified against four independent
self-consistency checks in the document ("5 elements - fire, water, air, earth and
ether", "the 5th element of aakaasa or ether", "Tenth house shows the career ... if
the 10th house", "23.4 degrees of the Earth's axis"). Accordingly the fruitfulness
rule on page 10, which decodes literally as "5th house cusp", is recorded as the
5th cusp below.

NOTHING in this module is invented, inferred from general astrological knowledge, or
sourced from any third party. Where the client's own document contradicts itself the
contradiction is preserved and surfaced rather than silently resolved - see
GUNA_VARIANTS and UNRESOLVED_IN_SOURCE at the end of the file.
"""

from __future__ import annotations

from typing import Any, Literal

Lang = Literal["en", "bn", "hi"]

# Index order used throughout the codebase: 0 = Aries ... 11 = Pisces
SIGN_ORDER = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]

# --------------------------------------------------------------------------------------
# Sign names. name_hi was previously Latin transliteration ("Mesha") in a field the
# Hindi UI renders directly; the Devanagari forms are given here. [01], [12R]
# --------------------------------------------------------------------------------------
SIGN_NAMES: list[dict[str, str]] = [
    {"en": "Aries", "sa": "Mesha", "bn": "মেষ", "hi": "मेष"},
    {"en": "Taurus", "sa": "Vrisha", "bn": "বৃষ", "hi": "वृष"},
    {"en": "Gemini", "sa": "Mithuna", "bn": "মিথুন", "hi": "मिथुन"},
    {"en": "Cancer", "sa": "Karka", "bn": "কর্কট", "hi": "कर्क"},
    {"en": "Leo", "sa": "Simha", "bn": "সিংহ", "hi": "सिंह"},
    {"en": "Virgo", "sa": "Kanya", "bn": "কন্যা", "hi": "कन्या"},
    {"en": "Libra", "sa": "Tula", "bn": "তুলা", "hi": "तुला"},
    {"en": "Scorpio", "sa": "Vrischika", "bn": "বৃশ্চিক", "hi": "वृश्चिक"},
    {"en": "Sagittarius", "sa": "Dhanu", "bn": "ধনু", "hi": "धनु"},
    {"en": "Capricorn", "sa": "Makara", "bn": "মকর", "hi": "मकर"},
    {"en": "Aquarius", "sa": "Kumbha", "bn": "কুম্ভ", "hi": "कुम्भ"},
    {"en": "Pisces", "sa": "Meena", "bn": "মীন", "hi": "मीन"},
]

# --------------------------------------------------------------------------------------
# Shared value vocabulary. Each key maps to the three display languages so a
# classification value is translated once and reused across all twelve signs.
# --------------------------------------------------------------------------------------
VOCAB: dict[str, dict[str, str]] = {
    # Quality / gender
    "odd": {"en": "Odd / Male (Vishama)", "bn": "বিষম / পুরুষ রাশি", "hi": "विषम / पुरुष राशि"},
    "even": {"en": "Even / Female (Sama)", "bn": "সম / স্ত্রী রাশি", "hi": "सम / स्त्री राशि"},
    # Triplicity
    "fire": {"en": "Fiery (Agni)", "bn": "অগ্নি রাশি", "hi": "अग्नि राशि"},
    "earth": {"en": "Earthy (Bhoo)", "bn": "পৃথ্বী রাশি", "hi": "पृथ्वी राशि"},
    "air": {"en": "Airy (Vaayu)", "bn": "বায়ু রাশি", "hi": "वायु राशि"},
    "water": {"en": "Watery (Jala)", "bn": "জল রাশি", "hi": "जल राशि"},
    # Quadruplicity
    "movable": {"en": "Movable / Cardinal (Chara)", "bn": "চর রাশি", "hi": "चर राशि"},
    "fixed": {"en": "Fixed / Static (Sthira)", "bn": "স্থির রাশি", "hi": "स्थिर राशि"},
    "dual": {"en": "Dual / Common (Dwiswabhava)", "bn": "দ্বিস্বভাব রাশি", "hi": "द्विस्वभाव राशि"},
    # Fruitfulness
    "fruitful": {"en": "Fruitful", "bn": "ফলপ্রসূ", "hi": "फलदायी"},
    "semi_fruitful": {"en": "Semi-fruitful", "bn": "অর্ধ-ফলপ্রসূ", "hi": "अर्ध-फलदायी"},
    "barren": {"en": "Barren / Sterile", "bn": "বন্ধ্যা", "hi": "बंध्य"},
    # Voice
    "voice": {"en": "Voice sign", "bn": "শব্দকারী রাশি", "hi": "शब्दकारी राशि"},
    "mute": {"en": "Mute / Dumb sign", "bn": "মূক রাশি", "hi": "मूक राशि"},
    "voice_neutral": {"en": "Neither voice nor mute", "bn": "শব্দকারী বা মূক নয়", "hi": "शब्दकारी या मूक नहीं"},
    # Violence
    "violent": {"en": "Violent sign", "bn": "হিংস্র রাশি", "hi": "हिंस्र राशि"},
    "not_violent": {"en": "Not a violent sign", "bn": "হিংস্র রাশি নয়", "hi": "हिंस्र राशि नहीं"},
    # Form
    "quadruped": {"en": "Quadruped / Bestial (Chatushpada)", "bn": "চতুষ্পদ রাশি", "hi": "चतुष्पद राशि"},
    "human": {"en": "Human / Biped (Dwipada)", "bn": "দ্বিপদ / মানব রাশি", "hi": "द्विपद / मानव राशि"},
    "keeta": {"en": "Keeta (Insect)", "bn": "কীট রাশি", "hi": "कीट राशि"},
    "watery_form": {"en": "Watery (Jalachara)", "bn": "জলচর রাশি", "hi": "जलचर राशि"},
    "inanimate": {"en": "Inanimate (Scales)", "bn": "জড় প্রতীক (দাঁড়িপাল্লা)", "hi": "निर्जीव प्रतीक (तुला)"},
    "half_human_half_quad": {
        "en": "First half human, second half quadruped",
        "bn": "প্রথমার্ধ মানব, দ্বিতীয়ার্ধ চতুষ্পদ",
        "hi": "प्रथमार्ध मानव, द्वितीयार्ध चतुष्पद",
    },
    "half_quad_half_watery": {
        "en": "First half quadruped, second half watery",
        "bn": "প্রথমার্ধ চতুষ্পদ, দ্বিতীয়ার্ধ জলচর",
        "hi": "प्रथमार्ध चतुष्पद, द्वितीयार्ध जलचर",
    },
    # Double bodied
    "double_bodied": {"en": "Double-bodied / Bicorporeal", "bn": "দ্বিশরীরী রাশি", "hi": "द्विशरीरी राशि"},
    "single_bodied": {"en": "Single-bodied", "bn": "একশরীরী রাশি", "hi": "एकशरीरी राशि"},
    # Ascension
    "long_asc": {"en": "Long ascension", "bn": "দীর্ঘোদয় রাশি", "hi": "दीर्घोदय राशि"},
    "short_asc": {"en": "Short ascension", "bn": "স্বল্পোদয় রাশি", "hi": "अल्पोदय राशि"},
    # Hemisphere
    "northern": {"en": "Northern sign", "bn": "উত্তর রাশি", "hi": "उत्तर राशि"},
    "southern": {"en": "Southern sign", "bn": "দক্ষিণ রাশি", "hi": "दक्षिण राशि"},
    # Equinoctial / tropical
    "vernal_equinox": {"en": "Vernal equinoctial sign", "bn": "বসন্ত বিষুব রাশি", "hi": "वसंत विषुव राशि"},
    "autumnal_equinox": {"en": "Autumnal equinoctial sign", "bn": "শারদ বিষুব রাশি", "hi": "शरद विषुव राशि"},
    "summer_solstice": {"en": "Tropical - summer solstice sign", "bn": "কর্কটক্রান্তি (গ্রীষ্ম অয়নান্ত)", "hi": "कर्क संक्रांति (ग्रीष्म अयनांत)"},
    "winter_solstice": {"en": "Tropical - winter solstice sign", "bn": "মকরক্রান্তি (শীত অয়নান্ত)", "hi": "मकर संक्रांति (शीत अयनांत)"},
    "not_equinoctial": {"en": "Neither equinoctial nor tropical", "bn": "বিষুব বা অয়নান্ত রাশি নয়", "hi": "विषुव या अयनांत राशि नहीं"},
    # Dosha
    "pitta": {"en": "Pitta (Bilious)", "bn": "পিত্ত প্রকৃতি", "hi": "पित्त प्रकृति"},
    "vaata": {"en": "Vaata (Windy)", "bn": "বাত প্রকৃতি", "hi": "वात प्रकृति"},
    "kapha": {"en": "Kapha (Phlegmatic)", "bn": "কফ প্রকৃতি", "hi": "कफ प्रकृति"},
    "mixed_dosha": {
        "en": "Mixed - Bile, Wind and Phlegm",
        "bn": "মিশ্র - পিত্ত, বাত ও কফ",
        "hi": "मिश्र - पित्त, वात एवं कफ",
    },
    # Varna
    "brahmin": {"en": "Brahmana (Scholar / Priest)", "bn": "ব্রাহ্মণ", "hi": "ब्राह्मण"},
    "kshatriya": {"en": "Kshatriya (Warrior)", "bn": "ক্ষত্রিয়", "hi": "क्षत्रिय"},
    "vaishya": {"en": "Vaishya (Trader)", "bn": "বৈশ্য", "hi": "वैश्य"},
    "shudra": {"en": "Shudra (Worker)", "bn": "শূদ্র", "hi": "शूद्र"},
    # Day / night
    "nishaa": {"en": "Night sign (Nishaa) - strong at night", "bn": "নিশা রাশি - রাত্রিতে বলবান", "hi": "निशा राशि - रात्रि में बलवान"},
    "divaa": {"en": "Day sign (Divaa) - strong by day", "bn": "দিবা রাশি - দিবাভাগে বলবান", "hi": "दिवा राशि - दिन में बलवान"},
    # Rising
    "seershodaya": {"en": "Seershodaya (rises head first)", "bn": "শীর্ষোদয় রাশি", "hi": "शीर्षोदय राशि"},
    "prishthodaya": {"en": "Prishthodaya (rises feet first)", "bn": "পৃষ্ঠোদয় রাশি", "hi": "पृष्ठोदय राशि"},
    "ubhayodaya": {"en": "Ubhayodaya (rises head and feet)", "bn": "উভয়োদয় রাশি", "hi": "उभयोदय राशि"},
    # Footedness
    "odd_footed": {"en": "Odd-footed (Vishamapada)", "bn": "বিষমপদ রাশি", "hi": "विषमपद राशि"},
    "even_footed": {"en": "Even-footed (Samapada)", "bn": "সমপদ রাশি", "hi": "समपद राशि"},
    # Directions
    "east": {"en": "East (Agni)", "bn": "পূর্ব", "hi": "पूर्व"},
    "south": {"en": "South (Prithvi)", "bn": "দক্ষিণ", "hi": "दक्षिण"},
    "west": {"en": "West (Vayu)", "bn": "পশ্চিম", "hi": "पश्चिम"},
    "north": {"en": "North (Jal)", "bn": "উত্তর", "hi": "उत्तर"},
    # Guna
    "sattvik": {"en": "Sattvik", "bn": "সাত্ত্বিক", "hi": "सात्विक"},
    "rajasik": {"en": "Rajasik", "bn": "রাজসিক", "hi": "राजसिक"},
    "tamasik": {"en": "Tamasik", "bn": "তামসিক", "hi": "तामसिक"},
}

# --------------------------------------------------------------------------------------
# Group metadata. `source` cites the client file and page the group came from.
# `definition` is the client's own stated definition, condensed.
# `application` is the client's own stated predictive use, where they gave one.
# --------------------------------------------------------------------------------------
GROUPS: list[dict[str, Any]] = [
    {
        "key": "quality",
        "label": {"en": "Quality / Gender", "bn": "গুণ / লিঙ্গ", "hi": "गुण / लिंग"},
        "source": "01.pdf p.5",
        "definition": {
            "en": "Odd signs are male (vishama/oja rasi), even signs are female (sama/yugma rasi). Male signs tend to be extrovert, pushy, assertive and dominating; female signs calm, intuitive, nurturing, protective, quiet, introverted, gentle and emotional.",
            "bn": "বিষম রাশি পুরুষ (বিষম/ওজ রাশি), সম রাশি স্ত্রী (সম/যুগ্ম রাশি)। পুরুষ রাশি বহির্মুখী, আগ্রাসী, দৃঢ় ও প্রভাবশালী; স্ত্রী রাশি শান্ত, সহজবোধ্য, পালক, রক্ষাকারী, নীরব, অন্তর্মুখী, কোমল ও ভাবপ্রবণ।",
            "hi": "विषम राशियाँ पुरुष (विषम/ओज राशि), सम राशियाँ स्त्री (सम/युग्म राशि) होती हैं। पुरुष राशियाँ बहिर्मुखी, आग्रही, दृढ़ एवं प्रभावशाली; स्त्री राशियाँ शांत, सहजबोधी, पालक, रक्षक, मौन, अंतर्मुखी, कोमल एवं भावुक होती हैं।",
        },
    },
    {
        "key": "triplicity",
        "label": {"en": "Triplicity (Element)", "bn": "ত্রিকোণ (তত্ত্ব)", "hi": "त्रिकोण (तत्व)"},
        "source": "01.pdf p.6-7",
        "definition": {
            "en": "Fire, earth, air and water, three signs each; the fifth element aakaasa (ether) is present in every rasi. The client calls this 'one of the most important classifications for predictive purpose'.",
            "bn": "অগ্নি, পৃথ্বী, বায়ু ও জল - প্রতিটিতে তিনটি রাশি; পঞ্চম তত্ত্ব আকাশ প্রতিটি রাশিতেই বিদ্যমান। ক্লায়েন্টের নথি অনুসারে এটি 'ভবিষ্যদ্বাণীর জন্য সর্বাপেক্ষা গুরুত্বপূর্ণ শ্রেণিবিভাগ'।",
            "hi": "अग्नि, पृथ्वी, वायु एवं जल - प्रत्येक में तीन राशियाँ; पंचम तत्व आकाश प्रत्येक राशि में विद्यमान है। क्लाइंट के दस्तावेज़ अनुसार यह 'भविष्यकथन हेतु सर्वाधिक महत्वपूर्ण वर्गीकरण' है।",
        },
        "application": {
            "en": "The 10th house shows career. A fiery 10th can indicate work near a furnace or factory; a watery 10th can indicate the merchant navy.",
            "bn": "দশম ভাব কর্মজীবন নির্দেশ করে। অগ্নি রাশির দশম ভাব চুল্লি বা কারখানার কাজ নির্দেশ করতে পারে; জল রাশির দশম ভাব বাণিজ্য নৌবহর নির্দেশ করতে পারে।",
            "hi": "दशम भाव कर्मजीवन दर्शाता है। अग्नि राशि का दशम भाव भट्टी या कारखाने का कार्य दर्शा सकता है; जल राशि का दशम भाव व्यापारिक नौसेना दर्शा सकता है।",
        },
    },
    {
        "key": "quadruplicity",
        "label": {"en": "Quadruplicity (Mode)", "bn": "চতুষ্কোণ (স্বভাব)", "hi": "चतुष्कोण (स्वभाव)"},
        "source": "01.pdf p.3-4",
        "definition": {
            "en": "Movable (chara) signs are ruled by Brahma the Creator and are enterprising, outgoing and reform-seeking; negatively restless and overactive. Fixed (sthira) signs are ruled by Shiva the Destroyer and are focused, determined and persistent; negatively stubborn and resistant to change. Dual (dwiswabhava) signs are ruled by Vishnu the Sustainer and are adaptable, flexible and learning-oriented; negatively fluctuating and indecisive.",
            "bn": "চর রাশির অধিপতি সৃষ্টিকর্তা ব্রহ্মা - উদ্যমী, বহির্মুখী ও সংস্কারপ্রিয়; নেতিবাচক দিকে অস্থির ও অতিসক্রিয়। স্থির রাশির অধিপতি সংহারকর্তা শিব - একনিষ্ঠ, দৃঢ়সংকল্প ও অধ্যবসায়ী; নেতিবাচক দিকে একগুঁয়ে ও পরিবর্তনবিমুখ। দ্বিস্বভাব রাশির অধিপতি পালনকর্তা বিষ্ণু - অনুকূলনীয়, নমনীয় ও শিক্ষাপ্রিয়; নেতিবাচক দিকে দোদুল্যমান ও সিদ্ধান্তহীন।",
            "hi": "चर राशि के अधिपति सृष्टिकर्ता ब्रह्मा - उद्यमी, बहिर्मुखी एवं सुधारप्रिय; नकारात्मक रूप में अस्थिर एवं अतिसक्रिय। स्थिर राशि के अधिपति संहारकर्ता शिव - एकनिष्ठ, दृढ़संकल्पी एवं अध्यवसायी; नकारात्मक रूप में हठी एवं परिवर्तनविमुख। द्विस्वभाव राशि के अधिपति पालनकर्ता विष्णु - अनुकूलनीय, लचीले एवं शिक्षाप्रिय; नकारात्मक रूप में डगमगाते एवं निर्णयहीन।",
        },
    },
    {
        "key": "fruitfulness",
        "label": {"en": "Fruitful / Barren", "bn": "ফলপ্রসূ / বন্ধ্যা", "hi": "फलदायी / बंध्य"},
        "source": "01.pdf p.10",
        "definition": {
            "en": "All watery signs - Cancer, Scorpio and Pisces - are fruitful. Aries, Gemini, Leo and Virgo are barren or sterile. The remaining four are semi-fruitful.",
            "bn": "সমস্ত জল রাশি - কর্কট, বৃশ্চিক ও মীন - ফলপ্রসূ। মেষ, মিথুন, সিংহ ও কন্যা বন্ধ্যা। অবশিষ্ট চারটি অর্ধ-ফলপ্রসূ।",
            "hi": "समस्त जल राशियाँ - कर्क, वृश्चिक एवं मीन - फलदायी हैं। मेष, मिथुन, सिंह एवं कन्या बंध्य हैं। शेष चार अर्ध-फलदायी हैं।",
        },
        "application": {
            "en": "A fruitful sign on the 5th cusp, with no affliction to the cusp or its lord and with Jupiter in the natal horoscope, indicates several children, the number depending on the strength of the houses and planets concerned. A barren sign with an afflicted 5th house and lord indicates childlessness.",
            "bn": "পঞ্চম ভাবের সন্ধিস্থলে ফলপ্রসূ রাশি, সেই সন্ধি বা তার অধিপতি অপীড়িত এবং জন্মকুণ্ডলীতে বৃহস্পতি থাকলে বহু সন্তান নির্দেশ করে; সংখ্যা সংশ্লিষ্ট ভাব ও গ্রহের বলের উপর নির্ভরশীল। বন্ধ্যা রাশির সঙ্গে পীড়িত পঞ্চম ভাব ও অধিপতি সন্তানহীনতা নির্দেশ করে।",
            "hi": "पंचम भाव की संधि पर फलदायी राशि, संधि अथवा उसके अधिपति पर कोई पीड़ा न हो तथा जन्मकुंडली में बृहस्पति हो, तो अनेक संतान का संकेत; संख्या संबंधित भावों एवं ग्रहों के बल पर निर्भर। बंध्य राशि के साथ पीड़ित पंचम भाव एवं अधिपति संतानहीनता दर्शाते हैं।",
        },
    },
    {
        "key": "voice",
        "label": {"en": "Voice / Mute", "bn": "শব্দকারী / মূক", "hi": "शब्दकारी / मूक"},
        "source": "01.pdf p.10-11",
        "definition": {
            "en": "The airy signs Gemini, Libra and Aquarius are voice signs, because sound requires an airy medium. The watery signs Cancer, Scorpio and Pisces are mute signs, because water is not a good medium for sound.",
            "bn": "বায়ু রাশি মিথুন, তুলা ও কুম্ভ শব্দকারী রাশি, কারণ শব্দের জন্য বায়বীয় মাধ্যম প্রয়োজন। জল রাশি কর্কট, বৃশ্চিক ও মীন মূক রাশি, কারণ জল শব্দের উত্তম মাধ্যম নয়।",
            "hi": "वायु राशियाँ मिथुन, तुला एवं कुम्भ शब्दकारी हैं, क्योंकि ध्वनि हेतु वायवीय माध्यम आवश्यक है। जल राशियाँ कर्क, वृश्चिक एवं मीन मूक हैं, क्योंकि जल ध्वनि का उत्तम माध्यम नहीं।",
        },
        "application": {
            "en": "A voice sign on the 2nd house with Venus placed in it suggests a voice suitable for singing; the same in the 10th house suggests a career using the voice - singer, ventriloquist, commentator, mimicry artist. A watery sign on an afflicted ascendant or 2nd house, or Mercury afflicted by Saturn in these signs, can cause speech problems, stammering or other speech impediments.",
            "bn": "দ্বিতীয় ভাবে শব্দকারী রাশি ও সেখানে শুক্র থাকলে গানের উপযোগী কণ্ঠ নির্দেশ করে; দশম ভাবে একই যোগ কণ্ঠনির্ভর পেশা নির্দেশ করে - গায়ক, ভেন্ট্রিলোকুইস্ট, ভাষ্যকার, মিমিক্রি শিল্পী। পীড়িত লগ্ন বা দ্বিতীয় ভাবে জল রাশি, অথবা এই রাশিতে শনি কর্তৃক পীড়িত বুধ, বাক্‌সমস্যা, তোতলামি বা অন্য বাক্‌প্রতিবন্ধকতা ঘটাতে পারে।",
            "hi": "द्वितीय भाव में शब्दकारी राशि तथा वहाँ शुक्र हो तो गायन योग्य कंठ; दशम भाव में वही योग कंठ-आधारित पेशा दर्शाता है - गायक, वेंट्रिलोक्विस्ट, भाष्यकार, मिमिक्री कलाकार। पीड़ित लग्न अथवा द्वितीय भाव में जल राशि, अथवा इन राशियों में शनि से पीड़ित बुध, वाणी दोष, हकलाना अथवा अन्य वाक्-बाधा उत्पन्न कर सकता है।",
        },
    },
    {
        "key": "violent",
        "label": {"en": "Violent Signs", "bn": "হিংস্র রাশি", "hi": "हिंस्र राशि"},
        "source": "01.pdf p.11",
        "definition": {
            "en": "Aries and Scorpio are violent signs. These signs know no fear, are full of courage and confidence and are eager to take risk. Aries is violent on the physical level, Scorpio on the emotional level.",
            "bn": "মেষ ও বৃশ্চিক হিংস্র রাশি। এই রাশি ভয় জানে না, সাহস ও আত্মবিশ্বাসে পূর্ণ এবং ঝুঁকি নিতে উৎসুক। মেষ শারীরিক স্তরে হিংস্র, বৃশ্চিক আবেগিক স্তরে।",
            "hi": "मेष एवं वृश्चिक हिंस्र राशियाँ हैं। ये राशियाँ भय नहीं जानतीं, साहस एवं आत्मविश्वास से पूर्ण तथा जोखिम लेने को उत्सुक हैं। मेष भौतिक स्तर पर हिंस्र, वृश्चिक भावनात्मक स्तर पर।",
        },
    },
    {
        "key": "form",
        "label": {"en": "Bestial / Human / Keeta", "bn": "চতুষ্পদ / মানব / কীট", "hi": "चतुष्पद / मानव / कीट"},
        "source": "01.pdf p.10-11",
        "definition": {
            "en": "Aries (Ram), Taurus (Bull), Leo (Lion), Capricorn (Goat) and the second half of Sagittarius are symbolised by animal figures and are called bestial or four-legged. Gemini (Twins), Virgo (Virgin), Aquarius (Water bearer) and the first half of Sagittarius (Centaur) are human signs. Cancer, Pisces and the later half of Capricorn are watery. Scorpio is keeta (insect). Libra is neither, being represented by a non-living thing, the Scales.",
            "bn": "মেষ (ভেড়া), বৃষ (বৃষভ), সিংহ, মকর (ছাগ) এবং ধনুর দ্বিতীয়ার্ধ পশুমূর্তিতে প্রতীকায়িত, তাই চতুষ্পদ। মিথুন (যুগল), কন্যা, কুম্ভ (জলবাহক) এবং ধনুর প্রথমার্ধ (কিন্নর) মানব রাশি। কর্কট, মীন এবং মকরের শেষার্ধ জলচর। বৃশ্চিক কীট। তুলা কোনোটিই নয়, কারণ তার প্রতীক একটি জড় বস্তু - দাঁড়িপাল্লা।",
            "hi": "मेष (मेढ़ा), वृष (वृषभ), सिंह, मकर (बकरा) तथा धनु का द्वितीयार्ध पशु आकृतियों से प्रतीकित हैं, अतः चतुष्पद। मिथुन (युगल), कन्या, कुम्भ (जलवाहक) तथा धनु का प्रथमार्ध (किन्नर) मानव राशियाँ हैं। कर्क, मीन तथा मकर का उत्तरार्ध जलचर। वृश्चिक कीट। तुला कोई भी नहीं, क्योंकि उसका प्रतीक निर्जीव वस्तु - तुला दंड है।",
        },
    },
    {
        "key": "double_bodied",
        "label": {"en": "Double-bodied", "bn": "দ্বিশরীরী", "hi": "द्विशरीरी"},
        "source": "01.pdf p.12",
        "definition": {
            "en": "Gemini, Sagittarius and Pisces are double-bodied, dual or bicorporeal signs, because of their 'double' symbols - the Twins, the part-human part-horse Centaur, and the two Fishes. Virgo was included in this category but is not any more in modern times.",
            "bn": "মিথুন, ধনু ও মীন দ্বিশরীরী বা দ্বৈত রাশি, কারণ এদের প্রতীক 'দ্বৈত' - যুগল, অর্ধমানব-অর্ধঅশ্ব কিন্নর, এবং দুটি মৎস্য। কন্যা পূর্বে এই শ্রেণিতে ছিল, আধুনিক কালে আর নয়।",
            "hi": "मिथुन, धनु एवं मीन द्विशरीरी अथवा द्वैत राशियाँ हैं, क्योंकि उनके प्रतीक 'द्वैत' हैं - युगल, अर्धमानव-अर्धअश्व किन्नर, तथा दो मत्स्य। कन्या पूर्व में इस श्रेणी में थी, आधुनिक काल में नहीं।",
        },
        "application": {
            "en": "A double-bodied sign on the cusp of the 7th house can indicate two marriages, and on the cusp of the 5th house can indicate the birth of twins.",
            "bn": "সপ্তম ভাবের সন্ধিস্থলে দ্বিশরীরী রাশি দুটি বিবাহ নির্দেশ করতে পারে, এবং পঞ্চম ভাবের সন্ধিস্থলে যমজ সন্তানের জন্ম নির্দেশ করতে পারে।",
            "hi": "सप्तम भाव की संधि पर द्विशरीरी राशि दो विवाह दर्शा सकती है, तथा पंचम भाव की संधि पर जुड़वाँ संतान का जन्म दर्शा सकती है।",
        },
    },
    {
        "key": "ascension",
        "label": {"en": "Long / Short Ascension", "bn": "দীর্ঘোদয় / স্বল্পোদয়", "hi": "दीर्घोदय / अल्पोदय"},
        "source": "01.pdf p.12-13",
        "definition": {
            "en": "The 23.4 degree slant of the Earth's axis causes signs to take different times to rise over the horizon, particularly at middle latitudes. In the northern hemisphere the signs of long ascension are Cancer, Leo, Virgo, Libra, Scorpio and Sagittarius, the longest being Virgo and Libra. The signs of short ascension are Capricorn, Aquarius, Pisces, Aries, Taurus and Gemini, the shortest being Pisces and Aries. The classification reverses in the southern hemisphere.",
            "bn": "পৃথিবীর অক্ষের ২৩.৪ ডিগ্রি হেলানো অবস্থানের কারণে বিভিন্ন রাশি দিগন্তে উঠতে ভিন্ন সময় নেয়, বিশেষত মধ্য অক্ষাংশে। উত্তর গোলার্ধে দীর্ঘোদয় রাশি কর্কট, সিংহ, কন্যা, তুলা, বৃশ্চিক ও ধনু - দীর্ঘতম কন্যা ও তুলা। স্বল্পোদয় রাশি মকর, কুম্ভ, মীন, মেষ, বৃষ ও মিথুন - স্বল্পতম মীন ও মেষ। দক্ষিণ গোলার্ধে এই শ্রেণিবিভাগ বিপরীত হয়।",
            "hi": "पृथ्वी के अक्ष के 23.4 डिग्री झुकाव के कारण विभिन्न राशियाँ क्षितिज पर उदय होने में भिन्न समय लेती हैं, विशेषतः मध्य अक्षांशों पर। उत्तरी गोलार्ध में दीर्घोदय राशियाँ कर्क, सिंह, कन्या, तुला, वृश्चिक एवं धनु - दीर्घतम कन्या एवं तुला। अल्पोदय राशियाँ मकर, कुम्भ, मीन, मेष, वृष एवं मिथुन - अल्पतम मीन एवं मेष। दक्षिणी गोलार्ध में यह वर्गीकरण विपरीत होता है।",
        },
    },
    {
        "key": "hemisphere",
        "label": {"en": "Northern / Southern", "bn": "উত্তর / দক্ষিণ রাশি", "hi": "उत्तर / दक्षिण राशि"},
        "source": "01.pdf p.5",
        "definition": {
            "en": "The first six signs, Aries to Virgo, lie north of the celestial equator and are called northern signs. The remaining six, Libra to Pisces, lie south of the celestial equator and are termed southern signs.",
            "bn": "প্রথম ছয় রাশি, মেষ থেকে কন্যা, খগোলীয় বিষুবরেখার উত্তরে অবস্থিত, তাই উত্তর রাশি। অবশিষ্ট ছয়, তুলা থেকে মীন, বিষুবরেখার দক্ষিণে অবস্থিত, তাই দক্ষিণ রাশি।",
            "hi": "प्रथम छह राशियाँ, मेष से कन्या, खगोलीय विषुवत रेखा के उत्तर में स्थित हैं, अतः उत्तर राशियाँ। शेष छह, तुला से मीन, विषुवत रेखा के दक्षिण में स्थित हैं, अतः दक्षिण राशियाँ।",
        },
    },
    {
        "key": "equinoctial_tropical",
        "label": {"en": "Equinoctial / Tropical", "bn": "বিষুব / অয়নান্ত রাশি", "hi": "विषुव / अयनांत राशि"},
        "source": "01.pdf p.10, p.12",
        "definition": {
            "en": "Equinoctial means equal day and night, occurring around 21 March and 23 September when the Sun is directly over the equator. Aries is the vernal equinoctial sign and Libra the autumnal. Cancer and Capricorn are the two tropical signs, the summer and winter solstice signs respectively.",
            "bn": "বিষুব মানে সমান দিন ও রাত, যা ঘটে ২১ মার্চ ও ২৩ সেপ্টেম্বর নাগাদ, যখন সূর্য ঠিক বিষুবরেখার উপরে থাকে। মেষ বসন্ত বিষুব রাশি এবং তুলা শারদ বিষুব রাশি। কর্কট ও মকর দুটি অয়নান্ত রাশি - যথাক্রমে গ্রীষ্ম ও শীত অয়নান্ত।",
            "hi": "विषुव का अर्थ समान दिन-रात, जो 21 मार्च एवं 23 सितम्बर के आसपास होता है, जब सूर्य ठीक विषुवत रेखा के ऊपर रहता है। मेष वसंत विषुव राशि एवं तुला शरद विषुव राशि। कर्क एवं मकर दो अयनांत राशियाँ - क्रमशः ग्रीष्म एवं शीत अयनांत।",
        },
    },
    {
        "key": "dosha",
        "label": {"en": "Dosha (Pitta / Vaata / Kapha)", "bn": "দোষ (পিত্ত / বাত / কফ)", "hi": "दोष (पित्त / वात / कफ)"},
        "source": "01.pdf p.8",
        "definition": {
            "en": "Pitta or bilious nature combines fire and water and shows transformation from one state to another - in the body, digestion. Vaata or windy nature combines air and ether and shows what moves in and out of a system - in the body, breathing. Kapha or phlegmatic nature combines earth and water and shows what binds a system together and gives it structure - in the body, bones, muscles and fat.",
            "bn": "পিত্ত প্রকৃতি অগ্নি ও জলের সংযোগ, যা এক অবস্থা থেকে অন্য অবস্থায় রূপান্তর নির্দেশ করে - দেহে, পাচন। বাত প্রকৃতি বায়ু ও আকাশের সংযোগ, যা তন্ত্রে প্রবেশ ও নির্গমন নির্দেশ করে - দেহে, শ্বাসক্রিয়া। কফ প্রকৃতি পৃথ্বী ও জলের সংযোগ, যা তন্ত্রকে বন্ধন ও গঠন দেয় - দেহে, অস্থি, পেশি ও মেদ।",
            "hi": "पित्त प्रकृति अग्नि एवं जल का संयोग, जो एक अवस्था से दूसरी में रूपांतरण दर्शाती है - शरीर में, पाचन। वात प्रकृति वायु एवं आकाश का संयोग, जो तंत्र में प्रवेश एवं निर्गमन दर्शाती है - शरीर में, श्वसन। कफ प्रकृति पृथ्वी एवं जल का संयोग, जो तंत्र को बांधती एवं संरचना देती है - शरीर में, अस्थि, मांसपेशी एवं मेद।",
        },
    },
    {
        "key": "varna",
        "label": {"en": "Varna (Class)", "bn": "বর্ণ", "hi": "वर्ण"},
        "source": "01.pdf p.9",
        "definition": {
            "en": "Four varnas classified by karma or work. Brahmanas pursue knowledge and work as priests or ministers - watery signs. Kshatriyas are warriors, kings, army chiefs and soldiers - fiery signs. Vaishyas are traders and suppliers of services - earthy signs. Shudras execute physical tasks - airy signs.",
            "bn": "কর্ম অনুসারে চার বর্ণ। ব্রাহ্মণ জ্ঞানান্বেষী, পুরোহিত বা মন্ত্রী - জল রাশি। ক্ষত্রিয় যোদ্ধা, রাজা, সেনাপতি ও সৈনিক - অগ্নি রাশি। বৈশ্য ব্যবসায়ী ও সেবা সরবরাহকারী - পৃথ্বী রাশি। শূদ্র শারীরিক কর্ম সম্পাদনকারী - বায়ু রাশি।",
            "hi": "कर्म अनुसार चार वर्ण। ब्राह्मण ज्ञानान्वेषी, पुरोहित अथवा मंत्री - जल राशियाँ। क्षत्रिय योद्धा, राजा, सेनापति एवं सैनिक - अग्नि राशियाँ। वैश्य व्यापारी एवं सेवा प्रदाता - पृथ्वी राशियाँ। शूद्र शारीरिक कार्य करने वाले - वायु राशियाँ।",
        },
    },
    {
        "key": "day_night",
        "label": {"en": "Day / Night Strength", "bn": "দিবা / নিশা বল", "hi": "दिवा / निशा बल"},
        "source": "01.pdf p.8-9 (stated twice)",
        "definition": {
            "en": "Aries, Taurus, Gemini, Cancer, Sagittarius and Capricorn are nishaa rasis - strong during the night. Leo, Virgo, Libra, Scorpio, Aquarius and Pisces are divaa rasis - strong during the day. Of the two rasis owned by a planet, one is a day sign and one a night sign. The Moon governs all the nishaa rasis and the Sun all the divaa rasis. Day runs from sunrise to sunset, night from sunset to sunrise.",
            "bn": "মেষ, বৃষ, মিথুন, কর্কট, ধনু ও মকর নিশা রাশি - রাত্রিতে বলবান। সিংহ, কন্যা, তুলা, বৃশ্চিক, কুম্ভ ও মীন দিবা রাশি - দিবাভাগে বলবান। একটি গ্রহের অধীন দুই রাশির একটি দিবা ও একটি নিশা রাশি। চন্দ্র সমস্ত নিশা রাশির এবং সূর্য সমস্ত দিবা রাশির অধিপতি। দিন সূর্যোদয় থেকে সূর্যাস্ত, রাত্রি সূর্যাস্ত থেকে সূর্যোদয়।",
            "hi": "मेष, वृष, मिथुन, कर्क, धनु एवं मकर निशा राशियाँ हैं - रात्रि में बलवान। सिंह, कन्या, तुला, वृश्चिक, कुम्भ एवं मीन दिवा राशियाँ हैं - दिन में बलवान। एक ग्रह की दो राशियों में एक दिवा एवं एक निशा राशि होती है। चंद्र समस्त निशा राशियों एवं सूर्य समस्त दिवा राशियों का अधिपति है। दिन सूर्योदय से सूर्यास्त, रात्रि सूर्यास्त से सूर्योदय तक।",
        },
    },
    {
        "key": "rising",
        "label": {"en": "Mode of Rising", "bn": "উদয় প্রকার", "hi": "उदय प्रकार"},
        "source": "01.pdf p.9-10",
        "definition": {
            "en": "Some rasis rise with their head - Seershodaya: Gemini, Leo, Virgo, Libra, Scorpio, Aquarius. Some rise with their feet - Prishthodaya: Aries, Taurus, Cancer, Sagittarius, Capricorn. Pisces rises with both head and feet.",
            "bn": "কিছু রাশি মাথা দিয়ে উদিত হয় - শীর্ষোদয়: মিথুন, সিংহ, কন্যা, তুলা, বৃশ্চিক, কুম্ভ। কিছু পা দিয়ে উদিত হয় - পৃষ্ঠোদয়: মেষ, বৃষ, কর্কট, ধনু, মকর। মীন মাথা ও পা উভয় দিয়েই উদিত হয়।",
            "hi": "कुछ राशियाँ सिर से उदय होती हैं - शीर्षोदय: मिथुन, सिंह, कन्या, तुला, वृश्चिक, कुम्भ। कुछ पैर से उदय होती हैं - पृष्ठोदय: मेष, वृष, कर्क, धनु, मकर। मीन सिर एवं पैर दोनों से उदय होती है।",
        },
        "application": {
            "en": "Planets in Seershodaya rasis give their results in the first half of their dasas; planets in Prishthodaya rasis give their results in the second half.",
            "bn": "শীর্ষোদয় রাশিতে অবস্থিত গ্রহ তাদের দশার প্রথমার্ধে ফল দেয়; পৃষ্ঠোদয় রাশিতে অবস্থিত গ্রহ দ্বিতীয়ার্ধে ফল দেয়।",
            "hi": "शीर्षोदय राशियों में स्थित ग्रह अपनी दशा के प्रथमार्ध में फल देते हैं; पृष्ठोदय राशियों में स्थित ग्रह द्वितीयार्ध में फल देते हैं।",
        },
    },
    {
        "key": "footedness",
        "label": {"en": "Odd / Even Footed", "bn": "বিষমপদ / সমপদ", "hi": "विषमपद / समपद"},
        "source": "01.pdf p.5",
        "definition": {
            "en": "Aries, Taurus, Gemini, Libra, Scorpio and Sagittarius are odd-footed (vishamapada / ojapada) rasis. Cancer, Leo, Virgo, Capricorn, Aquarius and Pisces are even-footed (samapada / yugmapada) rasis. This division is used in some dasas.",
            "bn": "মেষ, বৃষ, মিথুন, তুলা, বৃশ্চিক ও ধনু বিষমপদ (ওজপদ) রাশি। কর্কট, সিংহ, কন্যা, মকর, কুম্ভ ও মীন সমপদ (যুগ্মপদ) রাশি। এই বিভাজন কিছু দশায় ব্যবহৃত হয়।",
            "hi": "मेष, वृष, मिथुन, तुला, वृश्चिक एवं धनु विषमपद (ओजपद) राशियाँ हैं। कर्क, सिंह, कन्या, मकर, कुम्भ एवं मीन समपद (युग्मपद) राशियाँ हैं। यह विभाजन कुछ दशाओं में प्रयुक्त होता है।",
        },
    },
    {
        "key": "direction",
        "label": {"en": "Direction", "bn": "দিক", "hi": "दिशा"},
        "source": "01.pdf p.8-9",
        "definition": {
            "en": "Aries, Leo and Sagittarius show east (Agni). Taurus, Virgo and Capricorn show south (Prithvi). Gemini, Libra and Aquarius show west (Vayu). Cancer, Scorpio and Pisces show north (Jal).",
            "bn": "মেষ, সিংহ ও ধনু পূর্ব দিক (অগ্নি) নির্দেশ করে। বৃষ, কন্যা ও মকর দক্ষিণ (পৃথ্বী)। মিথুন, তুলা ও কুম্ভ পশ্চিম (বায়ু)। কর্কট, বৃশ্চিক ও মীন উত্তর (জল)।",
            "hi": "मेष, सिंह एवं धनु पूर्व दिशा (अग्नि) दर्शाते हैं। वृष, कन्या एवं मकर दक्षिण (पृथ्वी)। मिथुन, तुला एवं कुम्भ पश्चिम (वायु)। कर्क, वृश्चिक एवं मीन उत्तर (जल)।",
        },
        "application": {
            "en": "Mostly used to decide from which direction the bride or groom will come, and in which direction a person has gone, will go, or will be transferred.",
            "bn": "মূলত কোন দিক থেকে পাত্র বা পাত্রী আসবে, এবং কোন দিকে ব্যক্তি গিয়েছে, যাবে বা বদলি হবে তা নির্ণয়ে ব্যবহৃত হয়।",
            "hi": "मुख्यतः किस दिशा से वर अथवा वधू आएगी, तथा किस दिशा में व्यक्ति गया है, जाएगा अथवा स्थानांतरित होगा, यह निर्णय करने हेतु प्रयुक्त।",
        },
    },
    {
        "key": "colour",
        "label": {"en": "Rasi Colour", "bn": "রাশির বর্ণ", "hi": "राशि का रंग"},
        "source": "01.pdf p.11-12",
        "definition": {
            "en": "The colour attributed to each rasi in the client's document. This is the sign's own colour, which is distinct from a lucky or favourable colour.",
            "bn": "ক্লায়েন্টের নথিতে প্রতিটি রাশির জন্য নির্দিষ্ট বর্ণ। এটি রাশির নিজস্ব বর্ণ, শুভ বা অনুকূল বর্ণ থেকে পৃথক।",
            "hi": "क्लाइंट के दस्तावेज़ में प्रत्येक राशि हेतु निर्दिष्ट रंग। यह राशि का स्वयं का रंग है, शुभ अथवा अनुकूल रंग से भिन्न।",
        },
    },
    {
        "key": "kalapurusha",
        "label": {"en": "Kalapurusha Body Part", "bn": "কালপুরুষ অঙ্গ", "hi": "कालपुरुष अंग"},
        "source": "01.pdf p.9",
        "definition": {
            "en": "The body of the Kalapurusha mapped onto the zodiac: Aries is the head, Taurus the face, Gemini the arms, Cancer the heart, Leo the stomach, Virgo the hip, Libra the space below the navel, Scorpio the private parts, Sagittarius the thighs, Capricorn the knees, Aquarius the ankles, Pisces the feet.",
            "bn": "রাশিচক্রে কালপুরুষের দেহ: মেষ মস্তক, বৃষ মুখ, মিথুন বাহু, কর্কট হৃদয়, সিংহ উদর, কন্যা নিতম্ব, তুলা নাভির নিম্নাংশ, বৃশ্চিক গুহ্যাঙ্গ, ধনু ঊরু, মকর জানু, কুম্ভ গুল্ফ, মীন পদ।",
            "hi": "राशिचक्र में कालपुरुष का शरीर: मेष मस्तक, वृष मुख, मिथुन बाहु, कर्क हृदय, सिंह उदर, कन्या कटि, तुला नाभि के नीचे का भाग, वृश्चिक गुह्यांग, धनु जंघा, मकर जानु, कुम्भ गुल्फ, मीन पाद।",
        },
        "application": {
            "en": "Look to the relevant sign when analysing a body part - Aries for head problems, headaches and head injury, Pisces for problems of the feet, and so on.",
            "bn": "কোনো অঙ্গ বিশ্লেষণে সংশ্লিষ্ট রাশি দেখতে হয় - মস্তকের সমস্যা, মাথাব্যথা ও মাথায় আঘাতের জন্য মেষ, পায়ের সমস্যার জন্য মীন, ইত্যাদি।",
            "hi": "किसी अंग के विश्लेषण हेतु संबंधित राशि देखें - मस्तक की समस्या, सिरदर्द एवं सिर की चोट हेतु मेष, पाँव की समस्या हेतु मीन, इत्यादि।",
        },
    },
]

# --------------------------------------------------------------------------------------
# Per-sign assignments. Each row is transcribed from 01.pdf page 2 (the per-sign
# attribute lines) cross-checked against the group lists on pages 3-13. Where the
# two disagree the group lists win, because they are stated explicitly and in full.
# --------------------------------------------------------------------------------------
_A: list[dict[str, str]] = [
    # 0 Aries - "Odd, Fiery, Movable, Barren, Violent, Quadruped, Short ascension,
    #            Male, Bilious, Forest, Hilly Areas, Head, Brain."
    {
        "quality": "odd", "triplicity": "fire", "quadruplicity": "movable",
        "fruitfulness": "barren", "voice": "voice_neutral", "violent": "violent",
        "form": "quadruped", "double_bodied": "single_bodied", "ascension": "short_asc",
        "hemisphere": "northern", "equinoctial_tropical": "vernal_equinox",
        "dosha": "pitta", "varna": "kshatriya", "day_night": "nishaa",
        "rising": "prishthodaya", "footedness": "odd_footed", "direction": "east",
    },
    # 1 Taurus - "Even, Earthy, Fixed, Semi Fruitful, Quadruped, Short ascension,
    #             Female, Windy, Agricultural Land, Face, Eyes."
    {
        "quality": "even", "triplicity": "earth", "quadruplicity": "fixed",
        "fruitfulness": "semi_fruitful", "voice": "voice_neutral", "violent": "not_violent",
        "form": "quadruped", "double_bodied": "single_bodied", "ascension": "short_asc",
        "hemisphere": "northern", "equinoctial_tropical": "not_equinoctial",
        "dosha": "vaata", "varna": "vaishya", "day_night": "nishaa",
        "rising": "prishthodaya", "footedness": "odd_footed", "direction": "south",
    },
    # 2 Gemini - "Odd, Airy, Dual, Barren, Human, Double-bodied, Voice,
    #             Short ascension, Male, Bile Wind and Phlegm, Bedroom, Throat,
    #             Shoulder, Arms, Lungs."
    {
        "quality": "odd", "triplicity": "air", "quadruplicity": "dual",
        "fruitfulness": "barren", "voice": "voice", "violent": "not_violent",
        "form": "human", "double_bodied": "double_bodied", "ascension": "short_asc",
        "hemisphere": "northern", "equinoctial_tropical": "not_equinoctial",
        "dosha": "mixed_dosha", "varna": "shudra", "day_night": "nishaa",
        "rising": "seershodaya", "footedness": "odd_footed", "direction": "west",
    },
    # 3 Cancer - "Even, Watery, Movable, Fruitful, Mute, Long ascension, Female,
    #             Phlegm, Chasm with water, Chest."
    {
        "quality": "even", "triplicity": "water", "quadruplicity": "movable",
        "fruitfulness": "fruitful", "voice": "mute", "violent": "not_violent",
        "form": "watery_form", "double_bodied": "single_bodied", "ascension": "long_asc",
        "hemisphere": "northern", "equinoctial_tropical": "summer_solstice",
        "dosha": "kapha", "varna": "brahmin", "day_night": "nishaa",
        "rising": "prishthodaya", "footedness": "even_footed", "direction": "north",
    },
    # 4 Leo - "Odd, Fiery, Fixed, Barren, Human, Long ascension, Male, Bilious,
    #          Forest, Heart, Upper Abdomen."
    {
        "quality": "odd", "triplicity": "fire", "quadruplicity": "fixed",
        "fruitfulness": "barren", "voice": "voice_neutral", "violent": "not_violent",
        "form": "quadruped", "double_bodied": "single_bodied", "ascension": "long_asc",
        "hemisphere": "northern", "equinoctial_tropical": "not_equinoctial",
        "dosha": "pitta", "varna": "kshatriya", "day_night": "divaa",
        "rising": "seershodaya", "footedness": "even_footed", "direction": "east",
    },
    # 5 Virgo - "Even, Earthy, Dual, Barren, Human, Long ascension, Female, Windy,
    #            Mountain, Lower Abdomen, Spleen."
    {
        "quality": "even", "triplicity": "earth", "quadruplicity": "dual",
        "fruitfulness": "barren", "voice": "voice_neutral", "violent": "not_violent",
        "form": "human", "double_bodied": "single_bodied", "ascension": "long_asc",
        "hemisphere": "northern", "equinoctial_tropical": "not_equinoctial",
        "dosha": "vaata", "varna": "vaishya", "day_night": "divaa",
        "rising": "seershodaya", "footedness": "even_footed", "direction": "south",
    },
    # 6 Libra - "Odd, Airy, Movable, Semi Fruitful, Voice, Long ascension, Male,
    #            Bile Wind and Phlegm, Entertainment Places, Genitalia, Kidney."
    {
        "quality": "odd", "triplicity": "air", "quadruplicity": "movable",
        "fruitfulness": "semi_fruitful", "voice": "voice", "violent": "not_violent",
        "form": "inanimate", "double_bodied": "single_bodied", "ascension": "long_asc",
        "hemisphere": "southern", "equinoctial_tropical": "autumnal_equinox",
        "dosha": "mixed_dosha", "varna": "shudra", "day_night": "divaa",
        "rising": "seershodaya", "footedness": "odd_footed", "direction": "west",
    },
    # 7 Scorpio - "Even, Watery, Fixed, Fruitful, Mute, Violent, Centiped,
    #              Long ascension, Female, Phlegm, Underground, Excretory Organs."
    {
        "quality": "even", "triplicity": "water", "quadruplicity": "fixed",
        "fruitfulness": "fruitful", "voice": "mute", "violent": "violent",
        "form": "keeta", "double_bodied": "single_bodied", "ascension": "long_asc",
        "hemisphere": "southern", "equinoctial_tropical": "not_equinoctial",
        "dosha": "kapha", "varna": "brahmin", "day_night": "divaa",
        "rising": "seershodaya", "footedness": "odd_footed", "direction": "north",
    },
    # 8 Sagittarius - "Odd, Fiery, Dual, Semi Fruitful, Double-bodied,
    #                  Quadruped (Second Half), Long ascension, Male, Bilious,
    #                  Military Places, Thighs, Liver."
    {
        "quality": "odd", "triplicity": "fire", "quadruplicity": "dual",
        "fruitfulness": "semi_fruitful", "voice": "voice_neutral", "violent": "not_violent",
        "form": "half_human_half_quad", "double_bodied": "double_bodied",
        "ascension": "long_asc", "hemisphere": "southern",
        "equinoctial_tropical": "not_equinoctial", "dosha": "pitta",
        "varna": "kshatriya", "day_night": "nishaa", "rising": "prishthodaya",
        "footedness": "odd_footed", "direction": "east",
    },
    # 9 Capricorn - "Even, Earthy, Movable, Semi Fruitful, Quadruped,
    #                Short ascension, Female, Windy, Watery, Knee."
    {
        "quality": "even", "triplicity": "earth", "quadruplicity": "movable",
        "fruitfulness": "semi_fruitful", "voice": "voice_neutral", "violent": "not_violent",
        "form": "half_quad_half_watery", "double_bodied": "single_bodied",
        "ascension": "short_asc", "hemisphere": "southern",
        "equinoctial_tropical": "winter_solstice", "dosha": "vaata",
        "varna": "vaishya", "day_night": "nishaa", "rising": "prishthodaya",
        "footedness": "even_footed", "direction": "south",
    },
    # 10 Aquarius - "Odd, Airy, Fixed, Human, Voice, Short ascension, Male,
    #                Bile Wind and Phlegm, Porter House, Shin."
    # 01.pdf omits a fruitfulness term for Aquarius; the group lists on p.10 place it
    # in neither the fruitful nor the barren set, so it falls in the remaining class.
    {
        "quality": "odd", "triplicity": "air", "quadruplicity": "fixed",
        "fruitfulness": "semi_fruitful", "voice": "voice", "violent": "not_violent",
        "form": "human", "double_bodied": "single_bodied", "ascension": "short_asc",
        "hemisphere": "southern", "equinoctial_tropical": "not_equinoctial",
        "dosha": "mixed_dosha", "varna": "shudra", "day_night": "divaa",
        "rising": "seershodaya", "footedness": "even_footed", "direction": "west",
    },
    # 11 Pisces - "Even, Watery, Dual, Fruitful, Mute, Double-Bodied, Centiped,
    #              Short ascension, Female, Phlegm, Sea, Feet."
    {
        "quality": "even", "triplicity": "water", "quadruplicity": "dual",
        "fruitfulness": "fruitful", "voice": "mute", "violent": "not_violent",
        "form": "watery_form", "double_bodied": "double_bodied", "ascension": "short_asc",
        "hemisphere": "southern", "equinoctial_tropical": "not_equinoctial",
        "dosha": "kapha", "varna": "brahmin", "day_night": "divaa",
        "rising": "ubhayodaya", "footedness": "even_footed", "direction": "north",
    },
]

# Rasi colours, 01.pdf p.11-12, verbatim.
COLOURS: list[dict[str, str]] = [
    {"en": "Blood red", "bn": "রক্তলাল", "hi": "रक्त लाल"},
    {"en": "White", "bn": "সাদা", "hi": "श्वेत"},
    {"en": "Grass green", "bn": "ঘাসের সবুজ", "hi": "घास जैसा हरा"},
    {"en": "Pale red", "bn": "ফ্যাকাশে লাল", "hi": "हल्का लाल"},
    {"en": "White", "bn": "সাদা", "hi": "श्वेत"},
    {"en": "Variegated", "bn": "চিত্রবিচিত্র", "hi": "चित्र-विचित्र"},
    {"en": "Black", "bn": "কালো", "hi": "काला"},
    {"en": "Reddish brown", "bn": "লালচে বাদামি", "hi": "लालिमायुक्त भूरा"},
    {"en": "Colour of the husk of grass", "bn": "ঘাসের তুষের বর্ণ", "hi": "घास की भूसी का रंग"},
    {"en": "Variegated", "bn": "চিত্রবিচিত্র", "hi": "चित्र-विचित्र"},
    {"en": "Brown", "bn": "বাদামি", "hi": "भूरा"},
    {"en": "Colour of fish", "bn": "মৎস্যবর্ণ", "hi": "मत्स्य वर्ण"},
]

# Kalapurusha body part, 01.pdf p.9, verbatim.
KALAPURUSHA: list[dict[str, str]] = [
    {"en": "Head", "bn": "মস্তক", "hi": "मस्तक"},
    {"en": "Face", "bn": "মুখ", "hi": "मुख"},
    {"en": "Arms", "bn": "বাহু", "hi": "बाहु"},
    {"en": "Heart", "bn": "হৃদয়", "hi": "हृदय"},
    {"en": "Stomach", "bn": "উদর", "hi": "उदर"},
    {"en": "Hip", "bn": "নিতম্ব", "hi": "कटि"},
    {"en": "Space below the navel", "bn": "নাভির নিম্নাংশ", "hi": "नाभि के नीचे का भाग"},
    {"en": "Private parts", "bn": "গুহ্যাঙ্গ", "hi": "गुह्यांग"},
    {"en": "Thighs", "bn": "ঊরু", "hi": "जंघा"},
    {"en": "Knees", "bn": "জানু", "hi": "जानु"},
    {"en": "Ankles", "bn": "গুল্ফ", "hi": "गुल्फ"},
    {"en": "Feet", "bn": "পদ", "hi": "पाद"},
]

# Detailed body parts as listed per sign on 01.pdf p.2, which goes beyond the single
# Kalapurusha limb. Verbatim, in the document's own order.
BODY_PARTS_DETAIL: list[dict[str, str]] = [
    {"en": "Head, brain", "bn": "মস্তক, মস্তিষ্ক", "hi": "मस्तक, मस्तिष्क"},
    {"en": "Face, eyes, fine teeth", "bn": "মুখ, চক্ষু, সুগঠিত দন্ত", "hi": "मुख, नेत्र, सुगठित दंत"},
    {"en": "Throat, shoulder, arms, lungs, chest", "bn": "কণ্ঠ, স্কন্ধ, বাহু, ফুসফুস, বক্ষ", "hi": "कंठ, स्कंध, बाहु, फुफ्फुस, वक्ष"},
    {"en": "Chest, heart, breast", "bn": "বক্ষ, হৃদয়, স্তন", "hi": "वक्ष, हृदय, स्तन"},
    {"en": "Heart, upper abdomen, stomach, digestion, navel", "bn": "হৃদয়, ঊর্ধ্ব উদর, পাকস্থলী, পাচন, নাভি", "hi": "हृदय, ऊर्ध्व उदर, जठर, पाचन, नाभि"},
    {"en": "Lower abdomen, spleen, hip, appendix", "bn": "নিম্ন উদর, প্লীহা, নিতম্ব, অ্যাপেন্ডিক্স", "hi": "निम्न उदर, प्लीहा, कटि, अपेंडिक्स"},
    {"en": "Genitalia, kidney, groins", "bn": "জননাঙ্গ, বৃক্ক, কুঁচকি", "hi": "जननांग, वृक्क, जांघ-मूल"},
    {"en": "Excretory organs, private parts", "bn": "মলাশয়, গুহ্যাঙ্গ", "hi": "उत्सर्जन अंग, गुह्यांग"},
    {"en": "Thighs, liver", "bn": "ঊরু, যকৃৎ", "hi": "जंघा, यकृत"},
    {"en": "Knees", "bn": "জানু", "hi": "जानु"},
    {"en": "Shin, ankles", "bn": "জঙ্ঘা, গুল্ফ", "hi": "पिंडली, गुल्फ"},
    {"en": "Feet", "bn": "পদ", "hi": "पाद"},
]

# Places and significations per sign, 01.pdf p.2 and [RCT]. These are the KP-style
# place significations; the client lists them inline with the physical traits.
PLACES: list[dict[str, list[str]]] = [
    {
        "en": ["Forest", "Hilly areas"],
        "bn": ["অরণ্য", "পাহাড়ি অঞ্চল"],
        "hi": ["वन", "पहाड़ी क्षेत्र"],
    },
    {
        "en": ["Agricultural land", "Meadows", "Plains", "Luxury halls", "Dining halls", "Eating places"],
        "bn": ["কৃষিভূমি", "তৃণভূমি", "সমতল", "বিলাসকক্ষ", "ভোজনকক্ষ", "আহারস্থল"],
        "hi": ["कृषि भूमि", "घास के मैदान", "समतल", "विलास कक्ष", "भोजन कक्ष", "आहार स्थल"],
    },
    {
        "en": ["Bedroom", "Garden", "Schools", "Colleges", "Study rooms", "Cables", "Telephone", "Newspapers"],
        "bn": ["শয়নকক্ষ", "উদ্যান", "বিদ্যালয়", "মহাবিদ্যালয়", "পাঠকক্ষ", "তার", "দূরভাষ", "সংবাদপত্র"],
        "hi": ["शयनकक्ष", "उद्यान", "विद्यालय", "महाविद्यालय", "अध्ययन कक्ष", "तार", "दूरभाष", "समाचार पत्र"],
    },
    {
        "en": ["Chasm with water", "Watery fields", "Rivers", "Canals", "Kitchen", "Food"],
        "bn": ["জলপূর্ণ গহ্বর", "জলাভূমি", "নদী", "খাল", "রন্ধনশালা", "খাদ্য"],
        "hi": ["जलयुक्त गर्त", "जलक्षेत्र", "नदियाँ", "नहरें", "रसोई", "भोजन"],
    },
    {
        "en": ["Mountains", "Forests", "Caves", "Deserts", "Palaces", "Parks", "Forts", "Boilers", "Steel factories"],
        "bn": ["পর্বত", "অরণ্য", "গুহা", "মরুভূমি", "প্রাসাদ", "উদ্যান", "দুর্গ", "বয়লার", "ইস্পাত কারখানা"],
        "hi": ["पर्वत", "वन", "गुफाएँ", "रेगिस्तान", "महल", "उद्यान", "किले", "बॉयलर", "इस्पात कारखाने"],
    },
    {
        "en": ["Mountain", "Lush gardens", "Fields", "Orchards", "Libraries", "Bookstores", "Farms"],
        "bn": ["পর্বত", "সুসজ্জিত উদ্যান", "ক্ষেত", "ফলবাগান", "গ্রন্থাগার", "পুস্তকবিপণি", "খামার"],
        "hi": ["पर्वत", "हरे-भरे उद्यान", "खेत", "फलोद्यान", "पुस्तकालय", "पुस्तक भंडार", "कृषि फार्म"],
    },
    {
        "en": ["Entertainment places", "Markets", "Trade centres", "Banks", "Hotels", "Amusement parks", "Toilets", "Cosmetics"],
        "bn": ["বিনোদনস্থল", "বাজার", "বাণিজ্যকেন্দ্র", "ব্যাংক", "হোটেল", "আনন্দ উদ্যান", "শৌচাগার", "প্রসাধনী"],
        "hi": ["मनोरंजन स्थल", "बाज़ार", "व्यापार केंद्र", "बैंक", "होटल", "मनोरंजन पार्क", "शौचालय", "प्रसाधन सामग्री"],
    },
    {
        "en": ["Underground", "Holes", "Deep caves", "Mines", "Garages"],
        "bn": ["ভূগর্ভ", "গর্ত", "গভীর গুহা", "খনি", "গ্যারাজ"],
        "hi": ["भूगर्भ", "गड्ढे", "गहरी गुफाएँ", "खदानें", "गैराज"],
    },
    {
        "en": ["Military places", "Government offices", "Aircraft"],
        "bn": ["সামরিক স্থান", "সরকারি কার্যালয়", "বিমান"],
        "hi": ["सैन्य स्थान", "सरकारी कार्यालय", "वायुयान"],
    },
    {
        "en": ["Marsh lands", "Watery places", "Bushes"],
        "bn": ["জলাভূমি", "জলময় স্থান", "ঝোপঝাড়"],
        "hi": ["दलदली भूमि", "जलयुक्त स्थान", "झाड़ियाँ"],
    },
    {
        "en": ["Porter house", "Mountain spring", "Places with water", "Charity", "Philosophy"],
        "bn": ["দ্বাররক্ষীগৃহ", "পার্বত্য নির্ঝর", "জলময় স্থান", "দানকর্ম", "দর্শনশাস্ত্র"],
        "hi": ["द्वारपाल गृह", "पर्वतीय झरना", "जलयुक्त स्थान", "दान कर्म", "दर्शनशास्त्र"],
    },
    {
        "en": ["Sea", "Oceans", "Prisons", "Hospitals", "Hermitages"],
        "bn": ["সমুদ্র", "মহাসাগর", "কারাগার", "হাসপাতাল", "আশ্রম"],
        "hi": ["समुद्र", "महासागर", "कारागार", "अस्पताल", "आश्रम"],
    },
]

# Per-sign trait keywords, 01.pdf p.2 and [RCT], verbatim and in the document's order.
TRAIT_KEYWORDS: list[dict[str, list[str]]] = [
    {
        "en": ["Dynamic", "Enterprising", "Valiant", "Ruddy", "Large forehead", "Hasty", "Impulsive", "Restless", "Thick eyebrows", "Leadership", "Overbearing", "Dry", "Lean", "Tall"],
        "bn": ["গতিশীল", "উদ্যোগী", "বীর", "রক্তিম", "প্রশস্ত ললাট", "দ্রুতগামী", "আবেগপ্রবণ", "অস্থির", "ঘন ভ্রূ", "নেতৃত্বগুণ", "প্রভাবপ্রবণ", "শুষ্ক", "কৃশ", "দীর্ঘদেহী"],
        "hi": ["गतिशील", "उद्यमी", "वीर", "रक्तिम", "विस्तृत ललाट", "शीघ्रगामी", "आवेगी", "अस्थिर", "घनी भौंहें", "नेतृत्व गुण", "प्रभावी", "शुष्क", "कृश", "दीर्घदेही"],
    },
    {
        "en": ["Beautiful face", "Stable", "Sluggish", "Loyal", "Fine teeth", "Large eyes", "Luxurious", "Faithful", "Thick hair", "Stout"],
        "bn": ["সুন্দর মুখশ্রী", "স্থিতিশীল", "মন্দগতি", "অনুগত", "সুগঠিত দন্ত", "বড় চোখ", "বিলাসপ্রিয়", "বিশ্বস্ত", "ঘন কেশ", "স্থূলদেহী"],
        "hi": ["सुंदर मुखाकृति", "स्थिर", "मंदगति", "निष्ठावान", "सुगठित दंत", "बड़े नेत्र", "विलासप्रिय", "विश्वसनीय", "घने केश", "स्थूलदेही"],
    },
    {
        "en": ["Communication", "Journalism", "Tall", "Well-built", "Prominent cheeks", "Thick hair", "Broad chest", "Curious", "Learned", "Jovial"],
        "bn": ["সংযোগ ও ভাষণ", "সাংবাদিকতা", "দীর্ঘদেহী", "সুগঠিত", "উন্নত গণ্ডদেশ", "ঘন কেশ", "প্রশস্ত বক্ষ", "কৌতূহলী", "বিদ্বান", "প্রফুল্ল"],
        "hi": ["संवाद एवं वाणी", "पत्रकारिता", "दीर्घदेही", "सुगठित", "उन्नत कपोल", "घने केश", "विस्तृत वक्ष", "जिज्ञासु", "विद्वान", "प्रसन्नचित्त"],
    },
    {
        "en": ["Attractive", "Small build", "Emotional", "Deeply attached", "Mother-like", "Sensitive"],
        "bn": ["আকর্ষণীয়", "ছোট গড়ন", "ভাবপ্রবণ", "গভীর আসক্তিসম্পন্ন", "মাতৃসুলভ", "সংবেদনশীল"],
        "hi": ["आकर्षक", "लघु गठन", "भावुक", "गहन आसक्तियुक्त", "मातृसुलभ", "संवेदनशील"],
    },
    {
        "en": ["Thin", "Dry", "Hot", "Royal", "Self-pride", "Insolent", "Domineering"],
        "bn": ["কৃশ", "শুষ্ক", "উষ্ণ", "রাজকীয়", "আত্মগরিমা", "উদ্ধত", "আধিপত্যপ্রবণ"],
        "hi": ["कृश", "शुष्क", "उष्ण", "राजसी", "आत्मगौरव", "उद्धत", "आधिपत्यप्रिय"],
    },
    {
        "en": ["Intelligent", "Sharp", "Orator", "Nervous", "Physically weak", "Discretion", "Tactfulness"],
        "bn": ["বুদ্ধিমান", "তীক্ষ্ণ", "বাগ্মী", "স্নায়বিক", "শারীরিকভাবে দুর্বল", "বিবেচনাবোধ", "কৌশলপরায়ণ"],
        "hi": ["बुद्धिमान", "तीक्ष्ण", "वक्ता", "स्नायविक", "शारीरिक रूप से दुर्बल", "विवेक", "कुशलता"],
    },
    {
        "en": ["Businessmen", "Balanced", "Wise in nature", "Good conversationalist", "Good talker"],
        "bn": ["ব্যবসায়ী", "সুসন্তুলিত", "প্রকৃতিগতভাবে বিজ্ঞ", "সুবক্তা", "ভালো আলাপী"],
        "hi": ["व्यापारी", "संतुलित", "स्वभावतः विज्ञ", "सुवक्ता", "अच्छा वार्ताकार"],
    },
    {
        "en": ["Small build", "Dusky complexion", "Bright eyes", "Secretive", "Scheming", "Occult", "Best friend or a worst enemy", "Peevish", "Sensitive"],
        "bn": ["ছোট গড়ন", "শ্যামবর্ণ", "উজ্জ্বল চোখ", "গোপনপ্রবণ", "কূটবুদ্ধি", "গুহ্যবিদ্যা", "পরম মিত্র বা পরম শত্রু", "খিটখিটে", "সংবেদনশীল"],
        "hi": ["लघु गठन", "श्याम वर्ण", "उज्ज्वल नेत्र", "गोपनप्रिय", "कूटनीतिक", "गूढ़ विद्या", "परम मित्र अथवा परम शत्रु", "चिड़चिड़ा", "संवेदनशील"],
    },
    {
        "en": ["Royal", "Attorneys", "Sparse hair", "Muscular body", "Deep eyes", "Upright", "Honest", "Genial", "Gambler"],
        "bn": ["রাজকীয়", "আইনজীবী", "পাতলা কেশ", "পেশিবহুল দেহ", "গভীর চোখ", "সরলচিত্ত", "সৎ", "সহৃদয়", "দ্যূতপ্রিয়"],
        "hi": ["राजसी", "अधिवक्ता", "विरल केश", "मांसल शरीर", "गहरे नेत्र", "सरल", "ईमानदार", "सौहार्दपूर्ण", "द्यूतप्रिय"],
    },
    {
        "en": ["Slender build", "Long neck", "Prominent teeth", "Witty", "Perfectionist", "Patient", "Organizer", "Cautious", "Secretive", "Pragmatic"],
        "bn": ["ক্ষীণ গড়ন", "দীর্ঘ গ্রীবা", "উন্নত দন্ত", "রসবোধসম্পন্ন", "নিখুঁততাপ্রিয়", "ধৈর্যশীল", "সংগঠক", "সতর্ক", "গোপনপ্রবণ", "বাস্তববাদী"],
        "hi": ["क्षीण गठन", "दीर्घ ग्रीवा", "उन्नत दंत", "विनोदी", "पूर्णतावादी", "धैर्यवान", "संगठक", "सतर्क", "गोपनप्रिय", "व्यवहारिक"],
    },
    {
        "en": ["Tall", "Bony", "Small eyes", "Ill-formed teeth", "Coarse hair", "Hard-working", "Stoic", "Honest", "Straightforward"],
        "bn": ["দীর্ঘদেহী", "অস্থিসার", "ছোট চোখ", "অসুগঠিত দন্ত", "রুক্ষ কেশ", "পরিশ্রমী", "নির্বিকার", "সৎ", "স্পষ্টবাদী"],
        "hi": ["दीर्घदेही", "अस्थिल", "छोटे नेत्र", "असुगठित दंत", "रूखे केश", "परिश्रमी", "निर्विकार", "ईमानदार", "स्पष्टवादी"],
    },
    {
        "en": ["Short structure", "Plump", "Large eyes", "Large eyebrows", "Lethargic", "Emotional", "Timid", "Honest", "Irresolute", "Talkative", "Intuitive"],
        "bn": ["খর্বাকৃতি", "স্থূল", "বড় চোখ", "ঘন ভ্রূ", "অলস", "ভাবপ্রবণ", "ভীরু", "সৎ", "সিদ্ধান্তহীন", "বাচাল", "সহজবোধসম্পন্ন"],
        "hi": ["लघु कद", "स्थूल", "बड़े नेत्र", "घनी भौंहें", "आलसी", "भावुक", "भीरु", "ईमानदार", "अनिर्णीत", "वाचाल", "सहजबोधी"],
    },
]

# Sign lords, [12R] verbatim. Traditional lords only - the client's table assigns
# Saturn to Aquarius and Mars to Scorpio, with no modern outer-planet rulerships.
SIGN_LORDS = [
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter",
]

# --------------------------------------------------------------------------------------
# The client's document states the Guna classification twice, and the two statements
# disagree for six of the twelve signs. Both are preserved verbatim. The API returns
# both, flagged, rather than picking one - see UNRESOLVED_IN_SOURCE.
# --------------------------------------------------------------------------------------
GUNA_VARIANTS: dict[str, Any] = {
    "page_5": {
        "source": "01.pdf p.5",
        "sattvik": ["Cancer", "Leo", "Sagittarius", "Pisces"],
        "rajasik": ["Taurus", "Gemini", "Virgo", "Libra"],
        "tamasik": ["Aries", "Scorpio", "Capricorn", "Aquarius"],
        "note": {
            "en": "This statement adds that sattvik signs are the houses ruled by Sun, Moon and Jupiter, rajasik those ruled by Mercury and Venus, and tamasik those ruled by Mars and Saturn.",
            "bn": "এই বিবৃতিতে আরও বলা হয়েছে সাত্ত্বিক রাশি সূর্য, চন্দ্র ও বৃহস্পতির অধীন, রাজসিক বুধ ও শুক্রের অধীন, এবং তামসিক মঙ্গল ও শনির অধীন।",
            "hi": "इस कथन में यह भी कहा गया है कि सात्विक राशियाँ सूर्य, चंद्र एवं बृहस्पति के अधीन, राजसिक बुध एवं शुक्र के अधीन, तथा तामसिक मंगल एवं शनि के अधीन हैं।",
        },
    },
    "page_8": {
        "source": "01.pdf p.8",
        "sattvik": ["Cancer", "Leo", "Sagittarius", "Pisces"],
        "rajasik": ["Aries", "Taurus", "Libra", "Scorpio"],
        "tamasik": ["Gemini", "Virgo", "Capricorn", "Aquarius"],
        "note": {
            "en": "This statement gives no planetary rationale.",
            "bn": "এই বিবৃতিতে কোনো গ্রহভিত্তিক যুক্তি দেওয়া হয়নি।",
            "hi": "इस कथन में कोई ग्रह-आधारित तर्क नहीं दिया गया है।",
        },
    },
}

UNRESOLVED_IN_SOURCE: list[dict[str, Any]] = [
    {
        "key": "guna",
        "severity": "blocking",
        "summary": {
            "en": "The client's 01.pdf states the Guna (sattvik / rajasik / tamasik) classification twice, on page 5 and page 8, and the two lists disagree for Aries, Gemini, Virgo and Scorpio. Four of twelve signs are affected; the other eight are classified identically in both statements. Both readings are returned below, unresolved, until the client confirms which is authoritative.",
            "bn": "ক্লায়েন্টের 01.pdf নথিতে গুণ (সাত্ত্বিক / রাজসিক / তামসিক) শ্রেণিবিভাগ দুইবার - পৃষ্ঠা ৫ ও পৃষ্ঠা ৮-এ - উল্লিখিত, এবং মেষ, মিথুন, কন্যা ও বৃশ্চিকের ক্ষেত্রে দুটি তালিকা পরস্পরবিরোধী। বারোটির মধ্যে চারটি রাশি প্রভাবিত; বাকি আটটি উভয় বিবৃতিতেই একইভাবে শ্রেণিবদ্ধ। ক্লায়েন্ট কোনটি চূড়ান্ত তা নিশ্চিত না করা পর্যন্ত উভয় পাঠই অমীমাংসিত অবস্থায় দেওয়া হল।",
            "hi": "क्लाइंट के 01.pdf में गुण (सात्विक / राजसिक / तामसिक) वर्गीकरण दो बार - पृष्ठ 5 एवं पृष्ठ 8 पर - दिया गया है, तथा मेष, मिथुन, कन्या एवं वृश्चिक हेतु दोनों सूचियाँ परस्पर विरोधी हैं। बारह में से चार राशियाँ प्रभावित हैं; शेष आठ दोनों कथनों में समान रूप से वर्गीकृत हैं। क्लाइंट द्वारा प्रामाणिक सूची की पुष्टि होने तक दोनों पाठ अनिर्णीत रूप में प्रस्तुत हैं।",
        },
    },
]

# --------------------------------------------------------------------------------------
# The five basic rules of the KP system, [KPB] p.1, verbatim.
# --------------------------------------------------------------------------------------
KP_BASIC_RULES: list[dict[str, str]] = [
    {
        "en": "Other significators also promise and the nakshatra gives the result.",
        "bn": "অন্যান্য কারকও প্রতিশ্রুতি দেয় এবং নক্ষত্র ফল প্রদান করে।",
        "hi": "अन्य कारक भी वचन देते हैं तथा नक्षत्र फल प्रदान करता है।",
    },
    {
        "en": "The 12th house from any house negates the results of that house.",
        "bn": "যেকোনো ভাব থেকে দ্বাদশ ভাব সেই ভাবের ফল নষ্ট করে।",
        "hi": "किसी भी भाव से द्वादश भाव उस भाव के फल को नष्ट करता है।",
    },
    {
        "en": "Results are not decided by one house but by a group of houses.",
        "bn": "ফল একটি ভাব দ্বারা নয়, ভাবসমষ্টি দ্বারা নির্ধারিত হয়।",
        "hi": "फल एक भाव से नहीं, भाव-समूह से निर्धारित होता है।",
    },
    {
        "en": "The sub-lord of a planet qualifies the result of that planet.",
        "bn": "গ্রহের সাব-লর্ড সেই গ্রহের ফল নির্ধারণ করে।",
        "hi": "ग्रह का सब-लॉर्ड उस ग्रह के फल को निर्धारित करता है।",
    },
    {
        "en": "The cuspal sub-lord tells whether the event is promised or not.",
        "bn": "ভাবসন্ধির সাব-লর্ড নির্দেশ করে ঘটনাটি প্রতিশ্রুত কিনা।",
        "hi": "भाव संधि का सब-लॉर्ड बताता है कि घटना वचनबद्ध है अथवा नहीं।",
    },
]

# The twelve house significations, [KPB] p.3-4, verbatim.
KP_HOUSE_SIGNIFICATIONS: list[dict[str, str]] = [
    {"en": "Birth, head, physical body, limb, physical features, livelihood", "bn": "জন্ম, মস্তক, দেহ, অঙ্গ, শারীরিক বৈশিষ্ট্য, জীবিকা", "hi": "जन्म, मस्तक, शरीर, अंग, शारीरिक लक्षण, जीविका"},
    {"en": "Wealth, food, right eye, what one eats or drinks, face, eye, speech, family, property", "bn": "ধন, খাদ্য, ডান চক্ষু, ভোজ্য ও পেয়, মুখ, চক্ষু, বাক্য, পরিবার, সম্পত্তি", "hi": "धन, भोजन, दायाँ नेत्र, खाद्य-पेय, मुख, नेत्र, वाणी, परिवार, संपत्ति"},
    {"en": "Courage, firmness, bad thoughts, breast, ear - especially the right ear, prowess, younger brother or sister, heroism, mental strength", "bn": "সাহস, দৃঢ়তা, কুচিন্তা, বক্ষ, কর্ণ - বিশেষত ডান কর্ণ, পরাক্রম, কনিষ্ঠ ভ্রাতা বা ভগিনী, বীরত্ব, মানসিক বল", "hi": "साहस, दृढ़ता, कुविचार, वक्ष, कर्ण - विशेषतः दायाँ कर्ण, पराक्रम, छोटा भाई अथवा बहन, वीरता, मानसिक बल"},
    {"en": "House, home, land, relation, mother, vehicle, happiness, water, learning", "bn": "গৃহ, বাসস্থান, ভূমি, আত্মীয়তা, মাতা, বাহন, সুখ, জল, বিদ্যা", "hi": "गृह, निवास, भूमि, संबंध, माता, वाहन, सुख, जल, विद्या"},
    {"en": "Intellect, children, son, belly, traditional law, virtuous acts previously done", "bn": "বুদ্ধি, সন্তান, পুত্র, উদর, পরম্পরাগত বিধি, পূর্বকৃত পুণ্যকর্ম", "hi": "बुद्धि, संतान, पुत्र, उदर, परंपरागत विधि, पूर्वकृत पुण्यकर्म"},
    {"en": "Debt, wounds, disease, enemy, sin, a wicked act, fear, humiliation", "bn": "ঋণ, ক্ষত, রোগ, শত্রু, পাপ, কুকর্ম, ভয়, অপমান", "hi": "ऋण, घाव, रोग, शत्रु, पाप, कुकर्म, भय, अपमान"},
    {"en": "Desire, love, passion, cohabitation, partner, public, wife or husband, dowry", "bn": "কামনা, প্রেম, আসক্তি, সহবাস, অংশীদার, জনসাধারণ, স্ত্রী বা স্বামী, যৌতুক", "hi": "इच्छा, प्रेम, आसक्ति, सहवास, साझेदार, जनसमुदाय, पत्नी अथवा पति, दहेज"},
    {"en": "Life, longevity, mental pain, defeat or insult, sorrow, scandal, ill-repute, death, impurity, obstacle, danger", "bn": "আয়ু, দীর্ঘায়ু, মানসিক যন্ত্রণা, পরাজয় বা অপমান, শোক, কলঙ্ক, দুর্নাম, মৃত্যু, অশুদ্ধি, বাধা, বিপদ", "hi": "आयु, दीर्घायु, मानसिक पीड़ा, पराजय अथवा अपमान, शोक, कलंक, अपयश, मृत्यु, अशुद्धि, बाधा, संकट"},
    {"en": "Guru or preceptor, father, auspicious, previous life, worship, penance, virtue, grandson, prayer, spiritual initiation, noble family, fortune", "bn": "গুরু বা আচার্য, পিতা, শুভ, পূর্বজন্ম, উপাসনা, তপস্যা, পুণ্য, পৌত্র, প্রার্থনা, আধ্যাত্মিক দীক্ষা, কুলীন পরিবার, ভাগ্য", "hi": "गुरु अथवा आचार्य, पिता, शुभ, पूर्वजन्म, उपासना, तपस्या, पुण्य, पौत्र, प्रार्थना, आध्यात्मिक दीक्षा, कुलीन परिवार, भाग्य"},
    {"en": "Livelihood, kingdom, work, commerce, trade, business, rank or position, good conduct, honour, sacrifice, command, quality, wealth, occupation", "bn": "জীবিকা, রাজ্য, কর্ম, বাণিজ্য, ব্যবসা, পদমর্যাদা, সদাচার, সম্মান, যজ্ঞ, আদেশ, গুণ, ধন, পেশা", "hi": "जीविका, राज्य, कर्म, वाणिज्य, व्यापार, पद अथवा स्थिति, सदाचार, सम्मान, यज्ञ, आदेश, गुण, धन, व्यवसाय"},
    {"en": "Profit or gain, income, all kinds of receipts, acquisition, gain, desire, passion, fulfilment of one's desire, wealth or riches, brothers and sisters - elder one, friends", "bn": "লাভ, আয়, সর্বপ্রকার প্রাপ্তি, অর্জন, কামনা, আসক্তি, বাসনাপূরণ, ধন বা সম্পদ, জ্যেষ্ঠ ভ্রাতা ও ভগিনী, বন্ধু", "hi": "लाभ, आय, सभी प्रकार की प्राप्ति, अर्जन, इच्छा, आसक्ति, इच्छापूर्ति, धन अथवा संपदा, ज्येष्ठ भाई-बहन, मित्र"},
    {"en": "House of disappearance, bondage, loss, negation, bed, sin, poverty, penury, loss, decline, misery, left eye, leg, defect", "bn": "অন্তর্ধানের ভাব, বন্ধন, ক্ষতি, নেতিকরণ, শয্যা, পাপ, দারিদ্র্য, অভাব, হানি, অবনতি, দুঃখ, বাম চক্ষু, পদ, ত্রুটি", "hi": "अंतर्धान का भाव, बंधन, हानि, निषेध, शय्या, पाप, दरिद्रता, अभाव, क्षति, पतन, दुःख, बायाँ नेत्र, पाँव, दोष"},
]


# --------------------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------------------
def _v(key: str, lang: Lang) -> str:
    entry = VOCAB.get(key)
    if entry is None:
        return key
    return entry.get(lang) or entry["en"]


def get_sign_lord(sign_index: int) -> str:
    """Planetary lord of a sign, from the client's 12 Rashis table."""
    return SIGN_LORDS[sign_index % 12]


def get_classifications(sign_index: int, lang: Lang = "en") -> list[dict[str, Any]]:
    """Every classification group the client's 01.pdf defines, for one sign.

    Each entry carries the group label, the sign's value in that group, the
    client's own definition, the client's stated predictive application where one
    was given, and a citation back to the source file and page.
    """
    idx = sign_index % 12
    assigned = _A[idx]
    out: list[dict[str, Any]] = []

    for group in GROUPS:
        key = group["key"]
        if key == "colour":
            value = COLOURS[idx].get(lang) or COLOURS[idx]["en"]
        elif key == "kalapurusha":
            value = KALAPURUSHA[idx].get(lang) or KALAPURUSHA[idx]["en"]
        else:
            value = _v(assigned[key], lang)

        entry: dict[str, Any] = {
            "key": key,
            "label": group["label"].get(lang) or group["label"]["en"],
            "value": value,
            "definition": group["definition"].get(lang) or group["definition"]["en"],
            "source": group["source"],
        }
        application = group.get("application")
        if application:
            entry["application"] = application.get(lang) or application["en"]
        out.append(entry)

    return out


def get_guna(sign_index: int, lang: Lang = "en") -> dict[str, Any]:
    """Both of the client's conflicting Guna readings for a sign, clearly flagged."""
    name = SIGN_ORDER[sign_index % 12]
    readings = []
    for page_key, variant in GUNA_VARIANTS.items():
        for guna_key in ("sattvik", "rajasik", "tamasik"):
            if name in variant[guna_key]:
                readings.append(
                    {
                        "source": variant["source"],
                        "value": _v(guna_key, lang),
                        "note": variant["note"].get(lang) or variant["note"]["en"],
                    }
                )
                break

    agrees = len({r["value"] for r in readings}) == 1
    conflict = next(
        (c for c in UNRESOLVED_IN_SOURCE if c["key"] == "guna"), None
    )
    return {
        "readings": readings,
        "is_disputed": not agrees,
        "notice": None
        if agrees
        else ((conflict or {}).get("summary", {}).get(lang) if conflict else None),
    }


def get_sign_profile(sign_index: int, lang: Lang = "en") -> dict[str, Any]:
    """The complete client-sourced profile of one sign."""
    idx = sign_index % 12
    names = SIGN_NAMES[idx]
    return {
        "index": idx,
        "name_en": names["en"],
        "name_sa": names["sa"],
        "name_bn": names["bn"],
        "name_hi": names["hi"],
        "lord": SIGN_LORDS[idx],
        "classifications": get_classifications(idx, lang),
        "guna": get_guna(idx, lang),
        "body_parts": BODY_PARTS_DETAIL[idx].get(lang) or BODY_PARTS_DETAIL[idx]["en"],
        "places": PLACES[idx].get(lang) or PLACES[idx]["en"],
        "trait_keywords": TRAIT_KEYWORDS[idx].get(lang) or TRAIT_KEYWORDS[idx]["en"],
        "sources": sorted({g["source"] for g in GROUPS}),
    }


def get_kp_reference(lang: Lang = "en") -> dict[str, Any]:
    """The KP basics the client supplied: the five rules and the house significations."""
    return {
        "basic_rules": [r.get(lang) or r["en"] for r in KP_BASIC_RULES],
        "house_significations": [
            {"house": i + 1, "signification": h.get(lang) or h["en"]}
            for i, h in enumerate(KP_HOUSE_SIGNIFICATIONS)
        ],
        "source": "KP Astrology Basics and Rules.pdf",
    }
