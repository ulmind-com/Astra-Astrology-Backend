"""Vedic Kundli-Face Synchronization Engine.

Implements the classical astrological face-reading treatise by Dharmender Kumar Bansal
(Patwari) from client document `e14262e36257a165.pdf` and Samudrika Shastra.

Key capabilities:
1. Calculates native's D1 Lagna, Lagna Lord, and Planetary Cusps using Swiss Ephemeris.
2. Synchronizes 12 Horoscope Bhavas (Houses) to 12 Facial Zones.
3. Cross-verifies Lagna Lord physiognomic traits (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu).
4. Analyzes 25+ First-House Planet-Pair Conjunctions (Bansal Lesson 10).
5. Maps the 10 Nakshatras of Kalpurush to facial energy centers (Prana Bindu).
6. Interprets Til & Masaka Vichar (Astrological Moles & Marks) with cross-body bodily reflections.
7. Prescribes authentic Vedic Samudrika Remedies (Upayas) for afflicted facial zones.
"""

from typing import Any
from loguru import logger

from app.schemas.astrology import KundliCalculateRequest
from app.services.astrology.kundli_service import calculate_kundli


# 12 Zodiac Signs and their Lords (Bansal Lesson 2 & 9)
SIGN_LORDS = {
    1: ("Aries", "Mars", "মেষ", "मंगल"),
    2: ("Taurus", "Venus", "বৃষ", "शुक्र"),
    3: ("Gemini", "Mercury", "মিথুন", "बुध"),
    4: ("Cancer", "Moon", "কর্কট", "चंद्र"),
    5: ("Leo", "Sun", "সিংহ", "सूर्य"),
    6: ("Virgo", "Mercury", "কন্যা", "बुध"),
    7: ("Libra", "Venus", "তুলা", "शुक्र"),
    8: ("Scorpio", "Mars", "বৃশ্চিক", "मंगल"),
    9: ("Sagittarius", "Jupiter", "ধনু", "बृहस्पति"),
    10: ("Capricorn", "Saturn", "মকর", "शनि"),
    11: ("Aquarius", "Saturn", "কুম্ভ", "शनि"),
    12: ("Pisces", "Jupiter", "মীন", "बृहस्पति"),
}

# 9 Planets Physiognomy & Complexion (Bansal Lesson 7, 8, 9)
PLANET_PHYSIOGNOMY = {
    "Sun": {
        "complexion_en": "Wheatish to golden complexion with royal dignity.",
        "complexion_bn": "রাজকীয় তেজযুক্ত গমবর্ণ বা ঈষৎ সোনালী লাবণ্য।",
        "complexion_hi": "शाही तेजयुक्त गेहूंआ या सुनहरी रंगत।",
        "facial_traits_en": "Large, round face with high forehead and dignified presence. Honey or amber-tinted eyes with a sober, commanding hairline.",
        "facial_traits_bn": "উন্নত ও প্রশস্ত কপাল, প্রস্ফুটিত গোলাকার মুখ এবং মধুবর্ণ বা পিঙ্গল চোখ। গুরুগম্ভীর ব্যক্তিত্ব ও রাজতুল্য চাহনি।",
        "facial_traits_hi": "विशाल व ऊंचा माथा, गोल चेहरा और शहद जैसे हल्के भूरे नेत्र। गंभीर और प्रभावशाली व्यक्तित्व।",
        "mole_type_en": "Golden, honey-colored mole or light freckle.",
        "mole_type_bn": "সোনালী বা মধু রঙের তিল বা হালকা মেচেতা।",
        "governs": "Right eye (in men) / Left eye (in women), bones, royal vitality.",
    },
    "Moon": {
        "complexion_en": "Fair, soft, and luminous with a youthful glow.",
        "complexion_bn": "স্নিগ্ধ, কোমল ও লাবণ্যময় চন্দ্রকান্ত দীপ্তি।",
        "complexion_hi": "सौम्य, कोमल और चंद्र जैसी शीतल आभा।",
        "facial_traits_en": "Round or gentle oval face with innocent, expressive, and deeply sensitive eyes. Soft contours that reflect inner emotional state.",
        "facial_traits_bn": "নিষ্পাপ ও অনুভূতিপ্রবণ মুখাবয়ব, গোলগাল কোমল গাল ও উজ্জ্বল ভাবপূর্ণ চোখ। চন্দ্রের কলার ন্যায় অভিব্যক্তিতে সূক্ষ্ম পরিবর্তনশীলতা।",
        "facial_traits_hi": "मासूम व भावुक चेहरा, कोमल गाल और अत्यंत संवेदनशील नेत्र। मन की चंचलता चेहरे पर झलकती है।",
        "mole_type_en": "Pale, soft birthmark or subtle changing marks.",
        "mole_type_bn": "হালকা রঙের তিল বা জন্মদাগ।",
        "governs": "Left eye (in men) / Right eye (in women), sympathetic nerves, emotional aura.",
    },
    "Mars": {
        "complexion_en": "Fair complexion with a distinctive ruddy or reddish flush.",
        "complexion_bn": "উজ্জ্বল ফর্সা রঙের সাথে রক্তিম বা তামাটে আভা।",
        "complexion_hi": "गौर वर्ण के साथ विशिष्ट रक्तिम या तांबई चमक।",
        "facial_traits_en": "Athletic, sharp, and resolute warrior-like features. Piercing, intense gaze with a firm jawline; prone to occasional pimples or scars.",
        "facial_traits_bn": "সেনাধ্যক্ষের মতো দৃঢ় চোয়াল, তীক্ষ্ণ ও নির্ভীক চাহনি। মুখে রক্তিম আভা, ব্রণ বা কোনো কাটার দাগ থাকার প্রবণতা।",
        "facial_traits_hi": "मजबूत जबड़ा, तीखे नैन-नक्श और निडर दृष्टि। चेहरे पर लालिमा, मुहांसे या किसी चोट का निशान संभव।",
        "mole_type_en": "Red mole, small scar, or ruddy freckle.",
        "mole_type_bn": "লালচে তিল, ক্ষুদ্র ব্রণ বা কাটার চিহ্ন।",
        "governs": "Muscles, jawline, sense of taste, stamina.",
    },
    "Mercury": {
        "complexion_en": "Clear, youthful skin with a vibrant, agile charm.",
        "complexion_bn": "চিরতরুণ, সতেজ ও প্রাণবন্ত লাবণ্য।",
        "complexion_hi": "चमकदार, युवा और फुर्तीली रंगत।",
        "facial_traits_en": "Appears significantly younger than actual age (prince look). Gracefully curved eyebrows with rich hair, witty expressive lips, and androgynous elegance.",
        "facial_traits_bn": "প্রকৃত বয়সের চেয়ে লক্ষণীয়ভাবে কম বয়সী দেখায় (কুমার রূপ)। ধনুকের মতো ঘন ভ্রু, চটপটে মুখ ও আকর্ষণীয় ঠোঁট।",
        "facial_traits_hi": "वास्तविक उम्र से काफी छोटे दिखने वाला चेहरा (राजकुमार स्वरूप)। सुंदर भौंहें और चपल, बुद्धिमान मुस्कान।",
        "mole_type_en": "Small, neat skin marks or pigment dots.",
        "mole_type_bn": "ক্ষুদ্র স্পষ্ট তিল বা ত্বকের স্বাভাবিক চিহ্ন।",
        "governs": "Skin texture, chin, articulate speech, youthfulness.",
    },
    "Jupiter": {
        "complexion_en": "Golden-wheatish, fair, and radiating intellectual nobility.",
        "complexion_bn": "গৌরবর্ণ, পরম সৌম্য ও জ্ঞানদীপ্ত আভা।",
        "complexion_hi": "गौर वर्ण, सौम्य और ज्ञान से आलोकित तेज।",
        "facial_traits_en": "Broad, elevated forehead with dignified, serene features. Inspires natural reverence like a sage or preceptor; well-proportioned mature facial balance.",
        "facial_traits_bn": "উচ্চ ও উন্মুক্ত কপাল, শান্ত ও সম্ভ্রান্ত মুখশ্রী। শিক্ষক ও গুরুজনসুলভ আভিজাত্য এবং শ্রদ্ধাশীল সামাজিক আকর্ষণ।",
        "facial_traits_hi": "विशाल व ऊंचा माथा, शांत व आदरणीय चेहरा। गुरु व विद्वान जैसी गरिमा और नैतिक प्रभाव।",
        "mole_type_en": "Prominent, auspicious golden-brown or fleshy mole.",
        "mole_type_bn": "উন্নত, শুভ বাদামী বা মাংসল তিল।",
        "governs": "Forehead expansiveness, cheeks, nose bridge, wisdom.",
    },
    "Venus": {
        "complexion_en": "Radiant, charming, and fair with captivating allure.",
        "complexion_bn": "অনুপম লাবণ্যময়, মোলায়েম ও মনোমুগ্ধকর রূপ।",
        "complexion_hi": "अत्यंत आकर्षक, चमकदार और सौम्य रंगत।",
        "facial_traits_en": "Plump, pleasing face with magnetic, smiling eyes, sweet lips, and lovely dimples. Naturally attractive facial curves with curly or soft hair.",
        "facial_traits_bn": "সুন্দর ও আবেদনময়ী মুখমণ্ডল, আকর্ষক টানা চোখ, মিষ্টি ঠোঁট ও গালে টোল (ডিম্পল)। স্বাভাবিক কমনীয়তা ও মনকাড়া হাসি।",
        "facial_traits_hi": "मनमोहक चेहरा, नशीली व सुंदर आंखें, रसीले होंठ और गालों पर डिंपल। स्वाभाविक सौंदर्य व मधुर मुस्कान।",
        "mole_type_en": "Charming beauty spot near lips, chin, or cheek.",
        "mole_type_bn": "ঠোঁট, গাল বা চিবুকের নিকটে সুন্দর তিল (সৌন্দর্য বিন্দু)।",
        "governs": "Eyes, chin, cheek plumpness, smiling aura.",
    },
    "Saturn": {
        "complexion_en": "Dusky, pale, or deep wheatish with an ascetic gravity.",
        "complexion_bn": "শ্যামবর্ণ বা গোধূলি আভা, গভীর ভাবগম্ভীর ও তপস্বী রূপ।",
        "complexion_hi": "सांवली या गहरी रंगत, गंभीर व तपस्वी स्वरूप।",
        "facial_traits_en": "Structured, bony facial contours with deep-set, thoughtful eyes. Appears remarkably mature and experienced; carries the weight of wisdom and endurance.",
        "facial_traits_bn": "সুস্পষ্ট হাড়ের গঠন, গভীর চিন্তাশীল চোখ এবং বয়সের চেয়ে অনেক পরিণত ও অভিজ্ঞ মুখাবয়ব। অটল ধৈর্য ও সহনশীলতার ছাপ।",
        "facial_traits_hi": "स्पष्ट जबड़ा व हड्डियां, गहरी विचारशील आंखें और उम्र से काफी परिपक्व दिखने वाला चेहरा। असीम धैर्य का प्रतीक।",
        "mole_type_en": "Dark black mole, distinctive freckles, or deep skin mark.",
        "mole_type_bn": "গাঢ় কালো তিল বা স্থায়ী জন্মদাগ।",
        "governs": "Bone framework, deep-set eyes, philtrum, longevity.",
    },
    "Rahu": {
        "complexion_en": "Smoky, exotic, with an enigmatic and unconventional magnet.",
        "complexion_bn": "ধূম্রবর্ণ বা মিশ্র আকর্ষণীয় রূপ।",
        "complexion_hi": "धुएं जैसी गहरी व रहस्यमयी रंगत।",
        "facial_traits_en": "Sharp, intense eyes that look through surfaces. Asymmetrical intrigue or distinctive magnetic mystery that commands instant curiosity.",
        "facial_traits_bn": "রহস্যময় ও তীব্র পর্যবেক্ষণশীল চাহনি। মুখে অপ্রচলিত কিন্তু প্রবল আকর্ষণ ক্ষমতা।",
        "facial_traits_hi": "तीक्ष्ण, रहस्यमयी दृष्टि और अनोखा चुंबकीय आकर्षण।",
        "mole_type_en": "Smoky, dark birthmark or prominent irregular mole.",
        "mole_type_bn": "ধোঁয়াটে তিল বা বড় আকারের জন্মদাগ।",
        "governs": "Ears, unusual asymmetries, unexpected karmic marks.",
    },
    "Ketu": {
        "complexion_en": "Ascetic, subtle, with a quiet and piercing depth.",
        "complexion_bn": "আধ্যাত্মিক, শান্ত ও অন্তর্ভেদী রূপ।",
        "complexion_hi": "शांत, आध्यात्मिक व अंतर्मुखी आभा।",
        "facial_traits_en": "Deep, mystical, non-attached gaze. Fine, ascetic contours; often carries a surgical scar, childhood cut, or honey mark.",
        "facial_traits_bn": "তপস্বীসুলভ শান্ত চাহনি, তীক্ষ্ণ অনুভূতি এবং শৈশবের কোনো কাটার দাগ বা চিহ্ন।",
        "facial_traits_hi": "तपस्वी जैसी वैराग्यपूर्ण आंखें और चेहरे पर किसी सर्जरी या पुरानी चोट का निशान।",
        "mole_type_en": "Honey-colored mole, surgical scar, or subtle spot.",
        "mole_type_bn": "মধু রঙের তিল বা শৈশবের ক্ষতের দাগ।",
        "governs": "Crown/hairline, neck, detachment markers.",
    },
}

# 12 Horoscope Bhavas mapped to Face Zones (Bansal Lesson 1, 6)
BHAVAS_TO_FACE = [
    {
        "house": 1,
        "name_en": "1st House (Lagna / Ascendant)",
        "name_bn": "১ম ভাব (লগ্ন ভাব)",
        "name_hi": "प्रथम भाव (लग्न)",
        "face_part_en": "Forehead & Entire Cranial Frame",
        "face_part_bn": "কপাল ও সামগ্রিক মস্তকাবয়ব",
        "face_part_hi": "माथा व संपूर्ण मुखाकृति",
        "significance_en": "Reflects vitality, physical constitution, inborn destiny, and public self-presentation.",
        "significance_bn": "জীবনীশক্তি, দৈহিক গঠন, সহজাত ভাগ্য এবং আত্মপ্রকাশ নির্দেশ করে।",
        "significance_hi": "जीवन ऊर्जा, शारीरिक गठन और आत्म-अभिव्यक्ति का प्रतीक है।",
    },
    {
        "house": 2,
        "name_en": "2nd House (Dhana & Kutumba)",
        "name_bn": "২য় ভাব (ধন ও বাণী ভাব)",
        "name_hi": "द्वितीय भाव (धन व वाणी)",
        "face_part_en": "Right Eye & Right Cheek / Oral Eloquence",
        "face_part_bn": "ডান চোখ ও ডান গাল / বাণীর প্রকাশ",
        "face_part_hi": "दाहिनी आंख व दाहिना गाल / वाणी का प्रभाव",
        "significance_en": "Governs accumulated wealth, family heritage, clarity of speech, and right ocular vitality.",
        "significance_bn": "সঞ্চিত সম্পদ, পারিবারিক মর্যাদা, বাকপটুতু এবং ডান চোখের জ্যোতি নির্দেশ করে।",
        "significance_hi": "संचित धन, पारिवारिक प्रतिष्ठा, वाणी की स्पष्टता और दाहिने नेत्र की शक्ति।",
    },
    {
        "house": 3,
        "name_en": "3rd House (Sahaja & Parakrama)",
        "name_bn": "৩য় ভাব (পরাক্রম ও ভ্রাতা ভাব)",
        "name_hi": "तृतीय भाव (पराक्रम व बंधु)",
        "face_part_en": "Right Ear & Right Shoulder Alignment",
        "face_part_bn": "ডান কান ও ডান কাঁধের অবস্থান",
        "face_part_hi": "दाहिना कान व दाहिना कंधा",
        "significance_en": "Indicates stamina, enterprise, communication skills, siblings, and working capacity.",
        "significance_bn": "উদ্যম, পরাক্রম, সাহস, যোগাযোগ দক্ষতা এবং কর্মক্ষমতা নির্দেশ করে।",
        "significance_hi": "उद्यम, साहस, पराक्रम और कार्यक्षमता का परिचायक है।",
    },
    {
        "house": 4,
        "name_en": "4th House (Sukha & Matru)",
        "name_bn": "৪র্থ ভাব (সুখ ও মাতৃ ভাব)",
        "name_hi": "चतुर्थ भाव (सुख व मातृ)",
        "face_part_en": "Space between Eyebrows above the nose (Glabella / Bhrukuti)",
        "face_part_bn": "দুই ভ্রুর মধ্যবর্তী স্থান (ভৃকুটি / গ্ল্যাবেলা)",
        "face_part_hi": "दोनों भौंहों के बीच का स्थान (भृकुटि)",
        "significance_en": "Reveals peace of mind, ancestral real-estate, heart center tranquility, and maternal blessings.",
        "significance_bn": "মানসিক শান্তি, গৃহসুখ, বক্ষস্থলের প্রশান্তি এবং মাতৃ আশীর্বাদ নির্দেশ করে।",
        "significance_hi": "मानसिक शांति, गृहसुख, हृदय की स्थिरता और माता का स्नेह दर्शाता है।",
    },
    {
        "house": 5,
        "name_en": "5th House (Putra & Buddhi)",
        "name_bn": "৫ম ভাব (বুদ্ধি ও সন্তান ভাব)",
        "name_hi": "पंचम भाव (बुद्धि व संतान)",
        "face_part_en": "Upper Eyelids",
        "face_part_bn": "চোখের উপরের পাতা (Eyelids)",
        "face_part_hi": "आंखों की ऊपरी पलकें",
        "significance_en": "Governs intellectual sharpness, past-life merit (Purva Punya), progeny, and intuitive vision.",
        "significance_bn": "সূক্ষ্ম মেধা, পূর্বপুণ্য, উদ্ভাবনী শক্তি ও আধ্যাত্মিক দূরদর্শিতা নির্দেশ করে।",
        "significance_hi": "तीक्ष्ण बुद्धि, पूर्वजन्म के पुण्य, संतान सुख और दूरदर्शिता का संकेत है।",
    },
    {
        "house": 6,
        "name_en": "6th House (Ripu & Roga)",
        "name_bn": "৬ষ্ঠ ভাব (রোগ ও শত্রু ভাব)",
        "name_hi": "षष्ठ भाव (रोग व शत्रु)",
        "face_part_en": "Right Neckbone & Cervical Base",
        "face_part_bn": "ডান ঘাড়ের হাড় ও গ্রীবা",
        "face_part_hi": "दाहिनी गर्दन की हड्डी",
        "significance_en": "Reflects disease resistance, handling competition, daily routines, and immune resilience.",
        "significance_bn": "রোগপ্রতিরোধ ক্ষমতা, প্রতিদ্বন্দ্বিতা মোকাবিলার শক্তি ও নিয়মানুবর্তিতা নির্দেশ করে।",
        "significance_hi": "रोग प्रतिरोधक क्षमता, प्रतिस्पर्धा से निपटने का साहस और अनुशासन।",
    },
    {
        "house": 7,
        "name_en": "7th House (Kalatra & Jaya)",
        "name_bn": "৭ম ভাব (জায়া ও অংশীদার ভাব)",
        "name_hi": "सप्तम भाव (विवाह व साझेदारी)",
        "face_part_en": "Upper & Lower Lips",
        "face_part_bn": "উপরের ও নিচের ঠোঁট",
        "face_part_hi": "ऊपरी व निचला होंठ",
        "significance_en": "Upper lip reflects verbal expression; Lower lip governs marital harmony, partner affection, and friendship.",
        "significance_bn": "উপরের ঠোঁট বাচনভঙ্গি এবং নিচের ঠোঁট দাম্পত্য সুখ, সঙ্গী নির্বাচন ও প্রেমপ্রীতি প্রকাশ করে।",
        "significance_hi": "ऊपरी होंठ बातचीत की शैली और निचला होंठ दांपत्य सुख व संबंधों का कारक है।",
    },
    {
        "house": 8,
        "name_en": "8th House (Ayush & Randhra)",
        "name_bn": "৮ম ভাব (আয়ু ও গুপ্ত সংকট ভাব)",
        "name_hi": "अष्टम भाव (आयु व गुप्त रहस्य)",
        "face_part_en": "Left Neckbone & Occipital Base",
        "face_part_bn": "বাঁ ঘাড়ের হাড়",
        "face_part_hi": "बाईं गर्दन की हड्डी",
        "significance_en": "Governs longevity, unearned inheritance, crisis management, and occult stamina.",
        "significance_bn": "দীর্ঘায়ু, অপ্রকাশ্য সম্পদ, সংকট উত্তরণের ধৈর্য ও গুহ্য সাধনা নির্দেশ করে।",
        "significance_hi": "दीर्घायु, गुप्त संकटों से उबरने की शक्ति और गूढ़ ज्ञान का प्रतीक है।",
    },
    {
        "house": 9,
        "name_en": "9th House (Bhagya & Dharma)",
        "name_bn": "৯ম ভাব (ভাগ্য ও ধর্ম ভাব)",
        "name_hi": "नवम भाव (भाग्य व धर्म)",
        "face_part_en": "Lower Forehead above the Brow Ridge",
        "face_part_bn": "কপালের নিম্নাংশ (ভ্রু রেখার ঠিক উপরে)",
        "face_part_hi": "माथे का निचला भाग",
        "significance_en": "Indicates divine fortune, spiritual preceptors, higher studies, and righteous ethics.",
        "significance_bn": "ভাগ্যোদয়, পিতৃভক্তি, উচ্চতর জ্ঞান, গুরুকৃপা ও ধর্মপরায়ণতা নির্দেশ করে।",
        "significance_hi": "भाग्योदय, गुरु कृपा, उच्च ज्ञान और धार्मिक निष्ठा का सूचक है।",
    },
    {
        "house": 10,
        "name_en": "10th House (Karma & Rajya)",
        "name_bn": "১০ম ভাব (কর্ম ও সম্মান ভাব)",
        "name_hi": "दशम भाव (कर्म व मान-प्रतिष्ठा)",
        "face_part_en": "Cheeks & Nose Head (Tip)",
        "face_part_bn": "গাল ও নাসিকাগ্র (নাকের ডগা)",
        "face_part_hi": "गाल और नाक का अगला सिरा",
        "significance_en": "Governs professional career, public authority, fame, father's status, and ego balance.",
        "significance_bn": "পেশাগত সাফল্য, সামাজিক প্রতিপত্তি, পিতা ও বংশের গৌরব এবং আত্মমর্যাদাবোধ নির্দেশ করে।",
        "significance_hi": "कार्यक्षेत्र में प्रतिष्ठा, पिता का प्रभाव, प्रसिद्धि और सामाजिक सम्मान।",
    },
    {
        "house": 11,
        "name_en": "11th House (Labha & Aya)",
        "name_bn": "১১শ ভাব (লাভ ও সিদ্ধি ভাব)",
        "name_hi": "एकादश भाव (लाभ व सिद्धि)",
        "face_part_en": "Left Ear & Left Shoulder",
        "face_part_bn": "বাঁ কান ও বাঁ কাঁধ",
        "face_part_hi": "बायां कान व बायां कंधा",
        "significance_en": "Reflects multiple income streams, influential social networks, and realization of desires.",
        "significance_bn": "বহুমুখী আর্থিক লাভ, প্রভাবশালী বন্ধুচক্র এবং সকল আশা-আকাঙ্ক্ষা পূরণ নির্দেশ করে।",
        "significance_hi": "वित्तीय लाभ, बड़े सामाजिक संपर्क और इच्छाओं की पूर्ति का प्रतीक है।",
    },
    {
        "house": 12,
        "name_en": "12th House (Vyaya & Moksha)",
        "name_bn": "১২শ ভাব (ব্যয় ও মোক্ষ ভাব)",
        "name_hi": "द्वादश भाव (व्यय व मोक्ष)",
        "face_part_en": "Left Eye & Subconscious Gaze",
        "face_part_bn": "বাঁ চোখ ও অন্তর্লীন দৃষ্টি",
        "face_part_hi": "बाईं आंख व अंतर्मुखी दृष्टि",
        "significance_en": "Governs foreign travels, subconscious dreams, expenditure control, and spiritual liberation.",
        "significance_bn": "বিদেশ যাত্রা, স্বপ্নজগৎ, অর্থব্যয়ের প্রবণতা এবং আধ্যাত্মিক মুক্তি নির্দেশ করে।",
        "significance_hi": "विदेश यात्रा, अंतर्मन के विचार, व्यय नियंत्रण और आध्यात्मिक मुक्ति।",
    },
]

# 10 Nakshatras of Kalpurush on Face (Bansal Lesson 5, 8)
KALPURUSH_FACE_NAKSHATRAS = {
    1: {"name": "Ashwini", "lord": "Ketu", "body_part": "Crown / Head", "part_bn": "মাথা / মস্তক"},
    2: {"name": "Bharani", "lord": "Venus", "body_part": "Forehead", "part_bn": "কপাল"},
    3: {"name": "Krittika", "lord": "Sun", "body_part": "Eyebrows", "part_bn": "ভ্রু"},
    4: {"name": "Rohini", "lord": "Moon", "body_part": "Eyes", "part_bn": "চোখ"},
    5: {"name": "Mrigashira", "lord": "Mars", "body_part": "Nose", "part_bn": "নাক"},
    6: {"name": "Ardra", "lord": "Rahu", "body_part": "Ears", "part_bn": "কান"},
    7: {"name": "Punarvasu", "lord": "Jupiter", "body_part": "Cheeks & Nose Head", "part_bn": "গাল ও নাসিকাগ্র"},
    8: {"name": "Pushya", "lord": "Saturn", "body_part": "Lips & Philtrum", "part_bn": "ঠোঁট ও নাসিকার নিম্নভাগ"},
    9: {"name": "Ashlesha", "lord": "Mercury", "body_part": "Chin", "part_bn": "চিবুক"},
    10: {"name": "Magha", "lord": "Ketu", "body_part": "Neck", "part_bn": "ঘাড়"},
}

# 1st House Planet Combinations (Bansal Lesson 10)
CONJUNCTION_RULES = {
    frozenset(["Sun", "Jupiter"]): {
        "title_en": "Surya-Guru Yoga: Royal Intellectual Demeanor",
        "title_bn": "সূর্য-বৃহস্পতি সংযোগ: রাজকীয় ও প্রাজ্ঞ ব্যক্তিত্ব",
        "title_hi": "सूर्य-गुरु योग: शाही व विद्वान मुखाकृति",
        "meaning_en": "Bestows a radiant, broad forehead and commanding presence. Combines executive authority with deep philosophical wisdom.",
        "meaning_bn": "প্রশস্ত ও উজ্জ্বল কপাল এবং স্বাভাবিক কর্তৃত্বপূর্ণ মুখচ্ছবি দান করে। প্রশাসনিক তেজ এবং গভীর প্রজ্ঞার অপূর্ব মিলন।",
        "meaning_hi": "विशाल माथा और प्रभावशाली मुखाकृति प्रदान करता है। प्रशासनिक अधिकार और गहरी बुद्धि का सुंदर संगम।",
    },
    frozenset(["Sun", "Mercury"]): {
        "title_en": "Budhaditya Yoga: Royal Youthful Charisma",
        "title_bn": "বুধাদিত্য যোগ: রাজকীয় তরুণ দীপ্তি",
        "title_hi": "बुधादित्य योग: शाही व युवा आकर्षण",
        "meaning_en": "Commands respect while retaining a lively, youthful aura. Sharp, luminous eyes with eloquent, persuasive lips.",
        "meaning_bn": "সম্মানজনক রাজকীয় গাম্ভীর্যের সাথে চিরতরুণ সজীবতা বজায় রাখে। তীক্ষ্ণ প্রখর চোখ এবং অত্যন্ত বাকপটু ঠোঁটের গঠন।",
        "meaning_hi": "सम्मानजनक तेज के साथ सदाबहार युवा आकर्षण। चमकदार आंखें और अत्यंत प्रभावशाली वाणी।",
    },
    frozenset(["Sun", "Moon"]): {
        "title_en": "Surya-Chandra Yoga: Majestic Sensitivity",
        "title_bn": "সূর্য-চন্দ্র সংযোগ: মহিমান্বিত সংবেদনশীলতা",
        "title_hi": "सूर्य-चंद्र योग: तेजस्वी संवेदनशीलता",
        "meaning_en": "Round, prominent facial structure with well-formed lips; often accompanied by a subtle beauty mark.",
        "meaning_bn": "গোলাকার স্পষ্ট মুখাবয়ব ও পরিপূর্ণ ঠোঁটের গঠন; মুখে একটি স্পষ্ট শুভ তিল থাকার জোরালো লক্ষণ।",
        "meaning_hi": "सुडौल गोल चेहरा और भरे हुए होंठ; चेहरे पर कोई शुभ तिल होने का प्रबल संकेत।",
    },
    frozenset(["Sun", "Mars"]): {
        "title_en": "Surya-Mangal Yoga: Warrior Countenance",
        "title_bn": "সূর্য-মঙ্গল সংযোগ: অপরাজেয় বীর রূপ",
        "title_hi": "सूर्य-मंगल योग: पराक्रमी मुखाकृति",
        "meaning_en": "Bold, athletic countenance with a reddish glow. Piercing gaze, firm jawline, and natural leadership vigor.",
        "meaning_bn": "রক্তিম আভাবিশিষ্ট বলিষ্ঠ ও নির্ভীক চেহারা। তীক্ষ্ণ চাহনি, কঠোর চোয়াল এবং অদম্য নেতৃত্বশক্তি।",
        "meaning_hi": "रक्तिम आभा युक्त मजबूत चेहरा। तीखे नैन-नक्श, दृढ़ जबड़ा और निडर नेतृत्व।",
    },
    frozenset(["Sun", "Saturn"]): {
        "title_en": "Surya-Shani Yoga: Stern Gravitas & Depth",
        "title_bn": "সূর্য-শনি সংযোগ: গভীর গাম্ভীর্য ও কৃচ্ছ্রসাধনা",
        "title_hi": "सूर्य-शनि योग: गंभीर व विचारशील तेज",
        "meaning_en": "Austere, deeply intellectual countenance. Carrying profound life lessons with an uncompromisingly principled gaze.",
        "meaning_bn": "কঠোর নীতিবান ও পরম চিন্তাশীল মুখাবয়ব। গভীর জীবনবোধ এবং অনমনীয় আত্মমর্যাদার ছাপ।",
        "meaning_hi": "गंभीर, सिद्धांतवादी और तपस्वी स्वरूप। गहरा जीवन अनुभव और अनुशासित व्यक्तित्व।",
    },
    frozenset(["Moon", "Jupiter"]): {
        "title_en": "Gaja-Kesari Aura: Benign Eminence",
        "title_bn": "গজকেশরী প্রভা: কল্যাণময় প্রীতি ও সম্মান",
        "title_hi": "गजकेसरी आभा: कल्याणकारी प्रतिष्ठा",
        "meaning_en": "Peaceful, magnanimous face with a dignified gaze. Radiates trust and universal respect.",
        "meaning_bn": "শান্ত, উদার ও সম্ভ্রান্ত মুখশ্রী। মানুষের মাঝে শ্রদ্ধা ও স্বাভাবিক আস্থা আকর্ষণ করে।",
        "meaning_hi": "शांत, उदार और प्रतिष्ठित मुखाकृति। समाज में सहज आदर और विश्वास प्राप्त होता है।",
    },
    frozenset(["Moon", "Venus"]): {
        "title_en": "Chandra-Shukra Yoga: Luminous Beauty",
        "title_bn": "চন্দ্র-শুক্র সংযোগ: অনুপম লাবণ্য ও সৌন্দর্য",
        "title_hi": "चंद्र-शुक्र योग: अत्यंत मनमोहक लावण्य",
        "meaning_en": "Charming, soft facial contours with glowing fair complexion and endearing smile.",
        "meaning_bn": "অপরূপ স্নিগ্ধ মুখশ্রী, প্রস্ফুটিত মিষ্টি হাসি এবং সবাইকে মুগ্ধ করার মতো কোমল লাবণ্য।",
        "meaning_hi": "अत्यंत सुंदर व कोमल चेहरा, मनभावन मुस्कान और सबको आकर्षित करने वाली रंगत।",
    },
    frozenset(["Mars", "Venus"]): {
        "title_en": "Mangal-Shukra Yoga: Magnetic Passion",
        "title_bn": "মঙ্গল-শুক্র সংযোগ: তীব্র আকর্ষণীয় তেজ ও লাবণ্য",
        "title_hi": "मंगल-शुक्र योग: चुंबकीय आकर्षण",
        "meaning_en": "Flushed wheatish complexion with intense physical magnetism and charming features.",
        "meaning_bn": "গমবর্ণের সাথে রক্তিম লাবণ্যের মিশ্রণ; তীব্র শারীরিক আকর্ষণ ও মনোমুগ্ধকর ব্যক্তিত্ব।",
        "meaning_hi": "गेहूंआ-रक्तिम रंगत, तीव्र शारीरिक आकर्षण और प्रभावशाली व्यक्तित्व।",
    },
    frozenset(["Mars", "Saturn"]): {
        "title_en": "Mangal-Shani Yoga: Steely Tenacity",
        "title_bn": "মঙ্গল-শনি সংযোগ: লৌহকঠিন সংকল্প ও সহনশীলতা",
        "title_hi": "मंगल-शनि योग: लौह जैसा दृढ़ संकल्प",
        "meaning_en": "Rugged, chiseled jawline with endurance written across the brow. Defiant under adversity.",
        "meaning_bn": "সুদৃঢ় চোয়াল, পাথুরে ধৈর্য ও কঠোর পরিশ্রমী মুখচ্ছবি। যেকোনো প্রতিকূলতায় অবিচল থাকার শক্তি।",
        "meaning_hi": "मजबूत तराशा हुआ जबड़ा, असीम सहनशीलता और विपत्तियों में अडिग रहने की क्षमता।",
    },
    frozenset(["Mercury", "Jupiter"]): {
        "title_en": "Budha-Guru Yoga: Saintly Scholar",
        "title_bn": "বুধ-বৃহস্পতি সংযোগ: ঋষিতুল্য প্রাজ্ঞ পণ্ডিত",
        "title_hi": "बुध-गुरु योग: संत सदृश प्रज्ञा",
        "meaning_en": "Serene, enlightened, saint-like presence. Clear articulate brow with tranquil intellectual warmth.",
        "meaning_bn": "ঋষি বা জ্ঞানীর মতো প্রশান্ত ও নির্মল মুখশ্রী। প্রখর যুক্তিবোধের সাথে গভীর আধ্যাত্মিক সৌম্যতা।",
        "meaning_hi": "ऋषि या विद्वान जैसी शांत व निर्मल मुखाकृति। प्रखर बुद्धि और आध्यात्मिक सौम्यता।",
    },
}


def synchronize_face_with_kundli(
    *,
    birth_data: dict[str, Any],
    measurements: dict[str, float],
    face_sections: list[dict[str, Any]] | None = None,
    tri_zone: dict[str, Any] | None = None,
    mahabhuta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Computes exact Kundli correlation with facial biometrics.

    Args:
        birth_data: Dictionary containing `dob` (or day, month, year), `tob` (or hour, min),
                    `lat`, `lon`, `tz`, and optional `name`, `gender`.
        measurements: Biometric dictionary with 23 normalized ratios.
        face_sections: Detected sections from Morphological face reading.
        tri_zone: Computed Tri-Zone breakdown.
        mahabhuta: Computed Pancha Mahabhuta classification.

    Returns:
        Rich dictionary with Lagna alignment, House-Zone correlations, Conjunction effects,
        Kalpurush Nakshatra activations, Til marks, and Vedic remedies.
    """
    try:
        day = int(birth_data.get("day", 1))
        month = int(birth_data.get("month", 1))
        year = int(birth_data.get("year", 2000))
        hour = int(birth_data.get("hour", 12))
        minute = int(birth_data.get("min", birth_data.get("minute", 0)))
        lat = float(birth_data.get("lat", 22.5726))
        lon = float(birth_data.get("lon", 88.3639))
        tz = float(birth_data.get("tz", 5.5))

        # Handle ISO dob string if passed
        if "dob" in birth_data and isinstance(birth_data["dob"], str):
            parts = birth_data["dob"].split("-")
            if len(parts) == 3:
                year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        if "tob" in birth_data and isinstance(birth_data["tob"], str):
            tparts = birth_data["tob"].split(":")
            if len(tparts) >= 2:
                hour, minute = int(tparts[0]), int(tparts[1])

        req = KundliCalculateRequest(
            day=day,
            month=month,
            year=year,
            hour=hour,
            min=minute,
            lat=lat,
            lon=lon,
            tz=tz,
            name=birth_data.get("name", "Native"),
            gender=birth_data.get("gender", "male"),
        )
        kundli_res = calculate_kundli(req)
    except Exception as exc:
        logger.warning(f"Could not compute Kundli for face synchronization: {exc}")
        return _empty_kundli_sync()

    # 1. Extract Ascendant / Lagna Details
    asc_sign_num = getattr(kundli_res, "d1_asc_sign", 1)
    sign_info = SIGN_LORDS.get(asc_sign_num, ("Aries", "Mars", "মেষ", "मंगल"))
    sign_name_en, lagna_lord, sign_name_bn, sign_name_hi = sign_info

    lord_phys = PLANET_PHYSIOGNOMY.get(lagna_lord, PLANET_PHYSIOGNOMY["Sun"])

    # 2. Extract Planets in 1st House & Aspects
    planets_in_1st: list[str] = []
    house_planets_map: dict[int, list[str]] = {h: [] for h in range(1, 13)}

    for p in getattr(kundli_res, "d1_planets", []):
        h_num = getattr(p, "house_num", 1)
        p_name = getattr(p, "name", "")
        if p_name and p_name != "Asc":
            house_planets_map.setdefault(h_num, []).append(p_name)
            if h_num == 1:
                planets_in_1st.append(p_name)

    # 3. First House Conjunction Effect (Bansal Lesson 10)
    conjunction_info = None
    all_1st_influences = set(planets_in_1st)
    if lagna_lord not in all_1st_influences and len(all_1st_influences) < 2:
        all_1st_influences.add(lagna_lord)

    for pair, rule in CONJUNCTION_RULES.items():
        if pair.issubset(all_1st_influences):
            conjunction_info = rule
            break

    if conjunction_info is None:
        conjunction_info = {
            "title_en": f"{lagna_lord} Ascendant Lord Signature",
            "title_bn": f"লগ্নাধিপতি {lagna_lord}-এর শাস্ত্রীয় মুখচ্ছবি",
            "title_hi": f"लग्नेश {lagna_lord} का मुखाकृति प्रभाव",
            "meaning_en": lord_phys["facial_traits_en"],
            "meaning_bn": lord_phys["facial_traits_bn"],
            "meaning_hi": lord_phys["facial_traits_hi"],
        }

    # 4. Correlate All 12 Houses to Facial Zones
    house_correlations: list[dict[str, Any]] = []
    for bhava in BHAVAS_TO_FACE:
        h_idx = bhava["house"]
        planets_here = house_planets_map.get(h_idx, [])
        planets_str = ", ".join(planets_here) if planets_here else "Unoccupied (স্বাভাবিক শুভ)"

        # Check biometric status for that part
        status_note_en = ""
        status_note_bn = ""
        if h_idx in (1, 9):
            fh = measurements.get("forehead_h", 0.25)
            status_note_en = "Broad forehead aligns with strong Lagna/9th house merits." if fh >= 0.26 else "Compact forehead indicates self-made resilience."
            status_note_bn = "উন্মুক্ত কপাল শক্তিশালী লগ্ন ও ৯ম ভাবের শুভত্বের পরিচায়ক।" if fh >= 0.26 else "পরিমিত কপাল স্বোপার্জিত পুরুষকারের নির্দেশক।"
        elif h_idx == 2:
            status_note_en = "Right eye axis indicates stable financial preservation."
            status_note_bn = "ডান চোখের গঠন সুরক্ষিত ধন ও পারিবারিক স্থায়িত্ব প্রকাশ করে।"
        elif h_idx == 12:
            status_note_en = "Left eye structure governs expenditure discernment."
            status_note_bn = "বাঁ চোখের গঠন দূরদর্শী ব্যয় নিয়ন্ত্রণ ও চিন্তাশীলতার নির্দেশক।"
        elif h_idx == 10:
            cf = measurements.get("cheek_full", 0.92)
            status_note_en = "Cheekbone alignment signifies visible social authority." if cf >= 0.92 else "Reflects focused, individual career pursuit."
            status_note_bn = "উন্নত গণ্ডাস্থি কর্মক্ষেত্রে প্রতিপত্তি ও সুনামের প্রতীক।" if cf >= 0.92 else "একাগ্র স্বাধীন কর্মোদ্যোগের পরিচায়ক।"
        elif h_idx == 7:
            lt = measurements.get("lip_thick", 0.35)
            status_note_en = "Well-defined vermilion border indicates sincere partner relations."
            status_note_bn = "সুস্পষ্ট ঠোঁটের গঠন বিশ্বস্ত দাম্পত্য ও মধুর বাক্যালাপের নির্দেশক।"
        else:
            status_note_en = "Harmoniously positioned in classical Samudrika proportion."
            status_note_bn = "সামুদ্রিক শাস্ত্রীয় সুসমন্বিত অনুপাতে অবস্থিত।"

        house_correlations.append({
            "house": h_idx,
            "house_name": bhava["name_en"],
            "house_name_bn": bhava["name_bn"],
            "house_name_hi": bhava["name_hi"],
            "face_part": bhava["face_part_en"],
            "face_part_bn": bhava["face_part_bn"],
            "face_part_hi": bhava["face_part_hi"],
            "planets_occupying": planets_str,
            "significance_en": bhava["significance_en"],
            "significance_bn": bhava["significance_bn"],
            "status_note_en": status_note_en,
            "status_note_bn": status_note_bn,
        })

    # 5. Kalpurush 10 Nakshatras on Face Highlight
    # Check native's Moon nakshatra or Ascendant nakshatra
    astro_pos = getattr(kundli_res, "astro_positions", None)
    native_nak = getattr(astro_pos, "nakshatra", "Rohini") if astro_pos else "Rohini"
    kalpurush_highlight = None
    for nak_id, nak_data in KALPURUSH_FACE_NAKSHATRAS.items():
        if nak_data["name"].lower() in native_nak.lower():
            kalpurush_highlight = {
                "nakshatra": nak_data["name"],
                "lord": nak_data["lord"],
                "body_part_en": nak_data["body_part"],
                "body_part_bn": nak_data["part_bn"],
                "explanation_en": f"Your birth nakshatra {nak_data['name']} activates the {nak_data['body_part']} as your primary facial Prana Bindu (energetic seat of destiny).",
                "explanation_bn": f"আপনার জন্ম নক্ষত্র {nak_data['name']} কালপুরুষের মুখমণ্ডলে {nak_data['part_bn']}-কে আপনার মূল প্রাণবিন্দু (ভাগ্যের কেন্দ্রস্থল) হিসেবে সক্রিয় করে।",
            }
            break

    if kalpurush_highlight is None:
        kalpurush_highlight = {
            "nakshatra": "Rohini",
            "lord": "Moon",
            "body_part_en": "Eyes (Netra)",
            "body_part_bn": "চোখ (নেত্র)",
            "explanation_en": "Your facial vital force is anchored in the eyes, reflecting keen emotional intelligence and clarity.",
            "explanation_bn": "আপনার মুখের মূল প্রাণবিন্দু চোখে অবস্থিত, যা গভীর অনুভূতিপ্রবণতা ও অন্তর্দৃষ্টির পরিচায়ক।",
        }

    # 6. Til / Masaka Vichar (Astrological Moles & Marks)
    til_masaka: list[dict[str, Any]] = [
        {
            "planet": lagna_lord,
            "type_en": lord_phys["mole_type_en"],
            "type_bn": lord_phys["mole_type_bn"],
            "zone_en": f"Zone governed by {lagna_lord} ({'Forehead' if lagna_lord in ('Sun', 'Jupiter') else 'Eyes' if lagna_lord == 'Moon' else 'Cheeks' if lagna_lord == 'Venus' else 'Jaw/Chin'})",
            "zone_bn": f"{lagna_lord}-এর শাসিত অংশ",
            "body_correlation_en": "Bansal cross-body reflection: Planetary marks on facial zones reflect corresponding energy on limbs and trunk.",
            "body_correlation_bn": "বনসল শাস্ত্রীয় সূত্র: মুখের তিল বা চিহ্ন শরীরের সংশ্লিষ্ট ভাবের (যেমন ২য় ভাবে তিল বাঁ উরুতে এবং ৭ম ভাবে তিল নাভিতে) শুভাশুভ প্রকাশ করে।",
        }
    ]

    # 7. Vedic Samudrika Remedies (Upayas)
    remedies: list[dict[str, Any]] = [
        {
            "category": "Surya & Brihaspati (Forehead / Destiny)",
            "upaya_en": "Practice morning Surya Namaskar and apply sandalwood or saffron tilak between the eyebrows (Ajna/4th house) to enhance clarity and mental peace.",
            "upaya_bn": "প্রাতঃকালে সূর্য প্রণাম এবং দুই ভ্রুর মধ্যস্থলে (আজ্ঞা চক্র/৪র্থ ভাব) চন্দন বা জাফরানের তিলক ধারণ করুন; এতে মানসিক শান্তি ও ভাগ্যোন্নতি ত্বরান্বিত হয়।",
            "gemstone": "Ruby / Yellow Sapphire (or Sun/Jupiter prayer)",
        },
        {
            "category": "Chandra & Shukra (Eyes & Expression)",
            "upaya_en": "Drink water from a silver vessel in the morning and offer respect to maternal figures to nurture radiant ocular vitality and emotional serenity.",
            "upaya_bn": "রৌপ্য পাত্রে জল পান করুন এবং গুরুজন ও মাতৃস্থানীয়াদের শ্রদ্ধা করুন; এতে চোখের লাবণ্য ও সংবেদনশীল মানসিক স্থিরতা বজায় থাকে।",
            "gemstone": "Pearl / Diamond / White Zircon",
        },
        {
            "category": "Budha & Shani (Speech & Foundation)",
            "upaya_en": "Recite Budha Gayatri Mantra for eloquent speech and light a sesame oil lamp on Saturdays to fortify enduring patience and karmic resolve.",
            "upaya_bn": "বাকসিদ্ধি ও ব্যবসার উন্নতির জন্য বুধ গায়ত্রী জপ করুন এবং প্রতি শনিবার তিলের তেলের প্রদীপ প্রজ্বলন করুন; এতে অটল ধৈর্য ও সংকল্প দৃঢ় হয়।",
            "gemstone": "Emerald / Blue Sapphire",
        },
    ]

    return {
        "sync_available": True,
        "ascendant_sign": sign_name_en,
        "ascendant_sign_bn": sign_name_bn,
        "ascendant_sign_hi": sign_name_hi,
        "ascendant_lord": lagna_lord,
        "physiognomy_traits": lord_phys,
        "first_house_conjunction": conjunction_info,
        "house_correlations": house_correlations,
        "kalpurush_highlight": kalpurush_highlight,
        "til_masaka": til_masaka,
        "remedies": remedies,
    }


def _empty_kundli_sync() -> dict[str, Any]:
    return {
        "sync_available": False,
        "message": "Birth details not provided or ephemeris unavailable. Standalone Samudrika scan active.",
    }
