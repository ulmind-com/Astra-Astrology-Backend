"""Comprehensive Canonical Nakshatra (Birth Star) Database & Avakahada Chakra Rules.

Derived from canonical Vedic astrology treatises (Brihat Parashara Hora Shastra,
Jataka Parijata, Muhurta Chintamani, and technical specifications in client resource documents).
Supports 100% accurate mathematical positions, 27 Nakshatras, 108 Padas, Avakahada Chakra,
Tarabala, and complete multi-language descriptions (English, Bengali, Hindi).
"""

from typing import Any

NAKSHATRAS_MASTER: list[dict[str, Any]] = [
    {
        "index": 0,
        "name_en": "Ashwini",
        "name_bn": "অশ্বিনী",
        "name_hi": "अश्विनी",
        "lord": "Ketu",
        "deity_en": "Ashwini Kumaras (Celestial Physicians)",
        "deity_bn": "অশ্বিনীকুমারদ্বয় (স্বর্গের দৈব চিকিৎসক)",
        "deity_hi": "अश्विनी कुमार (देवताओं के वैद्य)",
        "symbol_en": "Horse's Head",
        "symbol_bn": "অশ্বের মস্তক (ঘোড়ার মাথা)",
        "symbol_hi": "अश्व का सिर",
        "gana_en": "Deva (Divine)",
        "gana_bn": "দেব",
        "gana_hi": "देव",
        "yoni_en": "Horse (Male)",
        "yoni_bn": "অশ্ব (পুং)",
        "yoni_hi": "अश्व (पुरुष)",
        "nadi_en": "Aadi (Vata)",
        "nadi_bn": "আদি (বাত)",
        "nadi_hi": "आदि (वात)",
        "sacred_tree_en": "Kuchla (Strychnos nux-vomica)",
        "sacred_tree_bn": "বিষকাঁটালি / কুচিলা",
        "sacred_tree_hi": "कुचिला",
        "beej_mantra": "ॐ অশ্বিনীকুমারাভ্যাং নমঃ (Om Ashwini Kumarabhyam Namah)",
        "lucky_color_en": "Blood Red & Peach",
        "lucky_color_bn": "রক্তলাল ও পীচ",
        "lucky_color_hi": "रक्त लाल और पीच",
        "lucky_numbers": [1, 9],
        "lucky_gemstone_en": "Cat's Eye (Vaidurya)",
        "lucky_gemstone_bn": "বৈদূর্যমণি (ক্যাটস আই)",
        "lucky_gemstone_hi": "लहसुनिया (कैट्स आई)",
        "padas": [
            {"pada": 1, "rashi_idx": 0, "navamsha": "Aries", "namakshar_en": "Chu", "namakshar_bn": "চু", "namakshar_hi": "चू"},
            {"pada": 2, "rashi_idx": 0, "navamsha": "Taurus", "namakshar_en": "Che", "namakshar_bn": "চে", "namakshar_hi": "चे"},
            {"pada": 3, "rashi_idx": 0, "navamsha": "Gemini", "namakshar_en": "Cho", "namakshar_bn": "চো", "namakshar_hi": "चो"},
            {"pada": 4, "rashi_idx": 0, "navamsha": "Cancer", "namakshar_en": "La", "namakshar_bn": "লা", "namakshar_hi": "ला"},
        ],
        "overview": {
            "en": "Ashwini, the first constellation of the zodiac, radiates youthfulness, agility, and swift healing power. Natives possess innate vitality, pioneering spirit, and spontaneous enthusiasm.",
            "bn": "রাশিচক্রের প্রথম নক্ষত্র অশ্বিনী ক্ষিপ্রতা, তারুণ্য ও অলৌকিক নিরাময় ক্ষমতার প্রতীক। এঁরা অত্যন্ত গতিশীল, সাহসী, স্বাধীনচেতা এবং যে কোনো নতুন উদ্যোগের অগ্রদূত হন।",
            "hi": "अश्विनी नक्षत्र ऊर्जा, गति और त्वरित उपचार शक्ति का प्रतीक है। इस नक्षत्र के जातक साहसी, फुर्तीले, स्वतंत्र और नए कार्यों की शुरुआत करने में निपुण होते हैं।",
        },
        "strengths": {
            "en": [
                "Remarkable speed of execution, quick intelligence, and alertness",
                "Natural talent in medicine, healing, emergency response, and athletics",
                "Warm-hearted generosity and readiness to rescue others in distress",
                "Charming, youthful appearance with dynamic personal magnetism",
            ],
            "bn": [
                "অসাধারণ ক্ষিপ্রতা, প্রখর বুদ্ধিমত্তা ও উপস্থিত বুদ্ধি",
                "চিকিৎসা, হিলিং, স্পোর্টস ও জরুরি পরিষেবা ক্ষেত্রে সহজাত দক্ষতা",
                "বিপদে মানুষকে রক্ষা করার অকুণ্ঠ উদারতা ও পরোপকারী মনোভাব",
                "চিরতরুণ ব্যক্তিত্ব, সপ্রতিভ আকর্ষণ ও উদ্যমী কর্মক্ষমতা",
            ],
            "hi": [
                "कार्य निष्पादन में गजब की फुर्ती और त्वरित निर्णय क्षमता",
                "चिकित्सा, खेलकूद, आपातकालीन सहायता और अनुसंधान में अद्भुत प्रतिभा",
                "संकट में दूसरों की सहायता के लिए सदैव तत्पर उदार स्वभाव",
                "सदाबहार ऊर्जावान व्यक्तित्व और सम्मोहक आकर्षण",
            ],
        },
        "cautions_and_pitfalls": {
            "en": [
                "Extreme restlessness, impulsiveness, and abandoning tasks prematurely",
                "Driving or rushing recklessly leading to sudden injuries or sprains",
                "Stubborn refusal to heed calm advice from elders or advisors",
                "Impatience with slower people leading to unnecessary friction",
            ],
            "bn": [
                "অতিরিক্ত চঞ্চলতা, ধৈর্যহীনতা ও কাজ অসমাপ্ত ফেলে অন্য কাজে চলে যাওয়া",
                "বেপরোয়া গতিতে গাড়ি চালানো বা তাড়াহুড়ো করতে গিয়ে হঠাৎ আঘাত পাওয়ার ঝুঁকি",
                "অভিজ্ঞ ব্যক্তিদের শান্ত পরামর্শ অগ্রাহ্য করার একগুঁয়েমি",
                "অন্যের ধীরগতির কাজে অধৈর্য হয়ে মেজাজ হারানোর প্রবণতা",
            ],
            "hi": [
                "अत्यधिक बेचैनी, अधीरता और काम को अधूरा छोड़कर आगे बढ़ जाना",
                "जल्दबाजी में वाहन चलाने या भागदौड़ से अचानक चोट लगने की आशंका",
                "अनुभवी लोगों की सलाह को अनदेखा करने का जिद्दी स्वभाव",
                "दूसरों के धीमे काम से खीझना और विवाद खड़ा करना",
            ],
        },
        "beneficial_actions_and_remedies": {
            "en": [
                "Offer fresh green grass or gram to horses or visit cowsheds on Tuesdays",
                "Practice slow deep breathing and grounding yoga to balance excess wind energy",
                "Worship Lord Ganesha and chant Ketu Beej Mantra on Wednesdays/Tuesdays",
                "Donate warm blankets, medical kits, or medicines to needy patients",
            ],
            "bn": [
                "মঙ্গলবার ঘোড়া বা গবাদি পশুকে কাঁচা ঘাস বা ছোলা খাওয়ানো অত্যন্ত শুভ",
                "অতিরিক্ত বায়ু ও চঞ্চলতা শান্ত করতে প্রতিদিন শান্ত প্রাণায়াম ও ধ্যান অভ্যাস",
                "শ্রী গণেশের উপাসনা এবং কেতুর বীজ মন্ত্র জপ করা পরম কল্যাণকর",
                "দরিদ্র ও অসুস্থ রোগীদের বিনামূল্যে ওষুধ বা প্রাথমিক চিকিৎসা সামগ্রী দান",
            ],
            "hi": [
                "मंगलवार को घोड़ों या गोवंश को हरा चारा अथवा भीगी चना दाल खिलाएं",
                "अत्यधिक वायु और चंचलता को संतुलित करने के लिए प्राणायाम का नियमित अभ्यास",
                "भगवान श्री गणेश की आराधना करें और केतु बीज मंत्र का जप करें",
                "जरूरतमंद मरीजों को नि:शुल्क दवाइयां अथवा प्राथमिक उपचार सामग्री दान करें",
            ],
        },
        "career_fields": {
            "en": ["Medicine & Surgery", "Aviation & Motorsports", "Sports & Fitness Training", "Defense & Law Enforcement", "Pharmaceuticals & Biotechnology"],
            "bn": ["চিকিৎসা ও শল্যচিকিৎসা (সার্জারি)", "বিমান চালনা ও মোটরস্পোর্টস", "ক্রীড়া ও ফিটনেস প্রশিক্ষণ", "প্রতিরক্ষা ও পুলিশ পরিষেবা", "ফার্মাসিউটিক্যাল ও বায়োটেকনোলজি"],
            "hi": ["चिकित्सा एवं शल्य चिकित्सा", "विमानन एवं मोटरस्पोर्ट्स", "खेलकूद एवं फिटनेस ट्रेनिंग", "रक्षा व सुरक्षा बल", "फार्मास्यूटिकल्स एवं अनुसंधान"],
        },
    },
    {
        "index": 1,
        "name_en": "Bharani",
        "name_bn": "ভরণী",
        "name_hi": "भरणी",
        "lord": "Venus",
        "deity_en": "Yamaraja (Lord of Truth & Dharma)",
        "deity_bn": "যমরাজ (ধর্ম ও সত্যের অধিপতি)",
        "deity_hi": "यमराज (धर्मराज)",
        "symbol_en": "Yoni (Vessel of Creation)",
        "symbol_bn": "যোনিদ্বার / সৃষ্টির পাত্র",
        "symbol_hi": "योनि द्वार (सृजन का आधार)",
        "gana_en": "Manushya (Human)",
        "gana_bn": "মনুষ্য",
        "gana_hi": "मनुष्य",
        "yoni_en": "Elephant (Male)",
        "yoni_bn": "হস্তী (পুং)",
        "yoni_hi": "गज / हाथी (पुरुष)",
        "nadi_en": "Madhya (Pitta)",
        "nadi_bn": "মধ্য (পিত্ত)",
        "nadi_hi": "मध्य (पित्त)",
        "sacred_tree_en": "Amla (Emblica officinalis)",
        "sacred_tree_bn": "আমলকী",
        "sacred_tree_hi": "आंवला",
        "beej_mantra": "ॐ যমায় নমঃ / ॐ শুক্রায় নমঃ",
        "lucky_color_en": "Pure White & Rose Pink",
        "lucky_color_bn": "শুভ্র সাদা ও গোলাপী",
        "lucky_color_hi": "श्वेत और गुलाबी",
        "lucky_numbers": [6, 2],
        "lucky_gemstone_en": "Diamond (Heera) or White Zircon",
        "lucky_gemstone_bn": "হীরে অথবা সাদা জিরকন",
        "lucky_gemstone_hi": "हीरा अथवा श्वेत जरकन",
        "padas": [
            {"pada": 1, "rashi_idx": 0, "navamsha": "Leo", "namakshar_en": "Lee", "namakshar_bn": "লী", "namakshar_hi": "ली"},
            {"pada": 2, "rashi_idx": 0, "navamsha": "Virgo", "namakshar_en": "Lu", "namakshar_bn": "লু", "namakshar_hi": "लू"},
            {"pada": 3, "rashi_idx": 0, "navamsha": "Libra", "namakshar_en": "Le", "namakshar_bn": "লে", "namakshar_hi": "ले"},
            {"pada": 4, "rashi_idx": 0, "navamsha": "Scorpio", "namakshar_en": "Lo", "namakshar_bn": "লো", "namakshar_hi": "लो"},
        ],
        "overview": {
            "en": "Bharani governs birth, transformation, and deep endurance. Ruled by Venus, natives exhibit fierce truthfulness, unyielding resolve, and deep appreciation for aesthetic arts.",
            "bn": "ভরণী নক্ষত্র সৃষ্টি, রূপান্তর ও সীমাহীন সহনশীলতার দ্যোতক। শুক্র নিয়ন্ত্রিত এই নক্ষত্রের মানুষ দৃঢ় সংকল্প, সত্যবাদিতা এবং নান্দনিক শিল্পের গভীর অনুরাগী হন।",
            "hi": "भरणी नक्षत्र जीवन, सृजन और परिवर्तन की शक्ति का प्रतिनिधित्व करता है। शुक्र के प्रभाव से जातक सत्यप्रिय, दृढ़ संकल्पी और सौंदर्य के पारखी होते हैं।",
        },
        "strengths": {
            "en": [
                "Unshakeable capacity to bear burdens and endure intense hardships",
                "Deep sense of justice, truthfulness, and uncompromising moral courage",
                "Artistic flair, refined romantic charm, and magnetic charisma",
                "Courage to undergo major personal transformations without fear",
            ],
            "bn": [
                "কঠিন পরিস্থিতি ও গুরুদায়িত্ব হাসিমুখে বহন করার অপূর্ব সহনশীলতা",
                "অদম্য ন্যায়পরায়ণতা, সত্যবাদিতা ও অন্যায়ের সঙ্গে আপসহীন মনোভাব",
                "শিল্পকলা, নান্দনিক রুচি এবং অত্যন্ত আকর্ষণীয় ব্যক্তিত্ব",
                "জীবনের আমূল পরিবর্তন ও নবজাগরণকে নিঃশঙ্ক চিত্তে বরণ করার সাহস",
            ],
            "hi": [
                "कठिन से कठिन चुनौतियों और जिम्मेदारियों को संभालने का धैर्य",
                "सत्यवादिता, न्यायप्रियता और अनैतिकता से कभी न झुकने का संकल्प",
                "कलात्मक दृष्टिकोण, सौंदर्यबोध और सम्मोहक आकर्षण",
                "जीवन के बड़े परिवर्तनों को निर्भीकता से स्वीकार करने की क्षमता",
            ],
        },
        "cautions_and_pitfalls": {
            "en": [
                "Extremism in emotional reactions; either excessively indulgent or unforgiving",
                "Harboring grudges or being harsh when delivering unvarnished truth",
                "Prone to sensory over-indulgence, spending splurges, or jealousy",
                "Throat, reproductive, or kidney sensitivities during stressful periods",
            ],
            "bn": [
                "আবেগ ও সিদ্ধান্তের ক্ষেত্রে চরমপন্থা—হয় অতিরিক্ত মোহগ্রস্ত নয়তো ক্ষমাহীন নির্মম",
                "স্পষ্ট কথা বলতে গিয়ে রূঢ় হয়ে অন্যের মনে আঘাত দেওয়ার প্রবণতা",
                "অতিরিক্ত বিলাসিতা, অমিতব্যয়িতা বা ঈর্ষাবোধের শিকার হওয়া",
                "অতিরিক্ত মানসিক চাপে গলা, প্রজনন অঙ্গ বা কিডনি সংক্রান্ত সমস্যায় ভোগা",
            ],
            "hi": [
                "भावुकता में अतिवादी हो जाना—अत्यधिक आसक्ति या कठोर विरक्ति",
                "अति स्पष्टवादिता में कटु शब्द बोलकर संबंध बिगाड़ लेना",
                "विलासिता और फिजूलखर्ची में संतुलन खो बैठना",
                "अत्यधिक तनाव के समय गले व गुर्दे संबंधी समस्याएं",
            ],
        },
        "beneficial_actions_and_remedies": {
            "en": [
                "Plant and tend an Amla tree; consume fresh Amla in the morning",
                "Worship Goddess Mahalakshmi or Durga on Fridays with white flowers",
                "Donate white silk clothes, curd, milk, or silver coins to respectable women",
                "Cultivate moderation in food, pleasures, and speech",
            ],
            "bn": [
                "বাড়িতে বা বাগানে আমলকী গাছ লাগানো এবং নিয়মিত আমলকী সেবন করা মঙ্গলজনক",
                "শুক্রবার দেবী মহালক্ষ্মী বা মা দুর্গার চরণে সাদা পদ্ম বা সাদা ফুল নিবেদন",
                "শুক্রবার কোনো সধবা নারীকে সাদা বস্ত্র, দই, দুধ বা মিষ্টান্ন দান",
                "আহার, বিলাসিতা ও বাক্যালাপে সংযম অনুশীলন করা",
            ],
            "hi": [
                "आंवले का वृक्ष लगाएं और उसकी देखभाल करें; आंवले का नियमित सेवन करें",
                "शुक्रवार को मां लक्ष्मी की आराधना करें और श्वेत पुष्प अर्पित करें",
                "शुक्रवार को जरूरतमंद महिलाओं को सफेद वस्त्र, दूध, दही या खीर दान करें",
                "वाणी और जीवनशैली में संयम बनाए रखें",
            ],
        },
        "career_fields": {
            "en": ["Obstetrics & Gynecology", "Cinema, Fashion & Luxury Goods", "Judiciary & Law Enforcement", "Culinary Arts & Hospitality", "Publishing & Media Production"],
            "bn": ["স্ত্রী ও প্রসূতি রোগ বিশেষজ্ঞ (গাইনোকোলজি)", "সিনেমা, ফ্যাশন ও বিলাসবহুল সামগ্রী", "আইন ও বিচার বিভাগ", "হসপিটালিটি ও রন্ধনশিল্প", "মিডিয়া ও প্রকাশনা"],
            "hi": ["स्त्री रोग व प्रसूति चिकित्सा", "फिल्म, फैशन व ग्लैमर उद्योग", "न्यायिक सेवा व वकालत", "होटल व आतिथ्य सत्कार", "मीडिया व प्रकाशन"],
        },
    },
    {
        "index": 2,
        "name_en": "Krittika",
        "name_bn": "কৃত্তিকা",
        "name_hi": "कृत्तिका",
        "lord": "Sun",
        "deity_en": "Agni (God of Sacred Fire)",
        "deity_bn": "অগ্নিদেব (পবিত্র অগ্নির অধিপতি)",
        "deity_hi": "अग्नि देव",
        "symbol_en": "Razor / Flame / Knife",
        "symbol_bn": "ক্ষুর / অগ্নিশিখা / কৃপাণ",
        "symbol_hi": "उस्तरा / ज्वाला / छुरी",
        "gana_en": "Rakshasa",
        "gana_bn": "রাক্ষস",
        "gana_hi": "राक्षस",
        "yoni_en": "Sheep / Ram (Female)",
        "yoni_bn": "মেষ / ভেড়া (স্ত্রী)",
        "yoni_hi": "मेष / भेड़ (स्त्री)",
        "nadi_en": "Antya (Kapha)",
        "nadi_bn": "অন্ত্য (কফ)",
        "nadi_hi": "अंत्य (कफ)",
        "sacred_tree_en": "Gular / Fig (Ficus glomerata)",
        "sacred_tree_bn": "ডুমুর (যজ্ঞডুমুর)",
        "sacred_tree_hi": "गूलर",
        "beej_mantra": "ॐ অগ্নয়ে নমঃ / ॐ সূর্যায় নমঃ",
        "lucky_color_en": "Ruby Red & Gold",
        "lucky_color_bn": "রক্তমাখানো লাল ও সোনালী",
        "lucky_color_hi": "रूबी लाल और सुनहरा",
        "lucky_numbers": [1, 3],
        "lucky_gemstone_en": "Ruby (Manikya)",
        "lucky_gemstone_bn": "চুনি (রুবি)",
        "lucky_gemstone_hi": "माणिक्य (रूबी)",
        "padas": [
            {"pada": 1, "rashi_idx": 0, "navamsha": "Sagittarius", "namakshar_en": "A", "namakshar_bn": "অ", "namakshar_hi": "अ"},
            {"pada": 2, "rashi_idx": 1, "navamsha": "Capricorn", "namakshar_en": "Ee", "namakshar_bn": "ঈ", "namakshar_hi": "ई"},
            {"pada": 3, "rashi_idx": 1, "navamsha": "Aquarius", "namakshar_en": "U", "namakshar_bn": "উ", "namakshar_hi": "उ"},
            {"pada": 4, "rashi_idx": 1, "navamsha": "Pisces", "namakshar_en": "Ea", "namakshar_bn": "এ", "namakshar_hi": "ए"},
        ],
        "overview": {
            "en": "Krittika embodies the purifying flame of Agni. Ruled by the Sun, individuals born under Krittika possess sharp intellect, fiery willpower, critical discernment, and protective nurturing.",
            "bn": "কৃত্তিকা পবিত্র যজ্ঞাগ্নির প্রতীক। সূর্যের শাসনে এঁরা অত্যন্ত প্রখর ধীশক্তিসম্পন্ন, তেজস্বী, কঠোর সত্যাশ্রয়ী এবং আশ্রিত ব্যক্তির রক্ষক হিসেবে পরিচিত হন।",
            "hi": "कृत्तिका नक्षत्र पवित्र अग्नि तत्व का प्रतीक है। सूर्य के स्वामित्व के कारण इस नक्षत्र के जातक तेजस्वी, दृढ़ संकल्पी, स्पष्टवादी और तीक्ष्ण बुद्धि के धनी होते हैं।",
        },
        "strengths": {
            "en": [
                "Penetrating critical intellect that cuts through deception and illusion",
                "Fierce dedication to protecting dependents, family, and vulnerable souls",
                "Tremendous willpower, dignified presence, and leadership authority",
                "Natural purification capacity, refining everything they touch",
            ],
            "bn": [
                "তীক্ষ্ণ বিশ্লেষণ ক্ষমতা যা অসত্য ও প্রতারণাকে নিমেষেই ছিন্নভিন্ন করে দেয়",
                "পরিবার ও আশ্রিতজনকে রক্ষা করার জন্য আত্মবলিদান দিতে প্রস্তুত মনোভাব",
                "দৃঢ় ব্যক্তিত্ব, তেজস্বী চালচলন ও নেতৃত্বদানের প্রাকৃতিক গুণাবলী",
                "যে কোনো বিশৃঙ্খল পরিবেশকে পরিশীলিত ও শুদ্ধ করার দুর্লভ ক্ষমতা",
            ],
            "hi": [
                "कुशाग्र विश्लेषणात्मक बुद्धि जो किसी भी छल-कपट को तुरंत पकड़ लेती है",
                "अपनों और आश्रितों की रक्षा के लिए सदैव ढाल बनकर खड़े रहना",
                "तेजस्वी व्यक्तित्व, स्वाभिमान और नेतृत्व की अपार क्षमता",
                "अव्यवस्था को सुधारकर शुद्ध व उत्कृष्ट बनाने की स्वाभाविक कला",
            ],
        },
        "cautions_and_pitfalls": {
            "en": [
                "Biting sarcasm, searing criticism that alienates well-meaning friends",
                "Short-tempered outbursts and stubborn pride refusing compromise",
                "Digestive acidity, ulcers, and inflammatory skin conditions",
                "Impatience with human imperfections and setting impossibly high standards",
            ],
            "bn": [
                "তীক্ষ্ণ কটূক্তি ও ব্যঙ্গাত্মক কথার কারণে বন্ধুদের শত্রু বানিয়ে ফেলা",
                "হঠাৎ অগ্নিশর্মা হয়ে যাওয়া এবং অহংকারের বশে নমনীয় হতে অস্বীকার করা",
                "অ্যাসিডিটি, বুকজ্বালা, গ্যাসট্রিক ও ত্বকের প্রদাহজনিত সমস্যায় ভোগা",
                "অন্যের ছোটখাটো ভুলত্রুটি সহ্য করতে না পেরে অতিরিক্ত খিটখিটে হওয়া",
            ],
            "hi": [
                "तीखी वाणी और व्यंग्य से मित्रों व सहयोगियों को आहत करना",
                "क्रोध पर नियंत्रण न रहना और अड़ियल रवैया अपनाना",
                "अम्लता (एसिडिटी), पेट में जलन और त्वचा संबंधी विकार",
                "दूसरों की गलतियों पर तुरंत भड़क उठना और अत्यधिक अपेक्षाएं रखना",
            ],
        },
        "beneficial_actions_and_remedies": {
            "en": [
                "Offer Surya Arghya (water mixed with red kumkum) at sunrise daily",
                "Recite Aditya Hridaya Stotra or Gayatri Mantra for inner peace",
                "Plant or care for a Gular (Fig) tree",
                "Donate wheat, copper, or jaggery to elders on Sundays",
            ],
            "bn": [
                "প্রতিদিন সূর্যোদয়ের সময় তামার পাত্রে জল ও রক্তচন্দন দিয়ে সূর্যপ্রণাম",
                "আদিত্য হৃদয় স্তোত্র বা গায়ত্রী মন্ত্র নিয়মিত জপ করা মানসিক শান্তি প্রদান করে",
                "যজ্ঞডুমুর গাছের পরিচর্যা করা অত্যন্ত শুভ",
                "রবিবারে গম, গুড় বা তামার পাত্র সৎ ব্রাহ্মণ বা প্রবীণদের দান করা",
            ],
            "hi": [
                "प्रतिदिन सूर्योदय के समय तांबे के लोटे से सूर्य देव को अर्घ्य दें",
                "आदित्य हृदय स्तोत्र अथवा गायत्री मंत्र का नित्य पाठ करें",
                "गूलर का वृक्ष लगाएं अथवा उसकी सेवा करें",
                "रविवार को गेहूं, तांबा या गुड़ का दान वृद्धजनों को करें",
            ],
        },
        "career_fields": {
            "en": ["Culinary Master Chefs", "Military & Defense Commanders", "Fire Engineering & Metallurgy", "Critical Reviewers & Editors", "Administrative & Executive Leadership"],
            "bn": ["রন্ধন বিশেষজ্ঞ (শেফ)", "প্রতিরক্ষা ও সামরিক অধিনায়ক", "ধাতুবিদ্যা ও অগ্নি প্রকৌশল", "সমালোচক ও উচ্চপদস্থ সম্পাদক", "প্রশাসনিক ও এক্সিকিউটিভ নেতৃত্ব"],
            "hi": ["मास्टर शेफ व पाककला", "सैन्य व रक्षा अधिकारी", "धातु विज्ञान व अग्नि अभियांत्रिकी", "समीक्षक व संपादक", "उच्च प्रशासनिक नेतृत्व"],
        },
    },
    {
        "index": 3,
        "name_en": "Rohini",
        "name_bn": "রোহিণী",
        "name_hi": "रोहिणी",
        "lord": "Moon",
        "deity_en": "Lord Brahma / Prajapati (The Creator)",
        "deity_bn": "ব্রহ্মা / প্রজাপতি (সৃষ্টিকর্তা)",
        "deity_hi": "प्रजापति ब्रह्मा",
        "symbol_en": "Chariot / Cart / Temple",
        "symbol_bn": "রথ / গো-যান / সুসজ্জিত মন্দির",
        "symbol_hi": "रथ / बैलगाड़ी / मंदिर",
        "gana_en": "Manushya",
        "gana_bn": "মনুষ্য",
        "gana_hi": "मनुष्य",
        "yoni_en": "Serpent (Male)",
        "yoni_bn": "সর্প (পুং)",
        "yoni_hi": "सर्प (पुरुष)",
        "nadi_en": "Antya (Kapha)",
        "nadi_bn": "অন্ত্য (কফ)",
        "nadi_hi": "अंत्य (कफ)",
        "sacred_tree_en": "Jamun (Syzygium cumini)",
        "sacred_tree_bn": "জামগাছ",
        "sacred_tree_hi": "जामुन",
        "beej_mantra": "ॐ চন্দ্রায় নমঃ / ॐ ব্রহ্মণে নমঃ",
        "lucky_color_en": "Pearl White & Emerald Green",
        "lucky_color_bn": "মুক্তো সাদা ও পান্না সবুজ",
        "lucky_color_hi": "मोती श्वेत और पन्ना हरा",
        "lucky_numbers": [2, 7],
        "lucky_gemstone_en": "Pearl (Moti) or Moonstone",
        "lucky_gemstone_bn": "খাঁটি মুক্তো অথবা চন্দ্রকান্তমণি",
        "lucky_gemstone_hi": "सच्चा मोती अथवा मूनस्टोन",
        "padas": [
            {"pada": 1, "rashi_idx": 1, "navamsha": "Aries", "namakshar_en": "O", "namakshar_bn": "ও", "namakshar_hi": "ओ"},
            {"pada": 2, "rashi_idx": 1, "navamsha": "Taurus", "namakshar_en": "Va", "namakshar_bn": "বা", "namakshar_hi": "वा"},
            {"pada": 3, "rashi_idx": 1, "navamsha": "Gemini", "namakshar_en": "Vi", "namakshar_bn": "বি", "namakshar_hi": "वी"},
            {"pada": 4, "rashi_idx": 1, "navamsha": "Cancer", "namakshar_en": "Vu", "namakshar_bn": "বু", "namakshar_hi": "वू"},
        ],
        "overview": {
            "en": "Rohini is the favorite star of the Moon, radiating beauty, fertility, agriculture, and high charm. Natives are gifted with artistic grace, sweet voice, and prosperous material growth.",
            "bn": "রোহিণী চন্দ্রের প্রিয়তমা নক্ষত্র। এটি রূপ, সৌন্দর্য, উর্বরতা, কৃষি ও সৃষ্টিশীলতার প্রতীক। এই নক্ষত্রের মানুষ মধুরভাষী, রুচিশীল এবং বিপুল বস্তুগত সমৃদ্ধি অর্জন করেন।",
            "hi": "रोहिणी चंद्रमा का सबसे प्रिय नक्षत्र है। यह सौंदर्य, आकर्षण, उर्वरता और समृद्धि का परिचायक है। जातक मनमोहक व्यक्तित्व, मधुर वाणी और कलाप्रिय स्वभाव के होते हैं।",
        },
        "strengths": {
            "en": [
                "Exceptional aesthetic sensibility, magnetic eyes, and charming demeanor",
                "High fertility of ideas, wealth creation, and business acumen",
                "Gentle, persuasive conversational ability that wins allies effortlessly",
                "Deep appreciation for nature, fine cuisine, music, and home comfort",
            ],
            "bn": [
                "অপূর্ব রূপলাবণ্য, আকর্ষণীয় টানা চোখ ও অমায়িক আচরণ",
                "নতুন পরিকল্পনা বাস্তবায়ন এবং ব্যবসা ও ধনসম্পদ বৃদ্ধির চমৎকার মেধা",
                "মিষ্টি কথা ও নরম ব্যবহারের মাধ্যমে সকলের প্রিয়ভাজন হওয়ার ক্ষমতা",
                "প্রকৃতি, গানবাজনা, সুস্বাদু আহার ও সুন্দর গৃহসজ্জার প্রতি গভীর অনুরাগ",
            ],
            "hi": [
                "आकर्षक नयन-नक्श, सुंदर व्यक्तित्व और सहज आकर्षण",
                "व्यापार में लाभ कमाने और संपत्ति संचय करने की तीव्र सूझबूझ",
                "मीठी वाणी और शालीनता जिससे हर कोई प्रभावित हो जाता है",
                "प्रकृति, कला, संगीत और स्वादिष्ट व्यंजनों के प्रति स्वाभाविक प्रेम",
            ],
        },
        "cautions_and_pitfalls": {
            "en": [
                "Possessiveness, jealousy, and vulnerability to flattery",
                "Over-attachment to material luxuries and sensual comforts",
                "Mood swings and stubborn sulking when denied desires",
                "Prone to water retention, throat phlegm, and weight gain",
            ],
            "bn": [
                "অতিরিক্ত অধিকারবোধ, অন্যের প্রতি ঈর্ষা ও তোষামোদে ভুলে যাওয়ার দুর্বলতা",
                "ভোগবিলাস ও আরাম-আয়েশের প্রতি মাত্রাতিরিক্ত আসক্তি",
                "মনের মতো না হলে মুখভার করে থাকা ও মেজাজের ওঠানামা",
                "শরীরে জল জমা, অতিরিক্ত মেদবৃদ্ধি ও ঠাণ্ডা লাগার ধাত",
            ],
            "hi": [
                "अधिकार जताने की भावना, ईर्ष्या और चापलूसी में जल्दी आ जाना",
                "भौतिक सुख-सुविधाओं और विलासिता के प्रति अत्यधिक आसक्ति",
                "मनचाहा न होने पर हठ करना और मूड में बदलाव",
                "कफ जनित रोग, मोटापा और जल तत्व से जुड़े विकार",
            ],
        },
        "beneficial_actions_and_remedies": {
            "en": [
                "Plant and water a Jamun tree; enjoy its shade and fruit",
                "Worship Lord Shiva and perform milk abhishekam on Mondays",
                "Honor your mother and seek her blessings before major ventures",
                "Donate white rice, silver, or milk to orphanages on Mondays",
            ],
            "bn": [
                "জামগাছ লাগানো এবং নিয়মিত তার যত্ন নেওয়া অত্যন্ত শুভ ফল দেয়",
                "সোমবারে দেবাদিদেব শিবলিঙ্গে কাঁচা দুধ ও গঙ্গাজল নিবেদন",
                "প্রতিদিন মায়ের পদধূলি গ্রহণ করে আশীর্বাদ নিয়ে কাজ শুরু করা",
                "সোমবারে আতপ চাল, খাঁটি দুধ বা শ্বেতবস্ত্র কোনো দরিদ্রকে দান",
            ],
            "hi": [
                "जामुन का पेड़ लगाएं और उसकी देखभाल करें",
                "सोमवार को शिवलिंग पर कच्चा दूध व जल अर्पित करें",
                "माता का सम्मान करें और प्रतिदिन उनके चरण स्पर्श करें",
                "सोमवार को सफेद चावल, दूध या चांदी का दान करें",
            ],
        },
        "career_fields": {
            "en": ["Fine Arts, Acting & Fashion", "Agriculture & Organic Farming", "Real Estate & Interior Architecture", "Hospitality & Gourmet Restaurants", "Banking & Wealth Management"],
            "bn": ["ললিতকলা, অভিনয় ও ফ্যাশন ডিজাইন", "কৃষি ও অর্গানিক ফার্মিং", "রিয়েল এস্টেট ও ইন্টেরিয়র ডেকরেশন", "হসপিটালিটি ও ফুড ইন্ডাস্ট্রি", "ব্যাংকিং ও সম্পদ ব্যবস্থাপনা"],
            "hi": ["अभिनय, मॉडलिंग व फैशन डिजाइन", "कृषि एवं बागवानी", "इंटीरियर डिजाइनिंग व रियल एस्टेट", "होटल व खानपान व्यवसाय", "बैंकिंग व धन प्रबंधन"],
        },
    },
    {
        "index": 4,
        "name_en": "Mrigashira",
        "name_bn": "মৃগশিরা",
        "name_hi": "मृगशिरा",
        "lord": "Mars",
        "deity_en": "Soma (Moon God / God of Immortal Nectar)",
        "deity_bn": "সোমদেব (অমৃত ও দিব্য জ্যোতির দেবতা)",
        "deity_hi": "सोम देव (चंद्रमा)",
        "symbol_en": "Deer's Head",
        "symbol_bn": "হরিণের মস্তক",
        "symbol_hi": "मृग / हिरण का सिर",
        "gana_en": "Deva",
        "gana_bn": "দেব",
        "gana_hi": "देव",
        "yoni_en": "Serpent (Female)",
        "yoni_bn": "সর্প (স্ত্রী)",
        "yoni_hi": "सर्प (स्त्री)",
        "nadi_en": "Madhya (Pitta)",
        "nadi_bn": "মধ্য (পিত্ত)",
        "nadi_hi": "मध्य (पित्त)",
        "sacred_tree_en": "Khadira / Cutch (Acacia catechu)",
        "sacred_tree_bn": "খয়ের গাছ",
        "sacred_tree_hi": "खैर",
        "beej_mantra": "ॐ সোমায় নমঃ / ॐ ভৌমায় নমঃ",
        "lucky_color_en": "Silver White & Coral Pink",
        "lucky_color_bn": "রুপোলি সাদা ও প্রবাল গোলাপী",
        "lucky_color_hi": "रुपहला श्वेत और मूंगा गुलाबी",
        "lucky_numbers": [9, 2],
        "lucky_gemstone_en": "Red Coral or Pearl",
        "lucky_gemstone_bn": "রক্তপ্রবাল অথবা মুক্তো",
        "lucky_gemstone_hi": "मूंगा अथवा मोती",
        "padas": [
            {"pada": 1, "rashi_idx": 1, "navamsha": "Leo", "namakshar_en": "Ve", "namakshar_bn": "বে", "namakshar_hi": "वे"},
            {"pada": 2, "rashi_idx": 1, "navamsha": "Virgo", "namakshar_en": "Vo", "namakshar_bn": "বো", "namakshar_hi": "वो"},
            {"pada": 3, "rashi_idx": 2, "navamsha": "Libra", "namakshar_en": "Ka", "namakshar_bn": "কা", "namakshar_hi": "का"},
            {"pada": 4, "rashi_idx": 2, "navamsha": "Scorpio", "namakshar_en": "Kee", "namakshar_bn": "কী", "namakshar_hi": "की"},
        ],
        "overview": {
            "en": "Mrigashira represents the eternal search for truth and knowledge. Natives possess inquisitive minds, gentle demeanor, wandering curiosity, and keen research abilities.",
            "bn": "মৃগশিরা চিরন্তন সত্যানুসন্ধান ও জ্ঞানতৃষ্ণার প্রতীক। হরিণের মতো চঞ্চল ও অনুসন্ধানী দৃষ্টির অধিকারী এঁরা অত্যন্ত নম্র, সজ্জন, পর্যটনপ্রিয় ও প্রখর অনুসন্ধিৎসু হন।",
            "hi": "मृगशिरा नक्षत्र ज्ञान और सत्य की निरंतर खोज का प्रतीक है। मृग के समान जिज्ञासु स्वभाव वाले जातक अत्यंत कोमल हृदय, बुद्धिमान और नई बातें सीखने को तत्पर रहते हैं।",
        },
        "strengths": {
            "en": [
                "Unquenchable curiosity, investigative talent, and sharp research skills",
                "Gentle, respectful, and peaceful interpersonal communication",
                "Agile problem solving with a blend of Mars energy and lunar sensitivity",
                "Fondness for travel, exploring new horizons, and open-mindedness",
            ],
            "bn": [
                "চিরঅতৃপ্ত জ্ঞানপিপাসা এবং গভীর গবেষণাধর্মী অনুসন্ধিৎসু মেধা",
                "শান্ত, মার্জিত ও মধুর অমায়িক কথনশৈলী",
                "মঙ্গল ও চন্দ্রের সুষম মিলনে বুদ্ধিদীপ্ত দ্রুত সমস্যা সমাধানের দক্ষতা",
                "ভ্রমণপ্রিয়তা ও নতুন নতুন জ্ঞান ও অভিজ্ঞতার সন্ধানে এগিয়ে চলা",
            ],
            "hi": [
                "असीम जिज्ञासा और गहन अनुसंधान करने की अद्भुत क्षमता",
                "मधुर, शांत और सभी को सम्मान देने वाली संवाद शैली",
                "मंगल की ऊर्जा और चंद्रमा की संवेदनशीलता का श्रेष्ठ संतुलन",
                "यात्रा प्रियता और नई संस्कृतियों व विचारों को जानने की ललक",
            ],
        },
        "cautions_and_pitfalls": {
            "en": [
                "Endless wavering, indecision, and second-guessing every choice",
                "Suspiciousness and over-analyzing relationships into exhaustion",
                "Restless hopping from one project or partner to another",
                "Vocal cord strain, shoulder/arm tensions, and nervous exhaustion",
            ],
            "bn": [
                "সিদ্ধান্তহীনতা—বারবার মত পরিবর্তন করা ও সঠিক পথ বেছে নিতে বিভ্রান্ত হওয়া",
                "সম্পর্কের ক্ষেত্রে অতিরিক্ত সন্দেহপ্রবণতা ও অকারণ চুলচেরা বিশ্লেষণ",
                "এক জায়গায় মন না বসা এবং ঘন ঘন কাজ বা লক্ষ্য বদলানো",
                "গলা ও কাঁধের পেশিতে টান এবং অতিরিক্ত চিন্তায় স্নায়বিক দুর্বলতা",
            ],
            "hi": [
                "निर्णय लेने में अत्यधिक हिचकिचाहट और संशय में फंसे रहना",
                "संबंधों में बेवजह शक करना और अत्यधिक बाल की खाल निकालना",
                "अस्थिरता—एक काम को पूरा किए बिना दूसरे में कूद जाना",
                "कंधों में दर्द, गले में तनाव और मानसिक थकावट",
            ],
        },
        "beneficial_actions_and_remedies": {
            "en": [
                "Feed deer, cattle, or stray animals green foliage",
                "Worship Lord Kartikeya or Lord Shiva on Mondays/Tuesdays",
                "Plant and respect a Khadira tree",
                "Practice anchoring meditation to stabilize restless mind",
            ],
            "bn": [
                "হরিণ বা গবাদি পশুকে কচি পাতা বা শস্য খাওয়ানো শুভ",
                "সোমবার বা মঙ্গলবারে দেবাদিদেব মহাদেব অথবা কার্তিকেয়র আরাধনা",
                "খয়ের গাছের রোপণ ও সেবা করা",
                "মনকে স্থির ও কেন্দ্রীভূত করতে নিয়মিত প্রাণায়াম ও ধ্যান অভ্যাস",
            ],
            "hi": [
                "हिरणों या मवेशियों को हरा चारा खिलाएं",
                "सोमवार या मंगलवार को भगवान कार्तिकेय या शिवजी की पूजा करें",
                "खैर का वृक्ष लगाएं",
                "मन की चंचलता को शांत करने हेतु एकाग्रता से ध्यान लगाएं",
            ],
        },
        "career_fields": {
            "en": ["Investigative Journalism & Media", "Scientific Research & Exploration", "Travel Writing & Tourism", "Textiles, Design & Architecture", "Information Technology & Analytics"],
            "bn": ["তদন্তমূলক সাংবাদিকতা ও মিডিয়া", "বৈজ্ঞানিক গবেষণা ও তথ্য আহরণ", "ভ্রমণ সাহিত্য ও পর্যটন শিল্প", "বস্ত্রশিল্প, ডিজাইন ও স্থাপত্য", "আইটি ও ডেটা অ্যানালিটিক্স"],
            "hi": ["खोजी पत्रकारिता व मीडिया", "वैज्ञानिक अनुसंधान व अन्वेषण", "पर्यटन व यात्रा लेखन", "वस्त्र उद्योग, डिजाइन व वास्तुकला", "आईटी व डेटा विश्लेषण"],
        },
    },
    {
        "index": 5,
        "name_en": "Ardra",
        "name_bn": "আর্দ্রা",
        "name_hi": "आर्द्रा",
        "lord": "Rahu",
        "deity_en": "Rudra (The Storm God & Destroyer of Darkness)",
        "deity_bn": "রুদ্র (মহাপ্রলয় ও অন্ধকার বিনাশকারী)",
        "deity_hi": "रुद्र (भगवान शिव का संहारक रूप)",
        "symbol_en": "Teardrop / Diamond",
        "symbol_bn": "অশ্রুবিন্দু / উজ্জ্বল হীরা",
        "symbol_hi": "अश्रु की बूंद / हीरा",
        "gana_en": "Manushya",
        "gana_bn": "মনুষ্য",
        "gana_hi": "मनुष्य",
        "yoni_en": "Dog (Female)",
        "yoni_bn": "শ্বান / কুকুর (স্ত্রী)",
        "yoni_hi": "श्वान / कुतिया (स्त्री)",
        "nadi_en": "Aadi (Vata)",
        "nadi_bn": "আদি (বাত)",
        "nadi_hi": "आदि (वात)",
        "sacred_tree_en": "Krishna Agaru (Aquilaria agallocha)",
        "sacred_tree_bn": "আগর গাছ (কৃষ্ণকাষ্ঠ)",
        "sacred_tree_hi": "अगर (अगरु)",
        "beej_mantra": "ॐ নমঃ শিবায় / ॐ রাহবে নমঃ",
        "lucky_color_en": "Dark Smoky Violet & Electric Blue",
        "lucky_color_bn": "ধূসর বেগুনী ও গাঢ় নীল",
        "lucky_color_hi": "धूमिल बैंगनी और विद्युत नीला",
        "lucky_numbers": [4, 7],
        "lucky_gemstone_en": "Hessonite Garnet (Gomed)",
        "lucky_gemstone_bn": "গোমেদ",
        "lucky_gemstone_hi": "गोमेद",
        "padas": [
            {"pada": 1, "rashi_idx": 2, "navamsha": "Sagittarius", "namakshar_en": "Ku", "namakshar_bn": "কু", "namakshar_hi": "कु"},
            {"pada": 2, "rashi_idx": 2, "navamsha": "Capricorn", "namakshar_en": "Gha", "namakshar_bn": "ঘ", "namakshar_hi": "घ"},
            {"pada": 3, "rashi_idx": 2, "navamsha": "Aquarius", "namakshar_en": "Nga", "namakshar_bn": "ঙ", "namakshar_hi": "ङ"},
            {"pada": 4, "rashi_idx": 2, "navamsha": "Pisces", "namakshar_en": "Chha", "namakshar_bn": "ছ", "namakshar_hi": "छ"},
        ],
        "overview": {
            "en": "Ardra brings the transformative power of storms and tears that cleanse the soul. Ruled by Rahu and presided over by Rudra, natives possess formidable intellectual depth and breakthrough insights.",
            "bn": "আর্দ্রা ঝড়-তুফানের পর শুদ্ধ হয়ে ওঠা প্রকৃতির মতো আত্মার রূপান্তরের প্রতীক। অশ্রুবিন্দুর মধ্য দিয়ে এঁরা জ্ঞান অর্জন করেন। এঁদের মেধা ক্ষুরধার, অন্তর্দৃষ্টি বিপ্লবী এবং উদ্ভাবনী ক্ষমতাসম্পন্ন।",
            "hi": "आर्द्रा नक्षत्र तूफान के बाद आने वाली निर्मलता और बौद्धिक क्रांति का प्रतीक है। रुद्र के प्रभाव से जातक गहरी अंतर्दृष्टि, वैज्ञानिक सोच और जटिल समस्याओं को सुलझाने में माहिर होते हैं।",
        },
        "strengths": {
            "en": [
                "Profound capacity for breakthrough scientific, technological, and mathematical research",
                "Ability to weather intense emotional storms and emerge resiliently transformed",
                "Honest dismantling of obsolete traditions and bold intellectual courage",
                "Keen memory, razor-sharp debating skills, and analytical brilliance",
            ],
            "bn": [
                "উন্নত বিজ্ঞান, প্রযুক্তি, গণিত ও গবেষণায় যুগান্তকারী আবিষ্কারের মেধা",
                "জীবনের চরম দুর্যোগ কাটিয়ে ফিনিক্স পাখির মতো নতুন উদ্যমে জেগে ওঠার শক্তি",
                "অন্ধবিশ্বাস ও কুসংস্কার ভেঙে আধুনিক যুক্তিবাদী পথে এগিয়ে চলার সাহস",
                "অসাধারণ স্মৃতিশক্তি, ক্ষুরধার যুক্তি এবং জটিল বিষয় সহজে বোঝার ক্ষমতা",
            ],
            "hi": [
                "विज्ञान, तकनीक और अनुसंधान के क्षेत्र में क्रांतिकारी खोज करने की प्रतिभा",
                "कठिन से कठिन संकटों से जूझकर और अधिक मजबूत होकर उभरने का साहस",
                "रूढ़िवादिता को तोड़कर तार्किक दृष्टिकोण अपनाने की निर्भीकता",
                "तीक्ष्ण स्मरण शक्ति और वाद-विवाद में अचूक तर्क क्षमता",
            ],
        },
        "cautions_and_pitfalls": {
            "en": [
                "Harsh outbursts of anger, cynical sarcasm, and emotional coldness",
                "Vulnerability to deep melancholic depression or brooding resentments",
                "Restless obsession leading to sudden relationship sabotage",
                "Respiratory issues, asthma, allergies, and nervous tremors",
            ],
            "bn": [
                "হঠাৎ রুদ্রমূর্তি ধারণ করে ক্রোধের বিস্ফোরণ ও কটূক্তিতে আপনজনকে পর করা",
                "গভীর বিষণ্ণতা, একাকীত্ব ও অতীতের ক্ষতে বারবার ভেঙে পড়া",
                "কোনো বিষয়ে পাগলের মতো মেতে উঠে বাস্তবতার সংযোগ হারিয়ে ফেলা",
                "হাঁপানি, শ্বাসকষ্ট, অ্যালার্জি ও স্নায়বিক অবসাদজনিত সমস্যা",
            ],
            "hi": [
                "अचानक अत्यधिक क्रोधित हो जाना और कटु वचनों से अपनों को दूर कर देना",
                "गहरे अवसाद, अकेलेपन और पुरानी बातों को लेकर कुढ़ते रहना",
                "हठधर्मिता में आकर बने बनाए रिश्तों को बिगाड़ लेना",
                "श्वास संबंधी रोग, एलर्जी और तंत्रिका तंत्र की कमजोरी",
            ],
        },
        "beneficial_actions_and_remedies": {
            "en": [
                "Chant Maha Mrityunjaya Mantra 108 times daily for emotional shield",
                "Offer Bilva leaves and raw milk to Lord Shiva on Mondays",
                "Feed stray dogs lovingly; never harm canines",
                "Donate dark blankets or sesame seeds to homeless people on Saturdays",
            ],
            "bn": [
                "প্রতিদিন শান্ত মনে ১০৮ বার মহামৃত্যুঞ্জয় মন্ত্র জপ মানসিক রক্ষা কবচ গড়ে তোলে",
                "সোমবারে দেবাদিদেব শিবের চরণে গঙ্গাজল ও বেলপাতা নিবেদন",
                "পথের কুকুরদের আহার দেওয়া—কখনও কোনো পশুর ওপর অত্যাচার না করা",
                "শনিবারে কম্বল, কালো তিল বা শুকনো খাদ্য গৃহহীন মানুষকে দান",
            ],
            "hi": [
                "नित्य महामृत्युंजय मंत्र की कम से कम 1 माला (108 बार) जप करें",
                "सोमवार को भगवान शिव पर बेलपत्र और गंगाजल अर्पित करें",
                "सड़क के कुत्तों को रोटी खिलाएं, किसी मूक प्राणी को कष्ट न दें",
                "शनिवार को असहाय लोगों को काले तिल या कंबल का दान करें",
            ],
        },
        "career_fields": {
            "en": ["Software Engineering & AI Architecture", "Meteorology & Atmospheric Sciences", "Pharmaceutical Toxicology & Pathology", "Specialized Surgery & Trauma Medicine", "Investigative Analysis & Cryptography"],
            "bn": ["সফটওয়্যার ইঞ্জিনিয়ারিং ও কৃত্রিম বুদ্ধিমত্তা (AI)", "আবহাওয়া বিজ্ঞান ও পরিবেশবিদ্যা", "টক্সিকোলজি ও রোগতত্ত্ব (প্যাথলজি)", "জরুরি ট্রমা সার্জারি", "ক্রিপ্টোগ্রাফি ও সাইবার গোয়েন্দা"],
            "hi": ["सॉफ्टवेयर इंजीनियरिंग व आर्टिफिशियल इंटेलिजेंस", "मौसम विज्ञान व भूगर्भ शास्त्र", "विष विज्ञान (टॉक्सिकोलॉजी) व पैथोलॉजी", "ट्रॉमा सर्जरी व आपातकालीन चिकित्सा", "साइबर सुरक्षा व कूटलेखन"],
        },
    },
    {
        "index": 6,
        "name_en": "Punarvasu",
        "name_bn": "পুনর্বসু",
        "name_hi": "पुनर्वसु",
        "lord": "Jupiter",
        "deity_en": "Aditi (Cosmic Mother of the Gods)",
        "deity_bn": "অদিতি (দেবমাতা ও অসীমতার দেবী)",
        "deity_hi": "माता अदिति (देवताओं की माता)",
        "symbol_en": "Bow and Quiver of Arrows",
        "symbol_bn": "ধনুক ও বাণভর্তি তূণীর",
        "symbol_hi": "धनुष और बाणों से भरा तरकश",
        "gana_en": "Deva",
        "gana_bn": "দেব",
        "gana_hi": "देव",
        "yoni_en": "Cat (Female)",
        "yoni_bn": "মার্জার / বিড়াল (স্ত্রী)",
        "yoni_hi": "मार्जार / बिल्ली (स्त्री)",
        "nadi_en": "Aadi (Vata)",
        "nadi_bn": "আদি (বাত)",
        "nadi_hi": "आदि (वात)",
        "sacred_tree_en": "Bamboo (Bambusa arundinacea)",
        "sacred_tree_bn": "বাঁশগাছ",
        "sacred_tree_hi": "बांस",
        "beej_mantra": "ॐ বৃহস্পতয়ে নমঃ / ॐ অদিতয়ে নমঃ",
        "lucky_color_en": "Golden Yellow & Saffron",
        "lucky_color_bn": "সোনালী হলুদ ও গেরুয়া",
        "lucky_color_hi": "सुनहरा पीला और केसरिया",
        "lucky_numbers": [3, 1],
        "lucky_gemstone_en": "Yellow Sapphire (Pukhraj)",
        "lucky_gemstone_bn": "পোখরাজ (হলুদ)",
        "lucky_gemstone_hi": "पुखराज (पीला)",
        "padas": [
            {"pada": 1, "rashi_idx": 2, "navamsha": "Aries", "namakshar_en": "Ke", "namakshar_bn": "কে", "namakshar_hi": "के"},
            {"pada": 2, "rashi_idx": 2, "navamsha": "Taurus", "namakshar_en": "Ko", "namakshar_bn": "কো", "namakshar_hi": "को"},
            {"pada": 3, "rashi_idx": 2, "navamsha": "Gemini", "namakshar_en": "Ha", "namakshar_bn": "হা", "namakshar_hi": "हा"},
            {"pada": 4, "rashi_idx": 3, "navamsha": "Cancer", "namakshar_en": "Hee", "namakshar_bn": "হী", "namakshar_hi": "ही"},
        ],
        "overview": {
            "en": "Punarvasu signifies the return of light and renewal of prosperity after hardship. Ruled by Jupiter, natives are philosophical, benevolent, forgiving, and blessed with the ability to rebuild from scratch.",
            "bn": "পুনর্বসু অন্ধকারের পর পুনরায় আলো ফিরে আসার এবং নবজীবনের প্রতীক। দেবগুরু বৃহস্পতি দ্বারা নিয়ন্ত্রিত এই নক্ষত্রের জাতকরা অত্যন্ত নীতিবান, ধার্মিক, পরোপকারী এবং যে কোনো ধ্বংসের মধ্য থেকেও পুনরায় সাফল্য গড়ে তোলার শক্তিসম্পন্ন হন।",
            "hi": "पुनर्वसु नक्षत्र कठिनाइयों के बाद जीवन में प्रकाश और समृद्धि की वापसी का प्रतीक है। गुरु के प्रभाव से जातक उदार, नैतिक, क्षमाशील और हर असफलता के बाद पुनः उठ खड़े होने वाले होते हैं।",
        },
        "strengths": {
            "en": [
                "Extraordinary resilience; arrows that return safely to the quiver",
                "Spiritual magnanimity, genuine contentment, and high moral character",
                "Natural talent in teaching, mentorship, writing, and counseling",
                "Inherent purity of thought and maternal protective devotion",
            ],
            "bn": [
                "অসাধারণ পুনরুত্থান ক্ষমতা—প্রতিটি বিপত্তি থেকে আরও শক্তি নিয়ে ঘুরে দাঁড়ানো",
                "আধ্যাত্মিক মহত্ত্ব, অন্তরের তৃপ্তি ও নিখাদ নৈতিক সততা",
                "শিক্ষকতা, পরামর্শদান, সাহিত্য ও পথপ্রদর্শনের দুর্লভ নৈপুণ্য",
                "মাতৃস্নেহসুলভ ক্ষমাশীলতা ও সকলকে কাছে টেনে নেওয়ার উদার প্রবৃত্তি",
            ],
            "hi": [
                "अद्भुत पुनरुत्थान शक्ति—हर विफलता को सफलता में बदलने का हुनर",
                "आध्यात्मिक दृष्टिकोण, संतोषी स्वभाव और उच्च नैतिक आचरण",
                "शिक्षण, मार्गदर्शन, लेखन और परामर्श में असाधारण दक्षता",
                "मातृत्व जैसा स्नेह, क्षमाशीलता और अपनों की रक्षा का भाव",
            ],
        },
        "cautions_and_pitfalls": {
            "en": [
                "Complacency, lack of intense material ambition, or becoming too passive",
                "Risk of over-trusting unworthy people who repeatedly take advantage",
                "Frequent changes of home or direction due to wandering restlessness",
                "Digestive sluggishness, liver sensitivities, or lung congestion",
            ],
            "bn": [
                "অতিরিক্ত সন্তুষ্টি বা পার্থিব উচ্চাকাঙ্ক্ষার অভাবে সহজে হাল ছেড়ে দেওয়া",
                "অযোগ্য ব্যক্তিকে বারবার বিশ্বাস করে প্রতারিত হওয়ার ঝুঁকি",
                "এক জায়গায় স্থায়ী হতে না পেরে বারবার বাসস্থান বা পথ পরিবর্তন",
                "হজমশক্তি হ্রাস, যকৃতের (লিভার) সমস্যা বা ফুসফুসে কফ জমা",
            ],
            "hi": [
                "अति-संतोषी होकर भौतिक प्रयासों में ढिलाई बरत देना",
                "गलत लोगों पर बार-बार भरोसा करके धोखा खाने की संभावना",
                "मन की अस्थिरता के कारण बार-बार स्थान अथवा लक्ष्य बदलना",
                "पाचन तंत्र की सुस्ती, यकृत (लीवर) व फेफड़ों के विकार",
            ],
        },
        "beneficial_actions_and_remedies": {
            "en": [
                "Plant and nurture bamboo clusters or keep bamboo plants at home",
                "Worship Lord Rama or Lord Vishnu with Tulsi leaves on Thursdays",
                "Respect teachers, gurus, and motherly figures unconditionally",
                "Donate bananas, yellow lentils, or turmeric to temples on Thursdays",
            ],
            "bn": [
                "বাড়িতে বা বাগানে বাঁশগাছ বা শুভ লাকি ব্যাম্বু রাখা কল্যাণকর",
                "বৃহস্পতিবারে শ্রীরামচন্দ্র বা ভগবান বিষ্ণুর চরণে তুলসীপত্র নিবেদন",
                "গুরুজন, শিক্ষক এবং মাতৃস্থানীয় ব্যক্তিদের শ্রদ্ধা ও সেবা করা",
                "বৃহস্পতিবারে কলা, ছোলার ডাল, হলুদ বা ধর্মগ্রন্থ দরিদ্রকে দান",
            ],
            "hi": [
                "बांस का पौधा लगाएं अथवा घर में सकारात्मकता हेतु बांस का पौधा रखें",
                "गुरुवार को भगवान विष्णु या श्रीराम को तुलसी पत्र अर्पित करें",
                "गुरुओं, शिक्षकों और माता-पिता का नित्य चरण वंदन करें",
                "गुरुवार को चने की दाल, केले या पीले वस्त्रों का दान करें",
            ],
        },
        "career_fields": {
            "en": ["Higher Education & Academia", "Philosophy, Theology & Publishing", "Civil Aviation & Space Sciences", "Counseling & Psychotherapy", "Philanthropy & Humanitarian Non-Profits"],
            "bn": ["উচ্চশিক্ষা ও বিশ্ববিদ্যালয় অধ্যাপনা", "দর্শন, ধর্মতত্ত্ব ও উচ্চমানের প্রকাশনা", "বিমানচালনা ও মহাকাশ গবেষণা", "কাউন্সেলিং ও মনস্তাত্ত্বিক পরামর্শ", "জনকল্যাণমূলক ও দাতব্য সংস্থা"],
            "hi": ["उच्च शिक्षा व विश्वविद्यालय शिक्षण", "दर्शनशास्त्र, धर्म व प्रकाशन", "विमानन व अंतरिक्ष विज्ञान", "परामर्श व मनोविज्ञान", "परोपकार व गैर-सरकारी संगठन"],
        },
    },
    {
        "index": 7,
        "name_en": "Pushya",
        "name_bn": "পুষ্যা",
        "name_hi": "पुष्य",
        "lord": "Saturn",
        "deity_en": "Brihaspati (Preceptor of the Gods)",
        "deity_bn": "বৃহস্পতি (দেবতাদের পরম গুরু)",
        "deity_hi": "देवगुरु बृहस्पति",
        "symbol_en": "Cow's Udder / Lotus Flower / Circle",
        "symbol_bn": "ধেনুর বাঁট / প্রস্ফুটিত পদ্ম / বৃত্ত",
        "symbol_hi": "गाय का थन / कमल का फूल",
        "gana_en": "Deva",
        "gana_bn": "দেব",
        "gana_hi": "देव",
        "yoni_en": "Goat / Sheep (Male)",
        "yoni_bn": "মেষ / ছাগল (পুং)",
        "yoni_hi": "मेष / बकरा (पुरुष)",
        "nadi_en": "Madhya (Pitta)",
        "nadi_bn": "মধ্য (পিত্ত)",
        "nadi_hi": "मध्य (पित्त)",
        "sacred_tree_en": "Peepal / Sacred Fig (Ficus religiosa)",
        "sacred_tree_bn": "অশ্বত্থ গাছ",
        "sacred_tree_hi": "पीपल",
        "beej_mantra": "ॐ বৃহস্পতয়ে নমঃ / ॐ শনৈশ্চরায় নমঃ",
        "lucky_color_en": "Royal Navy Blue & Turmeric Yellow",
        "lucky_color_bn": "গাঢ় নীল ও কাঁচা হলুদ",
        "lucky_color_hi": "शाही नीला और हल्दी पीला",
        "lucky_numbers": [8, 3],
        "lucky_gemstone_en": "Blue Sapphire (Neelam) or Yellow Sapphire",
        "lucky_gemstone_bn": "নীলা অথবা পোখরাজ",
        "lucky_gemstone_hi": "नीलम अथवा पुखराज",
        "padas": [
            {"pada": 1, "rashi_idx": 3, "navamsha": "Leo", "namakshar_en": "Hu", "namakshar_bn": "হু", "namakshar_hi": "हू"},
            {"pada": 2, "rashi_idx": 3, "navamsha": "Virgo", "namakshar_en": "He", "namakshar_bn": "হে", "namakshar_hi": "हे"},
            {"pada": 3, "rashi_idx": 3, "navamsha": "Libra", "namakshar_en": "Ho", "namakshar_bn": "হো", "namakshar_hi": "हो"},
            {"pada": 4, "rashi_idx": 3, "navamsha": "Scorpio", "namakshar_en": "Da", "namakshar_bn": "ডা", "namakshar_hi": "डा"},
        ],
        "overview": {
            "en": "Considered the most auspicious among the 27 nakshatras, Pushya represents nourishment, spiritual guardianship, and enduring prosperity. Ruled by Saturn and presided by Brihaspati, natives are wise, disciplined, and deeply caring.",
            "bn": "২৭টি নক্ষত্রের মধ্যে পুষ্যাকে সর্বোত্তম ও পরম শুভ বলে গণ্য করা হয়। এটি পুষ্টি, ধর্মরক্ষা এবং অক্ষয় সমৃদ্ধির প্রতীক। শনির অনুশাসন ও দেবগুরু বৃহস্পতির কৃপায় এঁরা অত্যন্ত জ্ঞানী, গম্ভীর, ধৈর্যশীল ও সমাজহিতৈষী হন।",
            "hi": "पुष्य को सभी 27 नक्षत्रों में सबसे अधिक कल्याणकारी माना गया है। यह पोषण, धर्म और स्थायी समृद्धि का प्रतीक है। शनि के अनुशासन और गुरु के ज्ञान से जातक अत्यंत विवेकशील व परोपकारी होते हैं।",
        },
        "strengths": {
            "en": [
                "Unmatched power to nourish, guide, and protect community and family",
                "Deep spiritual discipline, patience, and unwavering moral grounding",
                "Steadfast loyalty, emotional wisdom, and trusted counsel",
                "Capacity to create lasting philanthropic institutions and sustained wealth",
            ],
            "bn": [
                "পরিবার ও সমাজকে অন্ন, বস্ত্র ও স্নেহে পুষ্ট করার অপূর্ব মহত্ত্ব",
                "গভীর আধ্যাত্মিক নিষ্ঠা, অনন্ত ধৈর্য এবং অনড় নৈতিক ভিত্তি",
                "বিশ্বস্ত বন্ধু, নির্ভরযোগ্য উপদেষ্টা এবং সুবিচারক সত্ত্বা",
                "দীর্ঘমেয়াদী প্রতিষ্ঠান ও অক্ষয় অর্থনৈতিক সমৃদ্ধি গড়ে তোলার মেধা",
            ],
            "hi": [
                "परिवार और समाज का पालन-पोषण व संरक्षण करने का महान गुण",
                "गहरा आध्यात्मिक संयम, धैर्य और उच्च नैतिक आदर्श",
                "सच्ची मित्रता, विश्वसनीयता और निष्पक्ष परामर्श देने की क्षमता",
                "दीर्घकालिक संस्थाओं और स्थायी संपत्ति का निर्माण करने का कौशल",
            ],
        },
        "cautions_and_pitfalls": {
            "en": [
                "Rigid orthodoxy, dogmatic views, and resistance to modern changes",
                "Over-sacrificing self-interest until emotional burnout occurs",
                "Suspicion of unconventional ideas or outside outsiders",
                "Chest congestion, gall bladder sensitivities, and water retention",
            ],
            "bn": [
                "অতিরিক্ত গোঁড়ামি, প্রাচীন সংস্কারে অনড় থাকা ও পরিবর্তন গ্রহণে দ্বিধা",
                "নিজের সুখশান্তি বিসর্জন দিয়ে অন্যের জন্য অতিরিক্ত আত্মত্যাগ",
                "নতুন বা আধুনিক চিন্তাধারার প্রতি অহেতুক অনীহা ও সন্দেহ",
                "বুকের সংক্রমণ, কফ-কাশি ও পিত্তাশয়ের দুর্বলতা",
            ],
            "hi": [
                "रूढ़िवादी दृष्टिकोण और बदलाव को आसानी से स्वीकार न करना",
                "दूसरों के लिए इतना त्याग कर देना कि स्वयं मानसिक तनाव में आ जाएं",
                "नए विचारों या आधुनिक सोच पर संदेह करना",
                "छाती में जकड़न, कफ जनित विकार और पित्ताशय संबंधी समस्याएं",
            ],
        },
        "beneficial_actions_and_remedies": {
            "en": [
                "Circumambulate a Sacred Peepal tree on Saturdays; water its roots",
                "Worship Brihaspati and recite Guru Stotra on Thursdays",
                "Feed dairy products or sweet roti to cows on Thursdays",
                "Donate warm meals, sesame, or mustard oil to needy laborers on Saturdays",
            ],
            "bn": [
                "শনিবারে অশ্বত্থ গাছে জল দেওয়া এবং তাকে প্রদক্ষিণ করা পরম শুভ",
                "বৃহস্পতিবারে দেবগুরু বৃহস্পতির ধ্যান ও গুরুস্তোত্র পাঠ",
                "গরুকে গুড়-রুটি বা কাঁচা ঘাস আহার করানো",
                "শনিবার দুঃস্থ মেহনতী মানুষকে গরম আহার বা সরিষার তেল দান",
            ],
            "hi": [
                "शनिवार को पीपल के वृक्ष की जड़ में जल अर्पित करें और परिक्रमा करें",
                "गुरुवार को देवगुरु बृहस्पति का पूजन और गुरु मंत्र का जप करें",
                "गौमाता को गुड़, रोटी अथवा हरा चारा खिलाएं",
                "शनिवार को जरूरतमंद श्रमिकों को भोजन अथवा सरसों का तेल दान करें",
            ],
        },
        "career_fields": {
            "en": ["Judiciary, Law & Constitutional Governance", "Religious Leadership & Vedic Teaching", "Agriculture, Dairy & Food Security", "Public Service & Social Reform", "Wealth Trusts & Heritage Preservation"],
            "bn": ["আইন, বিচারবিভাগ ও সাংবিধানিক প্রশাসন", "ধর্মীয় নেতৃত্ব ও বেদ/উপনিষদ শিক্ষকতা", "কৃষি, দুগ্ধশিল্প ও খাদ্য সুরক্ষা", "জনকল্যাণ ও সমাজ সংস্কার", "ঐতিহ্য সংরক্ষণ ও ট্রাস্ট ম্যানেজমেন্ট"],
            "hi": ["न्यायिक सेवा, कानून व उच्च प्रशासन", "धार्मिक नेतृत्व व वैदिक शिक्षण", "कृषि, दुग्ध उद्योग व खाद्य सुरक्षा", "समाज सेवा व लोक कल्याण", "ट्रस्ट प्रबंधन व पुरातत्व संरक्षण"],
        },
    },
    {
        "index": 8,
        "name_en": "Ashlesha",
        "name_bn": "অশ্লেষা",
        "name_hi": "आश्लेषा",
        "lord": "Mercury",
        "deity_en": "Nagas / Sarpas (Serpent Deities of Hidden Wisdom)",
        "deity_bn": "নাগদেবতা (গোপন জ্ঞান ও কুন্ডলিনী শক্তির প্রতীক)",
        "deity_hi": "नाग देव (सर्प राज)",
        "symbol_en": "Coiled Serpent",
        "symbol_bn": "কুন্ডলীকৃত সর্প",
        "symbol_hi": "कुंडली मारे सर्प",
        "gana_en": "Rakshasa",
        "gana_bn": "রাক্ষস",
        "gana_hi": "राक्षस",
        "yoni_en": "Cat (Male)",
        "yoni_bn": "মার্জার / বিড়াল (পুং)",
        "yoni_hi": "मार्जार / बिलाव (पुरुष)",
        "nadi_en": "Antya (Kapha)",
        "nadi_bn": "অন্ত্য (কফ)",
        "nadi_hi": "अंत्य (कফ)",
        "sacred_tree_en": "Nagkesar (Mesua ferrea)",
        "sacred_tree_bn": "নাগকেশর",
        "sacred_tree_hi": "नागकेसर",
        "beej_mantra": "ॐ বুধায় নমঃ / ॐ সর্পায় নমঃ",
        "lucky_color_en": "Emerald Green & Deep Indigo",
        "lucky_color_bn": "পান্না সবুজ ও গাঢ় নীল",
        "lucky_color_hi": "पन्ना हरा और गहरा नीला",
        "lucky_numbers": [5, 9],
        "lucky_gemstone_en": "Emerald (Panna)",
        "lucky_gemstone_bn": "পান্না",
        "lucky_gemstone_hi": "पन्ना",
        "padas": [
            {"pada": 1, "rashi_idx": 3, "navamsha": "Sagittarius", "namakshar_en": "Dee", "namakshar_bn": "ডী", "namakshar_hi": "डी"},
            {"pada": 2, "rashi_idx": 3, "navamsha": "Capricorn", "namakshar_en": "Du", "namakshar_bn": "ডু", "namakshar_hi": "डू"},
            {"pada": 3, "rashi_idx": 3, "navamsha": "Aquarius", "namakshar_en": "De", "namakshar_bn": "ডে", "namakshar_hi": "डे"},
            {"pada": 4, "rashi_idx": 3, "navamsha": "Pisces", "namakshar_en": "Do", "namakshar_bn": "ডো", "namakshar_hi": "डो"},
        ],
        "overview": {
            "en": "Ashlesha embodies the hypnotic, penetrating power of the mystical serpent. Ruled by Mercury, natives possess psychological penetration, occult mastery, magnetic gaze, and fierce defense mechanisms.",
            "bn": "অশ্লেষা রহস্যময় সর্পশক্তির প্রতীক, যা কুন্ডলিনী ও গোপন জ্ঞানের আধার। বুধ নিয়ন্ত্রিত এই নক্ষত্রের মানুষ প্রখর মনস্তাত্ত্বিক দূরদৃষ্টি, সম্মোহনী দৃষ্টি, গভীর গবেষণা ক্ষমতা ও নিজস্ব গণ্ডি রক্ষার ক্ষেত্রে অত্যন্ত সতর্ক হন।",
            "hi": "आश्लेषा नक्षत्र नाग शक्ति और गूढ़ विद्याओं का प्रतीक है। बुध के प्रभाव से जातक अद्भुत मनोवैज्ञानिक समझ, सम्मोहक दृष्टि, तीक्ष्ণ बुद्धि और गुप्त रहस्यों को जानने में प्रवीण होते हैं।",
        },
        "strengths": {
            "en": [
                "Profound psychological insight; instantly senses hidden motives and deceptions",
                "Mastery over strategic planning, confidential intelligence, and negotiation",
                "Powerful healing abilities through knowledge of poisons, herbs, and chemistry",
                "Deep concentration and capacity for esoteric or occult sciences",
            ],
            "bn": [
                "অসাধারণ মনস্তাত্ত্বিক উপলব্ধি—অন্যের মনের গোপন মতলব মুহূর্তে ধরে ফেলার ক্ষমতা",
                "কূটনৈতিক কৌশল, গোপন তথ্যের বিশ্লেষণ ও দরকষাকষিতে শ্রেষ্ঠত্ব",
                "ভেষজ শাস্ত্র, বিষবিদ্যা, রসায়ন ও আয়ুর্বেদ চিকিৎসায় অনন্য মেধা",
                "গভীর একাগ্রতা এবং তন্ত্র, যোগ ও আধ্যাত্মিক বিজ্ঞানে সফল সাধনা",
            ],
            "hi": [
                "अद्भुत मनोवैज्ञानिक अंतर्दृष्टि—सामने वाले के मन की बात तुरंत भांप लेना",
                "कूटनीतिक रणनीति, गुप्तचर विश्लेषण और बातचीत में माहिर",
                "औषधि विज्ञान, रसायन शास्त्र और उपचार कला में विशेष रुचि",
                "गहन एकाग्रता और गुप्त व आध्यात्मिक विद्याओं में पारंगत",
            ],
        },
        "cautions_and_pitfalls": {
            "en": [
                "Excessive suspicion, paranoia, and manipulative plotting",
                "Venomous verbal retaliation when feeling crossed or insecure",
                "Secretiveness alienating loving family members and partners",
                "Digestive toxicity, liver sluggishness, or lymphatic stagnation",
            ],
            "bn": [
                "অতিরিক্ত সন্দেহপ্রবণতা, ষড়যন্ত্রের আশঙ্কা এবং কূটকৌশল ব্যবহারের প্রবৃত্তি",
                "আঘাত পেলে বা বিশ্বাসঘাতকতার আশঙ্কায় বিষাক্ত বাক্যবাণে চরম প্রতিশোধ",
                "অতিরিক্ত গোপনীয়তা যা ঘনিষ্ঠ আপনজনদেরও দূরে ঠেলে দেয়",
                "পেটের বিষক্রিয়া, যকৃতের সমস্যা ও হজমে গোলযোগ",
            ],
            "hi": [
                "अत्यधिक अविश्वास, शक्की मिजाज और छल-कपट की ओर झुकाव",
                "क्रोध में आकर अत्यंत विषैले शब्दों से प्रहार करना",
                "अत्यधिक गोपनीयता बनाए रखकर अपनों से ही दूरी बना लेना",
                "पेट में विषाक्तता (टॉक्सिन), लीवर की सुस्ती और कब्ज",
            ],
        },
        "beneficial_actions_and_remedies": {
            "en": [
                "Worship Lord Shiva and Nag Devata; offer milk on Nag Panchami",
                "Chant Maha Mrityunjaya Mantra or Rahu-Ketu shanti mantras",
                "Plant and tend a Nagkesar tree",
                "Avoid hoarding secrets; practice transparent honesty with loved ones",
            ],
            "bn": [
                "দেবাদিদেব শিবের আরাধনা এবং নাগপঞ্চমীতে সর্পদেবতার উদ্দেশ্যে দুধ নিবেদন",
                "প্রতিদিন মহামৃত্যুঞ্জয় মন্ত্র জপ মনকে শান্ত ও অহিংস রাখে",
                "নাগকেশর গাছের চারা রোপণ ও পরিচর্যা করা",
                "আপনজনদের কাছে সত্য গোপন না করে স্বচ্ছ ও সরল সম্পর্ক রক্ষা করা",
            ],
            "hi": [
                "भगवान शिव की पूजा करें और नागपंचमी पर नाग देवता को दूध अर्पित करें",
                "नित्य महामृत्युंजय मंत्र का पाठ करें",
                "नागकेसर का पौधा लगाएं",
                "अपनों के साथ पारदर्शिता बनाए रखें और अकारण शक करने से बचें",
            ],
        },
        "career_fields": {
            "en": ["Intelligence & Espionage Analysis", "Psychiatry & Psychoanalysis", "Pharmacology & Toxicological Research", "Strategic Corporate Diplomacy", "Occult Astrology & Esoteric Sciences"],
            "bn": ["গোয়েন্দা বিভাগ ও সাইবার সিকিউরিটি", "মনোচিকিৎসা ও সাইকোঅ্যানালিসিস", "ফার্মাকোলজি ও টক্সিকোলজি গবেষণা", "কূটনীতি ও করপোরেট স্ট্র্যাটেজি", "গুপ্ত জ্যোতিষ ও তন্ত্র সাধনা"],
            "hi": ["खुफिया एजेंसी व जासूसी विश्लेषण", "मनोचिकित्सा व मानसिक परामर्श", "दवा अनुसंधान व विष विज्ञान", "रणनीतिक कूटनीति व समझौता वार्ता", "गूढ़ ज्योतिष व रहस्य विज्ञान"],
        },
    },
    {
        "index": 9,
        "name_en": "Magha",
        "name_bn": "মঘা",
        "name_hi": "मघा",
        "lord": "Ketu",
        "deity_en": "Pitris (Ancestral Spirits & Forefathers)",
        "deity_bn": "পিতৃপুরুষগণ (পূর্বপুরুষদের দিব্য আত্মা)",
        "deity_hi": "पितृ देव (पूर्वज)",
        "symbol_en": "Royal Throne / Palanquin",
        "symbol_bn": "রাজসিংহাসন / রাজকীয় পালকি",
        "symbol_hi": "राज सिंहासन / पालकी",
        "gana_en": "Rakshasa",
        "gana_bn": "রাক্ষস",
        "gana_hi": "राक्षस",
        "yoni_en": "Rat (Male)",
        "yoni_bn": "মূষিক / ইঁদুর (পুং)",
        "yoni_hi": "मूषक / चूहा (पुरुष)",
        "nadi_en": "Antya (Kapha)",
        "nadi_bn": "অন্ত্য (কফ)",
        "nadi_hi": "अंत्य (कफ)",
        "sacred_tree_en": "Banyan Tree (Ficus benghalensis)",
        "sacred_tree_bn": "বটগাছ",
        "sacred_tree_hi": "बरगद (वट)",
        "beej_mantra": "ॐ পিতৃভ্যো নমঃ / ॐ কেতবে নমঃ",
        "lucky_color_en": "Royal Gold & Ivory",
        "lucky_color_bn": "রাজকীয় সোনালী ও হাতির দাঁতের শুভ্র",
        "lucky_color_hi": "शाही सुनहरा और हाथी दांत श्वेत",
        "lucky_numbers": [1, 9],
        "lucky_gemstone_en": "Cat's Eye (Vaidurya) or Ruby",
        "lucky_gemstone_bn": "ক্যাটস আই অথবা চুনি",
        "lucky_gemstone_hi": "लहसुनिया अथवा माणिक्य",
        "padas": [
            {"pada": 1, "rashi_idx": 4, "navamsha": "Aries", "namakshar_en": "Ma", "namakshar_bn": "মা", "namakshar_hi": "मा"},
            {"pada": 2, "rashi_idx": 4, "navamsha": "Taurus", "namakshar_en": "Mee", "namakshar_bn": "মী", "namakshar_hi": "मी"},
            {"pada": 3, "rashi_idx": 4, "navamsha": "Gemini", "namakshar_en": "Mu", "namakshar_bn": "মু", "namakshar_hi": "मू"},
            {"pada": 4, "rashi_idx": 4, "navamsha": "Cancer", "namakshar_en": "Me", "namakshar_bn": "মে", "namakshar_hi": "मे"},
        ],
        "overview": {
            "en": "Magha is the seat of royal power, ancestral lineage, and noble authority. Presided over by the Pitris and ruled by Ketu, natives carry regal dignity, deep respect for lineage, and leadership command.",
            "bn": "মঘা রাজসিংহাসন, কৌলীন্য এবং পিতৃপুরুষদের আশীর্বাদের দ্যোতক। কেতু নিয়ন্ত্রিত এবং পিতৃগণের অধিষ্ঠিত এই নক্ষত্রের মানুষ সহজাত রাজকীয় মর্যাদা, বংশমর্যাদা রক্ষা এবং বলিষ্ঠ কর্তৃত্বের অধিকারী হন।",
            "hi": "मघा नक्षत्र राजसत्ता, पैतृक गौरव और नेतृत्व का प्रतीक है। पितरों के आशीर्वाद और केतु के प्रभाव से जातक स्वाभिमानी, उच्च पद प्राप्त करने वाले और कुल की प्रतिष्ठा बढ़ाने वाले होते हैं।",
        },
        "strengths": {
            "en": [
                "Commanding natural authority, regal bearing, and inspiring executive presence",
                "Deep reverence for traditions, ancestral heritage, and historical wisdom",
                "High generosity towards loyal subjects and uncompromising personal honor",
                "Capacity to achieve high social status and monumental organizational success",
            ],
            "bn": [
                "সহজাত রাজকীয় ব্যক্তিত্ব, নেতৃত্বের ক্ষমতা ও সভায় মান্যতা",
                "বংশপরম্পরা, ইতিহাস, ঐতিহ্য ও প্রাচীন সংস্কৃতির প্রতি গভীর শ্রদ্ধা",
                "বিশ্বস্ত অনুগামীদের প্রতি মুক্তহস্ত দানশীলতা ও আত্মমর্যাদাবোধ",
                "সমাজে শীর্ষপদে পৌঁছানো এবং সুবৃহৎ সংগঠন পরিচালনার দক্ষতা",
            ],
            "hi": [
                "प्रभावशाली व्यक्तित्व, राजसी शान और स्वाभिमानी स्वभाव",
                "अपने पूर्वजों, संस्कृति और परंपराओं के प्रति अगाध आदर",
                "उदारता, निष्ठावान लोगों की सहायता और कभी स्वाभिमान से न डिगना",
                "समाज में उच्च प्रतिष्ठा और बड़े संगठनों का सफल संचालन",
            ],
        },
        "cautions_and_pitfalls": {
            "en": [
                "Excessive pride, arrogance, and looking down upon others as inferiors",
                "Inability to accept criticism or apologize for mistakes",
                "Heavy ancestral karmic obligations requiring regular reconciliation",
                "Heart palpitations, spinal stiffness, and high blood pressure",
            ],
            "bn": [
                "অতিরিক্ত অহংকার, আত্মাভিমান এবং অন্যকে হেয় দেখার প্রবণতা",
                "নিজের ভুল স্বীকার করতে না পারা এবং সমালোচনা সহ্য করতে না পারা",
                "পিতৃপুরুষদের অতৃপ্ত কর্মের প্রভাবজনিত পারিবারিক অশান্তি",
                "হৃদস্পন্দন দ্রুত হওয়া, রক্তচাপ বৃদ্ধি ও মেরুদণ্ডের সমস্যা",
            ],
            "hi": [
                "अत्यधिक अहंकार और दूसरों को अपने से कमतर आंकने की भूल",
                "अपनी गलती स्वीकार न करना और आलोचना से तिलमिला जाना",
                "पितृ दोष या पूर्वजों के ऋण के कारण पारिवारिक रुकावटें",
                "हृदय संबंधी विकार, रीढ़ की हड्डी में दर्द व उच्च रक्तचाप",
            ],
        },
        "beneficial_actions_and_remedies": {
            "en": [
                "Perform Pitru Tarpana on Amavasya; offer water to ancestors",
                "Plant and water a sacred Banyan tree",
                "Worship Lord Ganesha and Lord Shiva regularly",
                "Donate meals, clothes, or silver to elderly relatives or orphanages",
            ],
            "bn": [
                "প্রতি অমাবস্যায় পিতৃপুরুষদের উদ্দেশ্যে তর্পণ বা জলদান করা পরম কর্তব্য",
                "বটগাছ রোপণ করা অথবা বটবৃক্ষের গোড়ায় জল ঢালা",
                "শ্রী গণেশ ও দেবাদিদেব মহাদেবের উপাসনা করা",
                "পরিবারের প্রবীণদের সেবা করা এবং বৃদ্ধাশ্রমে আহার ও বস্ত্র দান",
            ],
            "hi": [
                "अमावस्या को पितरों के निमित्त तर्पण अथवा जल व अन्न दान करें",
                "बरगद (वट वृक्ष) का पौधा लगाएं और उसकी रक्षा करें",
                "भगवान गणेश और शिवजी की नित्य पूजा करें",
                "बुजुर्गों का आदर करें और वृद्धाश्रम में भोजन व वस्त्र दान करें",
            ],
        },
        "career_fields": {
            "en": ["State Politics & Government Ministries", "Executive Leadership & Board Governance", "Archaeology, History & Ancestral Archives", "Judiciary & High Administrative Service", "Heritage Conservation & Royal Trusts"],
            "bn": ["রাজনীতি ও সরকারি মন্ত্রক", "শীর্ষ কর্পোরেট এক্সিকিউটিভ ও ডিরেক্টর", "প্রত্নতত্ত্ব, ইতিহাস ও মহাফেজখানা", "বিচারবিভাগ ও ভারতীয় প্রশাসনিক সেবা (IAS)", "ঐতিহ্যবাহী ট্রাস্ট ও রাজকীয় সম্পদ রক্ষা"],
            "hi": ["राजनीति व शासन-प्रशासन", "उच्च स्तरीय प्रबंधन व कंपनी निदेशक", "पुरातत्व, इतिहास व अभिलेखागार", "न्यायिक व सिविल सेवाएं (IAS/IPS)", "विरासत संरक्षण व ट्रस्ट प्रबंधन"],
        },
    },
    {
        "index": 10,
        "name_en": "Purva Phalguni",
        "name_bn": "পূর্বাফাল্গুনী",
        "name_hi": "पूर्वाफाल्गुनी",
        "lord": "Venus",
        "deity_en": "Bhaga (God of Fortune, Prosperity & Affection)",
        "deity_bn": "ভগদেব (ভাগ্য, বৈবাহিক প্রেম ও ঐশ্বর্যের দেবতা)",
        "deity_hi": "भग देव (भाग्य व सौभाग्य के देवता)",
        "symbol_en": "Front Legs of Bed / Hammock",
        "symbol_bn": "পালঙ্কের অগ্রভাগ / দোলনা",
        "symbol_hi": "पलंग के आगे के पाए / झूला",
        "gana_en": "Manushya",
        "gana_bn": "মনুষ্য",
        "gana_hi": "मनुष्य",
        "yoni_en": "Rat (Female)",
        "yoni_bn": "মূষিক / ইঁদুর (স্ত্রী)",
        "yoni_hi": "मूषक / चूहा (स्त्री)",
        "nadi_en": "Madhya (Pitta)",
        "nadi_bn": "মধ্য (পিত্ত)",
        "nadi_hi": "मध्य (पित्त)",
        "sacred_tree_en": "Palash / Flame of the Forest (Butea monosperma)",
        "sacred_tree_bn": "পলাশ গাছ",
        "sacred_tree_hi": "पलाश (ढाक)",
        "beej_mantra": "ॐ শুক্রায় নমঃ / ॐ ভগায় নমঃ",
        "lucky_color_en": "Coral Pink & Cream White",
        "lucky_color_bn": "প্রবাল গোলাপী ও ননী সাদা",
        "lucky_color_hi": "गुलाबी और मखमली श्वेत",
        "lucky_numbers": [6, 1],
        "lucky_gemstone_en": "Diamond (Heera) or Opal",
        "lucky_gemstone_bn": "হীরে অথবা ওপাল",
        "lucky_gemstone_hi": "हीरा अथवा ओपल",
        "padas": [
            {"pada": 1, "rashi_idx": 4, "navamsha": "Leo", "namakshar_en": "Mo", "namakshar_bn": "মো", "namakshar_hi": "मो"},
            {"pada": 2, "rashi_idx": 4, "navamsha": "Virgo", "namakshar_en": "Ta", "namakshar_bn": "টা", "namakshar_hi": "टा"},
            {"pada": 3, "rashi_idx": 4, "navamsha": "Libra", "namakshar_en": "Tee", "namakshar_bn": "টী", "namakshar_hi": "टी"},
            {"pada": 4, "rashi_idx": 4, "navamsha": "Scorpio", "namakshar_en": "Too", "namakshar_bn": "টূ", "namakshar_hi": "टू"},
        ],
        "overview": {
            "en": "Purva Phalguni represents relaxed celebration, romantic delight, and creative fertility. Ruled by Venus in the solar sign Leo, natives love beauty, social harmony, arts, and joyous leisure.",
            "bn": "পূর্বাফাল্গুনী আনন্দোৎসব, দাম্পত্য সুখ এবং সৃজনশীল বিলাসিতার প্রতীক। শুক্রের রূপলাবণ্য এবং সূর্যের তেজের মিলনে এঁরা আকর্ষণীয় ব্যক্তিত্ব, সুরসিক স্বভাব, শিল্পপ্রিয় এবং সামাজিক মেলামেশায় অগ্রণী হন।",
            "hi": "पूर्वाफाल्गुनी नक्षत्र आनंद, प्रेम, विश्राम और कलात्मकता का प्रतीक है। सूर्य की सिंह राशि में शुक्र का यह नक्षत्र जातक को अत्यंत आकर्षक, सामाजिक, कलाप्रेमी और जीवन का आनंद लेने वाला बनाता है।",
        },
        "strengths": {
            "en": [
                "Effortless social charm, theatrical talent, and magnetic appeal",
                "Warm generosity, romantic loyalty, and celebration of life",
                "Exquisite taste in apparel, entertainment, fine dining, and decoration",
                "Ability to resolve tense conflicts through gentle affection and diplomacy",
            ],
            "bn": [
                "সহজাত সামাজিক আকর্ষণ, নাট্য ও সঙ্গীত প্রতিভা এবং নজরকাড়া ব্যক্তিত্ব",
                "উদার মনোভাব, নিখাদ প্রেম এবং জীবনকে প্রতিটি মুহূর্তে উপভোগ করার ক্ষমতা",
                "পোশাকআশাক, গৃহসজ্জা ও শিল্পকলার বিষয়ে অত্যন্ত রুচিশীল পছন্দ",
                "শান্ত ও মিষ্টি কথার মাধ্যমে যে কোনো কঠিন বিবাদ মিটিয়ে ফেলার ক্ষমতা",
            ],
            "hi": [
                "मनमोहक सामाजिक व्यवहार, अभिनय व कला में स्वाभाविक प्रतिभा",
                "खुशमिजाज स्वभाव, रिश्तों में वफादारी और जीवन का उत्सव मनाना",
                "वस्त्र, आभूषण, साज-सज्जा और संगीत में उत्कृष्ट सुरुचि",
                "मधुर व्यवहार से बड़े से बड़े विवाद को सरलता से सुलझा लेना",
            ],
        },
        "cautions_and_pitfalls": {
            "en": [
                "Indolence, laziness, and procrastination delaying vital responsibilities",
                "Overspending on luxuries, parties, and status symbols",
                "Vulnerability to vanity and seeking endless validation from others",
                "Lower back stiffness, heart circulation sluggishness, or metabolic weight gain",
            ],
            "bn": [
                "অলসতা, আরামপ্রিয়তা ও গুরুত্বপূর্ণ দায়িত্ব ফেলে রেখে সময় নষ্ট করা",
                "দেখনদারি, পার্টি ও বিলাসিতার পেছনে মাত্রাতিরিক্ত অর্থব্যয়",
                "নিজের রূপ বা গুণের প্রশংসার প্রতি অতিরিক্ত মোহ",
                "কোমরের নিচের অংশে ব্যথা, রক্তসঞ্চালনে সমস্যা ও মেদবৃদ্ধি",
            ],
            "hi": [
                "आलस्य, काम को टालने की आदत और आराम में समय गंवाना",
                "दिखावे और फिजूलखर्ची में अपनी बचत उड़ा देना",
                "प्रशंसा पाने की अत्यधिक भूख और आत्ममुग्धता",
                "कमर दर्द, रक्तचाप में असंतुलन और वजन बढ़ना",
            ],
        },
        "beneficial_actions_and_remedies": {
            "en": [
                "Plant and tend a Palash tree with orange-red blossoms",
                "Worship Goddess Lakshmi on Fridays with fragrant white flowers",
                "Donate cosmetics, silk garments, or sweets to young women on Fridays",
                "Maintain strict physical exercise discipline to counter sedentary inertia",
            ],
            "bn": [
                "পলাশ গাছ লাগানো এবং প্রকৃতির সৌন্দর্য রক্ষা করা",
                "শুক্রবার দেবী লক্ষ্মীর চরণে সুগন্ধি ফুল ও পায়েস নিবেদন",
                "শুক্রবার কুমারী বা সধবা নারীকে প্রসাধন সামগ্রী বা মিষ্টান্ন দান",
                "শারীরিক অলসতা দূর করতে প্রতিদিন ব্যায়াম বা প্রাতঃভ্রমণ অভ্যাস",
            ],
            "hi": [
                "पलाश का वृक्ष लगाएं और उसकी देखभाल करें",
                "शुक्रवार को देवी लक्ष्मी को सुवासित पुष्प व खीर अर्पित करें",
                "शुक्रवार को कन्याओं को फल, मिठाई अथवा सौंदर्य सामग्री भेंट करें",
                "आलस्य से बचने के लिए नियमित योग अथवा व्यायाम करें",
            ],
        },
        "career_fields": {
            "en": ["Performing Arts, Music & Cinema", "Wedding Planning & Event Production", "Fashion Design & Haute Couture", "Cosmetic Dermatology & Wellness Spas", "Diplomacy & Public Relations"],
            "bn": ["অভিনয়, নাটক, সঙ্গীত ও চলচ্চিত্র", "বিবাহ ও উৎসব আয়োজন (ওয়েডিং প্ল্যানার)", "ফ্যাশন ডিজাইন ও রূপসজ্জা", "ওয়েলনেস স্পা ও প্রসাধন বাণিজ্য", "জনসংযোগ (PR) ও কূটনীতি"],
            "hi": ["सिनेमा, संगीत, नृत्य व रंगमंच", "इवेंट मैनेजमेंट व वेडिंग प्लानिंग", "फैशन डिजाइनिंग व आभूषण कला", "वेलनेस स्पा व सौंदर्य प्रसाधन", "जनसंपर्क (PR) व आतिथ्य सत्कार"],
        },
    },
    {
        "index": 11,
        "name_en": "Uttara Phalguni",
        "name_bn": "উত্তরাফাল্গুনী",
        "name_hi": "उत्तराफाल्गुनी",
        "lord": "Sun",
        "deity_en": "Aryaman (God of Noble Friendship, Alliances & Patronage)",
        "deity_bn": "অর্যমা (পবিত্র মৈত্রী, পৃষ্ঠপোষকতা ও সামাজিক চুক্তির দেবতা)",
        "deity_hi": "अर्यमा देव (मित्रता व कुल रक्षक)",
        "symbol_en": "Back Legs of Bed",
        "symbol_bn": "পালঙ্কের পশ্চাদ্ভাগ",
        "symbol_hi": "पलंग के पीछे के पाए",
        "gana_en": "Manushya",
        "gana_bn": "মনুষ্য",
        "gana_hi": "मनुष्य",
        "yoni_en": "Cow / Bull (Male)",
        "yoni_bn": "গো / বৃষ (পুং)",
        "yoni_hi": "गाय / बैल (पुरुष)",
        "nadi_en": "Aadi (Vata)",
        "nadi_bn": "আদি (বাত)",
        "nadi_hi": "आदि (वात)",
        "sacred_tree_en": "Pakur / Java Fig (Ficus infectoria)",
        "sacred_tree_bn": "পাকুড় গাছ",
        "sacred_tree_hi": "पाकड़",
        "beej_mantra": "ॐ সূর্যায় নমঃ / ॐ অর্যমণে নমঃ",
        "lucky_color_en": "Bright Saffron & Sunrise Gold",
        "lucky_color_bn": "উজ্জ্বল গেরুয়া ও প্রভাতী সোনালী",
        "lucky_color_hi": "उज्ज्वल केसरिया और स्वर्णिम",
        "lucky_numbers": [1, 7],
        "lucky_gemstone_en": "Ruby (Manikya)",
        "lucky_gemstone_bn": "চুনি (রুবি)",
        "lucky_gemstone_hi": "माणिक्य (रूबी)",
        "padas": [
            {"pada": 1, "rashi_idx": 4, "navamsha": "Sagittarius", "namakshar_en": "Te", "namakshar_bn": "টে", "namakshar_hi": "टे"},
            {"pada": 2, "rashi_idx": 5, "navamsha": "Capricorn", "namakshar_en": "To", "namakshar_bn": "টো", "namakshar_hi": "टो"},
            {"pada": 3, "rashi_idx": 5, "navamsha": "Aquarius", "namakshar_en": "Pa", "namakshar_bn": "পা", "namakshar_hi": "पा"},
            {"pada": 4, "rashi_idx": 5, "navamsha": "Pisces", "namakshar_en": "Pee", "namakshar_bn": "পী", "namakshar_hi": "पी"},
        ],
        "overview": {
            "en": "Uttara Phalguni is the constellation of noble patronage, enduring friendship, and social contracts. Governed by the Sun, natives are dependable, chivalrous, generous, and committed to uplifting society.",
            "bn": "উত্তরাফাল্গুনী পবিত্র বন্ধুত্ব, সামাজিক দায়বদ্ধতা এবং আশ্রিতজনের পাশে দাঁড়ানোর প্রতীক। সূর্যের জ্যোতিতে আলোকিত এই নক্ষত্রের মানুষ বিশ্বস্ত বন্ধু, পরোপকারী, নীতিবান এবং যে কোনো প্রতিশ্রুতি রক্ষায় অবিচল থাকেন।",
            "hi": "उत्तराफाल्गुनी नक्षत्र सच्ची मित्रता, सामाजिक सहयोग और वचनबद्धता का परिचायक है। सूर्य के प्रभाव से जातक कर्तव्यनिष्ठ, उदार, दूसरों की सहायता करने वाले और समाज में आदरणीय होते हैं।",
        },
        "strengths": {
            "en": [
                "Unshakeable integrity and steadfast loyalty to contracts and friendships",
                "Chivalrous patronage and support for vulnerable people in society",
                "Warm, hospitable nature creating enduring social goodwill",
                "Capacity to manage complex organizational partnerships harmoniously",
            ],
            "bn": [
                "কথার দাম রাখা, চুক্তি ও মৈত্রীর প্রতি আজীবন বিশ্বস্ততা",
                "অসহায় ও দুর্বল মানুষের পাশে দাঁড়িয়ে ভরসা জোগানোর সাহস",
                "অতিথি পরায়ণতা, সজ্জন স্বভাব এবং সমাজে গভীর ভালোবাসা অর্জন",
                "জটিল সামাজিক ও ব্যবসায়িক অংশীদারিত্ব সফলভাবে এগিয়ে নিয়ে যাওয়ার দক্ষতা",
            ],
            "hi": [
                "वचन के पक्के, समझौतों व मित्रता के प्रति आजीवन समर्पित",
                "दुर्बलों व जरूरतमंदों को संरक्षण व सहयोग प्रदान करने का गुण",
                "अतिथि सत्कार, शालीनता और समाज में हर वर्ग का प्रिय होना",
                "व्यावसायिक साझेदारी और सामूहिक कार्यों को कुशलता से संभालना",
            ],
        },
        "cautions_and_pitfalls": {
            "en": [
                "Over-dependence on marital validation or social consensus",
                "Stubborn stubbornness when dignity or self-respect feels contested",
                "Resentment if generous patronage is not reciprocated with loyalty",
                "Intestinal sensitivities, spinal alignment issues, and acidity",
            ],
            "bn": [
                "অন্যের প্রশংসা বা সামাজিক অনুমোদনের ওপর অতিরিক্ত নির্ভরতা",
                "আত্মসম্মানে আঘাত লাগলে একগুঁয়ে হয়ে মুখ ফিরিয়ে নেওয়া",
                "উপকার করে বিনিময়ে আনুগত্য বা কৃতজ্ঞতা না পেলে মনে ক্ষোভ পুষে রাখা",
                "অন্ত্রের সমস্যা, গ্যাসট্রিক ও পিঠের ব্যথায় ভোগা",
            ],
            "hi": [
                "दूसरों की सहमति और सामाजिक मान्यता पर अत्यधिक निर्भर रहना",
                "स्वाभिमान को ठेस पहुंचने पर अत्यंत हठी हो जाना",
                "उपकार करने के बाद कृतज्ञता न मिलने पर मन में टीस रखना",
                "पाचन विकार, आंतों में संवेदनशीलता और पीठ में दर्द",
            ],
        },
        "beneficial_actions_and_remedies": {
            "en": [
                "Offer Arghya to the Sun God in a copper vessel every morning",
                "Plant and tend a Pakur tree; preserve nature",
                "Recite Aditya Hridaya Stotra on Sundays",
                "Help friends in need and sponsor education for underprivileged children",
            ],
            "bn": [
                "প্রতিদিন ভোরে তামার পাত্রে জল ও জবাফুল দিয়ে সূর্যদেবকে অর্ঘ্য নিবেদন",
                "পাকুড় গাছের চারা রোপণ ও পরিচর্যা করা",
                "রবিবারে আদিত্য হৃদয় স্তোত্র পাঠ আত্মবিশ্বাস বৃদ্ধি করে",
                "বিপদে বন্ধুদের পাশে দাঁড়ানো এবং দরিদ্র শিশুদের পড়াশোনার খরচ বহন করা",
            ],
            "hi": [
                "प्रतिदिन प्रातः तांबे के लोटे से सूर्य भगवान को अर्घ्य दें",
                "पाकड़ का वृक्ष लगाएं अथवा उसकी सेवा करें",
                "रविवार को आदित्य हृदय स्तोत्र का पाठ करें",
                "सच्चे मन से मित्रों की सहायता करें और निर्धन बालकों की शिक्षा में मदद करें",
            ],
        },
        "career_fields": {
            "en": ["Philanthropic Foundations & Charities", "International Diplomacy & Trade Treaties", "Human Resources & Talent Management", "Senior Civil Administration", "Hospitality & Social Services"],
            "bn": ["জনকল্যাণ ট্রাস্ট ও দাতব্য প্রতিষ্ঠান", "আন্তর্জাতিক কূটনীতি ও বাণিজ্য চুক্তি", "মানবসম্পদ উন্নয়ন (HR) ও পরামর্শ", "উচ্চপদস্থ সরকারি প্রশাসন", "হসপিটালিটি ও সামাজিক উন্নয়ন"],
            "hi": ["धर्मार्थ संस्थाएं व एनजीओ", "अंतरराष्ट्रीय कूटनीति व व्यापारिक संधियां", "मानव संसाधन (HR) प्रबंधन", "उच्च सिविल सेवाएं", "सामाजिक कार्य व आतिथ्य सत्कार"],
        },
    },
    {
        "index": 12,
        "name_en": "Hasta",
        "name_bn": "হস্তা",
        "name_hi": "हस्त",
        "lord": "Moon",
        "deity_en": "Savitar (The Creative Sun / Awaken of Light)",
        "deity_bn": "সবিতা (সৃষ্টিকর্তা সূর্যদেব ও দিব্য প্রকাশ)",
        "deity_hi": "सविता देव (सूर्य का प्रेरक रूप)",
        "symbol_en": "Open Hand / Clenched Fist",
        "symbol_bn": "উন্মুক্ত হস্ত / মুষ্টিবদ্ধ হাত",
        "symbol_hi": "खुली हथेली / मुट्ठी",
        "gana_en": "Deva",
        "gana_bn": "দেব",
        "gana_hi": "देव",
        "yoni_en": "Buffalo (Female)",
        "yoni_bn": "মহিষ (স্ত্রী)",
        "yoni_hi": "महिष / भैंस (स्त्री)",
        "nadi_en": "Aadi (Vata)",
        "nadi_bn": "আদি (বাত)",
        "nadi_hi": "আদি (वात)",
        "sacred_tree_en": "Chameli / Jasmine (Jasminum grandiflorum)",
        "sacred_tree_bn": "জুঁই / চামেলী",
        "sacred_tree_hi": "चमेली",
        "beej_mantra": "ॐ চন্দ্রায় নমঃ / ॐ সবিত্রে নমঃ",
        "lucky_color_en": "Pearl White & Leaf Green",
        "lucky_color_bn": "মুক্তাভ শুভ্র ও কচি কলাপাতা সবুজ",
        "lucky_color_hi": "मोती श्वेत और हल्का हरा",
        "lucky_numbers": [2, 5],
        "lucky_gemstone_en": "Pearl (Moti) or Emerald",
        "lucky_gemstone_bn": "মুক্তো অথবা পান্না",
        "lucky_gemstone_hi": "मोती अथवा पन्ना",
        "padas": [
            {"pada": 1, "rashi_idx": 5, "navamsha": "Aries", "namakshar_en": "Pu", "namakshar_bn": "পু", "namakshar_hi": "पु"},
            {"pada": 2, "rashi_idx": 5, "navamsha": "Taurus", "namakshar_en": "Sha", "namakshar_bn": "ষ", "namakshar_hi": "ष"},
            {"pada": 3, "rashi_idx": 5, "navamsha": "Gemini", "namakshar_en": "Na", "namakshar_bn": "ণ", "namakshar_hi": "ण"},
            {"pada": 4, "rashi_idx": 5, "navamsha": "Cancer", "namakshar_en": "Tha", "namakshar_bn": "ঠ", "namakshar_hi": "ठ"},
        ],
        "overview": {
            "en": "Hasta represents dexterity, craftsmanship, and the power to manifest through one's hands. Ruled by the Moon in Mercury's sign Virgo, natives are witty, versatile, clever with tools, and gifted in healing arts.",
            "bn": "হস্তা হাতের নিপুণ কারুকাজ, জাদুস্পর্শ এবং মনের ভাবকে বাস্তবে রূপ দেওয়ার প্রতীক। চন্দ্র ও বুধের যৌথ প্রভাবে এই জাতকরা অসাধারণ হস্তশিল্পী, চতুর হিসাববিদ, রসবোধসম্পন্ন এবং চিকিৎসা ও সেবায় পারদর্শী হন।",
            "hi": "हस्त नक्षत्र हाथों के कौशल, चातुर्य और रचनाशीलता का प्रतीक है। चंद्रमा व बुध के सुंदर समन्वय से जातक कुशल शिल्पकार, हाजिरजवाब, बुद्धिमान और हर कार्य को सलीके से करने वाले होते हैं।",
        },
        "strengths": {
            "en": [
                "Extraordinary manual dexterity, surgical precision, and artisan genius",
                "Sparkling wit, humor, and brilliant persuasive conversational skill",
                "Deep healing touch in massage, acupressure, nursing, and medicine",
                "Keen business calculation and resource optimization abilities",
            ],
            "bn": [
                "হাতের কাজে অবিশ্বাস্য নৈপুণ্য—অস্ত্রোপচার, চিত্রাঙ্কন বা হস্তশিল্পে সূক্ষ্ম দক্ষতা",
                "চমৎকার রসবোধ, উপস্থিত বুদ্ধি ও মিষ্টি কথায় সবাইকে আপন করার শক্তি",
                "নিরাময়কারী স্পর্শ—চিকিৎসা, সেবা ও নার্সিংয়ে পরম নিষ্ঠা",
                "হিসাব-নিকাশ, বাণিজ্য এবং কম খরচে নিখুঁত কাজ নামিয়ে আনার মেধা",
            ],
            "hi": [
                "हाथ के कार्यों में अद्भुत निपुणता—शल्य चिकित्सा, चित्रकला या शिल्प में पारंगत",
                "हाजिरजवाबी, चुटीला हास्य और बात मनवाने की जबर्दस्त कला",
                "उपचार की स्वाभाविक शक्ति—सेवाभाव व चिकित्सा में सफलता",
                "व्यापारिक गणना, बजट प्रबंधन और संसाधनों का उत्तम सदुपयोग",
            ],
        },
        "cautions_and_pitfalls": {
            "en": [
                "Restless overthinking leading to chronic anxiety and nervous ticks",
                "Tendency towards cunning manipulation, deception, or gambling tricks",
                "Mood swings and critical nitpicking of others' minor errors",
                "Digestive bowel distress, colic, and hand/wrist tendon inflammation",
            ],
            "bn": [
                "অতিরিক্ত খুঁতখুঁতে স্বভাব ও অহেতুক চিন্তায় মানসিক দুশ্চিন্তায় ভোগা",
                "কূটকৌশল প্রয়োগ, চালাকি বা অতিচালাক হতে গিয়ে ফাঁদে পড়া",
                "মেজাজের খামখেয়ালিপনা এবং অন্যের ছোটখাটো ত্রুটি নিয়ে অতিরিক্ত খোঁটা দেওয়া",
                "আইবিএস (IBS), পেটের গোলযোগ ও হাতের কব্জিতে ব্যথার প্রবণতা",
            ],
            "hi": [
                "अति-विचारशीलता के कारण व्यर्थ की चिंता और घबराहट में रहना",
                "अत्यधिक चालाकी या छल-कपट की ओर प्रवृत्त होने की भूल",
                "मूड में बार-बार बदलाव और दूसरों की छोटी-छोटी कमियां निकालना",
                "पेट के रोग (आईबीएस), गैस और कलाई या हाथों में दर्द",
            ],
        },
        "beneficial_actions_and_remedies": {
            "en": [
                "Practice Gayatri Mantra daily at sunrise to invoke Savitar's blessings",
                "Plant and tend fragrant Chameli (Jasmine) plants",
                "Worship the Sun God and keep pure water vessels clean",
                "Donate writing stationery, books, or green vegetables to students on Wednesdays",
            ],
            "bn": [
                "প্রতিদিন সূর্যোদয়ের পর একমনে গায়ত্রী মন্ত্র জপ সবিতৃ দেবের কৃপা আনে",
                "জুঁই বা চামেলী ফুলের গাছ লাগানো এবং পরিচর্যা করা",
                "সূর্যদেবের উপাসনা এবং প্রতিদিন গঙ্গাজল স্পর্শ করে দিন শুরু",
                "বুধবার দরিদ্র ছাত্রছাত্রীদের খাতা-কলম বা সবুজ শাকসবজি দান",
            ],
            "hi": [
                "प्रतिदिन सूर्योदय के समय गायत्री मंत्र का 108 बार जप करें",
                "चमेली का पौधा लगाएं और उसके सुवासित पुष्पों का आनंद लें",
                "भगवान सूर्य की उपासना करें",
                "बुधवार को जरूरतमंद विद्यार्थियों को पुस्तकें, कलम या हरी सब्जियां दान करें",
            ],
        },
        "career_fields": {
            "en": ["Precision Surgery & Dentistry", "Fine Jewelry Crafting & Watchmaking", "Graphic Design, Animation & Illustration", "Accounting, Auditing & Financial Analytics", "Massage Therapy, Reiki & Alternative Healing"],
            "bn": ["নিখুঁত শল্যচিকিৎসা ও দন্তচিকিৎসা", "রত্ন-অলঙ্কার কারিগর ও ঘড়ি প্রস্তুতকারক", "গ্রাফিক ডিজাইন, অ্যানিমেশন ও চিত্রাঙ্কন", "অ্যাকাউন্টিং, অডিট ও আর্থিক বিশ্লেষণ", "ফিজিওথেরাপি, রেইকি ও বিকল্প চিকিৎসা"],
            "hi": ["शल्य चिकित्सा (सर्जरी) व दंत चिकित्सा", "रत्न व आभूषण निर्माण, सूक्ष्म कारीगरी", "ग्राफिक डिजाइन, एनिमेशन व कला", "चार्टर्ड अकाउंटेंसी, ऑडिट व वित्तीय विश्लेषण", "फिजियोथेरेपी व प्राकृतिक चिकित्सा"],
        },
    },
    {
        "index": 13,
        "name_en": "Chitra",
        "name_bn": "চিত্রা",
        "name_hi": "चित्रा",
        "lord": "Mars",
        "deity_en": "Tvashtar / Vishwakarma (The Divine Celestial Architect)",
        "deity_bn": "ত্বষ্টা / বিশ্বকর্মা (দেবতাদের প্রধান স্থপতি ও ভাস্কর)",
        "deity_hi": "त्वष्टा / भगवान विश्वकर्मा",
        "symbol_en": "Bright Jewel / Pearl",
        "symbol_bn": "উজ্জ্বল রত্ন / দীপ্তিমান মুক্তো",
        "symbol_hi": "चमकता रत्न / मोती",
        "gana_en": "Rakshasa",
        "gana_bn": "রাক্ষস",
        "gana_hi": "রাক্ষস",
        "yoni_en": "Tiger (Female)",
        "yoni_bn": "ব্যাঘ্র / বাঘ (স্ত্রী)",
        "yoni_hi": "व्याघ्र / बाघिन (स्त्री)",
        "nadi_en": "Madhya (Pitta)",
        "nadi_bn": "মধ্য (পিত্ত)",
        "nadi_hi": "मध्य (पित्त)",
        "sacred_tree_en": "Bilva / Bael (Aegle marmelos)",
        "sacred_tree_bn": "বেলগাছ",
        "sacred_tree_hi": "बेलपत्र (बिल्व)",
        "beej_mantra": "ॐ বিশ্বকর্মণে নমঃ / ॐ ভৌমায় নমঃ",
        "lucky_color_en": "Bright Scarlet & Shining Opal",
        "lucky_color_bn": "উজ্জ্বল রক্তিম ও ঝিলমিলে ওপাল",
        "lucky_color_hi": "चटक लाल और चमकीला ओपल",
        "lucky_numbers": [9, 6],
        "lucky_gemstone_en": "Red Coral (Moonga) or Diamond",
        "lucky_gemstone_bn": "রক্তপ্রবাল অথবা হীরে",
        "lucky_gemstone_hi": "मूंगा अथवा हीरा",
        "padas": [
            {"pada": 1, "rashi_idx": 5, "navamsha": "Leo", "namakshar_en": "Pe", "namakshar_bn": "পে", "namakshar_hi": "पे"},
            {"pada": 2, "rashi_idx": 5, "navamsha": "Virgo", "namakshar_en": "Po", "namakshar_bn": "পো", "namakshar_hi": "पो"},
            {"pada": 3, "rashi_idx": 6, "navamsha": "Libra", "namakshar_en": "Ra", "namakshar_bn": "রা", "namakshar_hi": "रा"},
            {"pada": 4, "rashi_idx": 6, "navamsha": "Scorpio", "namakshar_en": "Ree", "namakshar_bn": "রী", "namakshar_hi": "री"},
        ],
        "overview": {
            "en": "Chitra, the solitary gem of the sky, represents multidimensional creativity, architectural brilliance, and aesthetic perfection. Governed by Mars and presided by Vishwakarma, natives are visionary builders.",
            "bn": "চিত্রা আকাশের বুকে এক উজ্জ্বল রত্নের মতো জ্বলজ্বলে। এটি দেবশিল্পী বিশ্বকর্মার সৃজনশীল স্থাপত্য এবং অনবদ্য রূপকল্পের প্রতীক। মঙ্গলের শক্তিতে বলীয়ান এঁরা দক্ষ ডিজাইনার, দূরদর্শী নির্মাতা এবং সৌন্দর্যের নিখুঁত রূপকার।",
            "hi": "चित्रा नक्षत्र आकाश में चमकते हुए सुंदर रत्न के समान है। देवशिल्पी विश्वकर्मा के प्रभाव से जातक अद्भुत वास्तुकला, डिजाइनिंग और हर वस्तु को सुंदर व परिपूर्ण बनाने की कला में दक्ष होते हैं।",
        },
        "strengths": {
            "en": [
                "Exceptional eye for design, spatial aesthetics, and architectural innovation",
                "Magnetic personal beauty, elegant sense of style, and sparkling charisma",
                "Technical brilliance with materials, machinery, sculpture, and visuals",
                "Courage to craft original paths rather than copying outdated models",
            ],
            "bn": [
                "স্থাপত্যকলা, আধুনিক ডিজাইন ও দৃশ্যমান সৌন্দর্যের অতুলনীয় চোখ",
                "আকর্ষণীয় রূপলাবণ্য, পরিপাটি বেশভূষা এবং ব্যক্তিত্বের প্রখর দীপ্তি",
                "যন্ত্রপাতি, ধাতু, ভাস্কর্য ও প্রযুক্তি নিয়ে কাজ করার সহজাত পারদর্শিতা",
                "অন্যের অনুকরণ না করে সম্পূর্ণ নতুন ও মৌলিক কিছু সৃষ্টি করার দুঃসাহস",
            ],
            "hi": [
                "वास्तुकला, इंटीरियर डिजाइन और सौंदर्यबोध की अद्वितीय दृष्टि",
                "सम्मोहक रूप-रंग, सुरुचिपूर्ण वेशभूषा और प्रभावशाली व्यक्तित्व",
                "यंत्रों, धातुओं, मूर्तिकला और दृश्य कलाओं में विशेष दक्षता",
                "नकल करने के बजाय अपनी मौलिक शैली विकसित करने का साहस",
            ],
        },
        "cautions_and_pitfalls": {
            "en": [
                "Superficial obsession with exterior appearances over interior substance",
                "Fiery arguments and egotistical clashes with equals and spouses",
                "Impulsive spending to acquire expensive ornaments and luxury facades",
                "Kidney inflammation, urinary irritation, and forehead headaches",
            ],
            "bn": [
                "ভেতরের গুণাগুণের চেয়ে বাইরের চাকচিক্য ও রূপের পেছনে অন্ধের মতো ছোটা",
                "অহংকারের সংঘাত এবং জীবনসঙ্গী বা সহকর্মীদের সঙ্গে রূঢ় ঝগড়ায় জড়ানো",
                "দামী অলঙ্কার ও বিলাসিতা প্রদর্শনের জন্য আয়-ব্যয়ের ভারসাম্য হারানো",
                "কিডনি ও মূত্রনালীর প্রদাহ, মাথাব্যথা ও রক্তে অম্লতা",
            ],
            "hi": [
                "आंतरिक गुणों की उपेक्षा कर बाहरी दिखावे व चमक-दमक में उलझ जाना",
                "अहंकार के टकराव में आकर जीवनसाथी या सहयोगियों से विवाद करना",
                "दिखावे के लिए महंगे आभूषणों और विलासिता पर फिजूलखर्ची",
                "गुर्दे व मूत्र मार्ग के विकार तथा सिरदर्द की समस्या",
            ],
        },
        "beneficial_actions_and_remedies": {
            "en": [
                "Plant and tend a sacred Bilva (Bael) tree; offer its leaves to Shiva",
                "Worship Lord Vishwakarma and Lord Kartikeya on Tuesdays",
                "Recite Durga Chalisa or Hanuman Chalisa for emotional balance",
                "Donate red lentils, copper items, or design tools to craftsmen on Tuesdays",
            ],
            "bn": [
                "একটি বেলগাছ রোপণ করা এবং শিবলিঙ্গে ত্রিনয়ন বিল্বপত্র নিবেদন",
                "মঙ্গলবার দেবশিল্পী বিশ্বকর্মা এবং কার্তিকেয়র আরাধনা",
                "নিয়মিত হনুমান চালীসা পাঠ মনের উগ্রতা ও অহংকার দূর করে",
                "মঙ্গলবার কারিগর বা মেকানিকদের প্রয়োজনীয় যন্ত্রপাতি বা মিষ্টি দান",
            ],
            "hi": [
                "बिल्व (बेल) का वृक्ष लगाएं और शिवजी पर त्रिदल बेलपत्र चढ़ाएं",
                "मंगलवार को भगवान विश्वकर्मा और हनुमानजी की पूजा करें",
                "दुर्गा चालीसा अथवा हनुमान चालीसा का नियमित पाठ करें",
                "मंगलवार को शिल्पकारों या मिस्त्रियों को औजार अथवा भोजन भेंट करें",
            ],
        },
        "career_fields": {
            "en": ["Architectural Engineering & Urban Planning", "Interior Decor & Visual Merchandising", "Fashion Design & Haute Jewelry", "Sculpture, Painting & Cinematic VFX", "Mechanical & Automotive Engineering"],
            "bn": ["স্থাপত্য প্রকৌশল ও নগর পরিকল্পনা", "ইন্টেরিয়র ডিজাইন ও ভিজ্যুয়াল আর্ট", "ফ্যাশন ডিজাইন ও রত্নালঙ্কার শিল্প", "ভাস্কর্য, চিত্রকলা ও সিনেমা ভিএফএক্স (VFX)", "মেকানিক্যাল ও অটোমোবাইল ইঞ্জিনিয়ারিং"],
            "hi": ["वास्तुकला (आर्किटेक्चर) व नगर नियोजन", "इंटीरियर डिजाइनिंग व गृह सज्जा", "फैशन डिजाइनिंग व ज्वैलरी निर्माण", "मूर्तिकला, चित्रकला व वीएफएक्स (VFX)", "मैकेनिकल व ऑटोमोबाइल इंजीनियरिंग"],
        },
    },
    {
        "index": 14,
        "name_en": "Swati",
        "name_bn": "স্বাতী",
        "name_hi": "स्वाति",
        "lord": "Rahu",
        "deity_en": "Vayu (The God of Cosmic Wind & Breath of Life)",
        "deity_bn": "বায়ুদেব (প্রাণবায়ু ও অসীম বাতাসের অধিপতি)",
        "deity_hi": "वायु देव (प्राण वायु के देवता)",
        "symbol_en": "Young Sprout swaying in wind / Coral / Sword",
        "symbol_bn": "বায়ুহিল্লোলিত কচি অঙ্কুর / প্রবাল / তরবারি",
        "symbol_hi": "हवा में लहराता अंकुर / मूंगा / तलवार",
        "gana_en": "Deva",
        "gana_bn": "দেব",
        "gana_hi": "देव",
        "yoni_en": "Buffalo (Male)",
        "yoni_bn": "মহিষ (পুং)",
        "yoni_hi": "महिष / भैंसा (पुरुष)",
        "nadi_en": "Antya (Kapha)",
        "nadi_bn": "অন্ত্য (কফ)",
        "nadi_hi": "अंत्य (कफ)",
        "sacred_tree_en": "Arjuna (Terminalia arjuna)",
        "sacred_tree_bn": "অর্জুন গাছ",
        "sacred_tree_hi": "अर्जुन",
        "beej_mantra": "ॐ বায়বে নমঃ / ॐ রাহবে নমঃ",
        "lucky_color_en": "Sky Blue & Silver White",
        "lucky_color_bn": "আকাশি নীল ও রুপোলি সাদা",
        "lucky_color_hi": "आसमानी नीला और रुपहला",
        "lucky_numbers": [4, 6],
        "lucky_gemstone_en": "Hessonite Garnet (Gomed) or Blue Sapphire",
        "lucky_gemstone_bn": "গোমেদ অথবা নীলা",
        "lucky_gemstone_hi": "गोमेद अथवा नीलम",
        "padas": [
            {"pada": 1, "rashi_idx": 6, "navamsha": "Sagittarius", "namakshar_en": "Roo", "namakshar_bn": "রূ", "namakshar_hi": "रू"},
            {"pada": 2, "rashi_idx": 6, "navamsha": "Capricorn", "namakshar_en": "Re", "namakshar_bn": "রে", "namakshar_hi": "रे"},
            {"pada": 3, "rashi_idx": 6, "navamsha": "Aquarius", "namakshar_en": "Ro", "namakshar_bn": "রো", "namakshar_hi": "रो"},
            {"pada": 4, "rashi_idx": 6, "navamsha": "Pisces", "namakshar_en": "Ta", "namakshar_bn": "তা", "namakshar_hi": "ता"},
        ],
        "overview": {
            "en": "Swati signifies independence, adaptability, and the gentle yet mighty force of wind. Governed by Rahu in the balance sign Libra, natives are diplomatic, freedom-loving, highly cultured traders.",
            "bn": "স্বাতী মুক্ত বাতাস, স্বাধীনতা এবং যে কোনো প্রতিকূলতায় নমনীয় হয়ে টিকে থাকার প্রতীক। তুলা রাশিতে রাহুর প্রভাব এঁদের অত্যন্ত দক্ষ মধ্যস্থতাকারী, স্বাধীনচেতা ব্যবসায়ী, মার্জিত ও মিষ্টভাষী করে তোলে।",
            "hi": "स्वाति नक्षत्र स्वतंत्रता, अनुकूलनशीलता और वायु तत्व की गतिशीलता का प्रतीक है। तुला राशि में राहु के प्रभाव से जातक अत्यंत कूटनीतिज्ञ, व्यापार कुशल, स्वावलंबी और सुरुचिपूर्ण होते हैं।",
        },
        "strengths": {
            "en": [
                "Exceptional business negotiation and commercial diplomacy skills",
                "Graceful adaptability; bends with fierce winds without ever breaking",
                "Love for liberty, fair-minded justice, and human rights advocacy",
                "Polite, refined social charm that makes them welcome everywhere",
            ],
            "bn": [
                "বাণিজ্যিক বোঝাপড়া, কূটনৈতিক আলোচনা ও ব্যবসায়ে অসাধারণ দক্ষতা",
                "অনমনীয় না হয়ে পরিস্থিতির সঙ্গে মানিয়ে নেওয়ার অদ্ভুত নমনীয় শক্তি",
                "স্বাধীনতা প্রিয়তা, সাম্যবাদ ও মানবাধিকারের প্রতি গভীর অঙ্গীকার",
                "ভদ্র, মার্জিত ও মধুর সামাজিক চালচলন যা সবাইকে মুগ্ধ করে",
            ],
            "hi": [
                "व्यापारिक समझौते और कूटनीतिक बातचीत में अद्वितीय कुशलता",
                "परिस्थितियों के अनुसार स्वयं को ढाल लेने का अद्भुत लचीलापन",
                "स्वतंत्र विचारों के धनी, न्यायप्रिय और मानवीय मूल्यों के पक्षधर",
                "सभ्य, शालीन और आकर्षक व्यवहार जिससे सर्वत्र सम्मान मिलता है",
            ],
        },
        "cautions_and_pitfalls": {
            "en": [
                "Indecisiveness, scattering energy across too many winds of thought",
                "Procrastination in committing deeply to relationships or locations",
                "Vulnerability to spending windfalls on luxury whims",
                "Kidney strain, gas/bloating, and joint stiffness due to dry wind",
            ],
            "bn": [
                "মন স্থির করতে না পারা এবং একসাথে অনেক দিকে শক্তি অপচয় করা",
                "কোনো সম্পর্কে বা একটি নির্দিষ্ট লক্ষ্যে দীর্ঘস্থায়ী দায়বদ্ধ হতে ভয় পাওয়া",
                "হাতে টাকা এলে হুজুগে পড়ে অপ্রয়োজনীয় শৌখিনতায় উড়িয়ে দেওয়া",
                "কিডনির দুর্বলতা, পেট ফাঁপা, গ্যাস ও বাতজনিত অস্থিসন্ধির ব্যথা",
            ],
            "hi": [
                "अनिर्णय की स्थिति और एक साथ कई दिशाओं में भटक जाना",
                "संबंधों या किसी एक लक्ष्य पर लंबे समय तक टिकने में हिचकना",
                "पैसा आने पर अचानक शौक-मौज में धन उड़ाने की प्रवृत्ति",
                "वात रोग, पेट में वायु विकार और जोड़ों में दर्द",
            ],
        },
        "beneficial_actions_and_remedies": {
            "en": [
                "Practice Pranayama (slow alternate nostril breathing) daily",
                "Plant and tend an Arjuna tree; utilize its heart-protective qualities",
                "Worship Lord Hanuman (the son of Vayu) on Tuesdays and Saturdays",
                "Donate blankets, umbrellas, or footwear to travelers and needy souls",
            ],
            "bn": [
                "বায়ু তত্ত্বকে শান্ত করতে প্রতিদিন অনুলোম-বিলোম প্রাণায়াম অভ্যাস",
                "অর্জুন গাছ লাগানো ও তার যত্ন নেওয়া অত্যন্ত কল্যাণকর",
                "পবনপুত্র শ্রী হনুমানজির আরাধনা ও সুন্দরকাণ্ড পাঠ",
                "শনিবার দুঃস্থ পথিকদের জুতো, ছাতা বা গরম বস্ত্র দান করা",
            ],
            "hi": [
                "प्रतिदिन अनुलोम-विलोम प्राणायाम का 15 मिनट अभ्यास करें",
                "अर्जुन का वृक्ष लगाएं जो हृदय और पर्यावरण दोनों के लिए शुभ है",
                "पवनपुत्र हनुमानजी की उपासना करें और हनुमान चालीसा पढ़ें",
                "शनिवार को असहाय यात्रियों या गरीबों को जूते, छाता अथवा कंबल दान करें",
            ],
        },
        "career_fields": {
            "en": ["International Trade & Import/Export", "Legal Arbitration & Diplomatic Relations", "Aviation, Flight Crew & Meteorological Tech", "Public Speaking, Podcasting & Media Hosting", "Stock Market Trading & Financial Broking"],
            "bn": ["আন্তর্জাতিক বাণিজ্য ও আমদানি-রপ্তানি", "আইনগত সালিশি ও কূটনৈতিক পরিষেবা", "বিমান পরিষেবা ও আবহাওয়া প্রযুক্তি", "পডকাস্টিং, গণবক্তৃতা ও মিডিয়া সঞ্চালনা", "শেয়ার বাজার ট্রেডিং ও ফিনান্সিয়াল ব্রোকিং"],
            "hi": ["अंतरराष्ट्रीय व्यापार, आयात-निर्यात", "कानूनी मध्यस्थता व कूटनीतिक सेवाएं", "विमानन (एविएशन) व मौसम विज्ञान", "पॉडकास्टिंग, जनसंचार व टीवी एंकरिंग", "शेयर बाजार ट्रेडिंग व वित्तीय दलाली"],
        },
    },
    {
        "index": 15,
        "name_en": "Vishakha",
        "name_bn": "বিশাখা",
        "name_hi": "विशाखा",
        "lord": "Jupiter",
        "deity_en": "Indragni (Combined Energy of Indra & Agni)",
        "deity_bn": "ইন্দ্রাগ্নি (দেবরাজ ইন্দ্র ও অগ্নিদেবের যুগল শক্তি)",
        "deity_hi": "इंद्राग्नि (देवराज इंद्र और अग्नि देव)",
        "symbol_en": "Triumphal Arch / Potter's Wheel",
        "symbol_bn": "বিজয় তোরণ / কুম্ভকারের চক্র",
        "symbol_hi": "विजय द्वार / कुम्हार का चाक",
        "gana_en": "Rakshasa",
        "gana_bn": "রাক্ষস",
        "gana_hi": "রাক্ষস",
        "yoni_en": "Tiger (Male)",
        "yoni_bn": "ব্যাঘ্র / বাঘ (পুং)",
        "yoni_hi": "व्याघ्र / बाघ (पुरुष)",
        "nadi_en": "Antya (Kapha)",
        "nadi_bn": "অন্ত্য (কফ)",
        "nadi_hi": "अंत्य (कফ)",
        "sacred_tree_en": "Vikankata / Kaith (Feronia elephantum)",
        "sacred_tree_bn": "কয়েতবেল / বিকঙ্কত",
        "sacred_tree_hi": "कैथ (कबीट)",
        "beej_mantra": "ॐ বৃহস্পতয়ে নমঃ / ॐ ইন্দ্রাগ্নিভ্যাং নমঃ",
        "lucky_color_en": "Bright Golden Orange & Saffron",
        "lucky_color_bn": "উজ্জ্বল সোনালী কমলা ও জাফরান",
        "lucky_color_hi": "स्वर्णिम नारंगी और केसरिया",
        "lucky_numbers": [3, 9],
        "lucky_gemstone_en": "Yellow Sapphire (Pukhraj)",
        "lucky_gemstone_bn": "হলুদ পোখরাজ",
        "lucky_gemstone_hi": "पीला पुखराज",
        "padas": [
            {"pada": 1, "rashi_idx": 6, "navamsha": "Aries", "namakshar_en": "Tee", "namakshar_bn": "তী", "namakshar_hi": "ती"},
            {"pada": 2, "rashi_idx": 6, "navamsha": "Taurus", "namakshar_en": "Too", "namakshar_bn": "তূ", "namakshar_hi": "तू"},
            {"pada": 3, "rashi_idx": 6, "navamsha": "Gemini", "namakshar_en": "Te", "namakshar_bn": "তে", "namakshar_hi": "ते"},
            {"pada": 4, "rashi_idx": 7, "navamsha": "Cancer", "namakshar_en": "To", "namakshar_bn": "তো", "namakshar_hi": "तो"},
        ],
        "overview": {
            "en": "Vishakha is the star of single-minded focus, triumphant breakthrough, and unyielding ambition. Presided over by Indra and Agni, natives possess relentless perseverance until they plant their victory flag.",
            "bn": "বিশাখা একাগ্র লক্ষ্যভেদ, বিজয়তোরণ এবং অদম্য উচ্চাকাঙ্ক্ষার প্রতীক। দেবরাজ ইন্দ্রের শাসনক্ষমতা এবং অগ্নির তেজ নিয়ে জন্ম নেওয়া এই জাতকরা যে কোনো লক্ষ্য পূরণ না হওয়া পর্যন্ত অবিচল সংগ্রামে বিশ্বাসী।",
            "hi": "विशाखा नक्षत्र अटूट संकल्प, लक्ष्य प्राप्ति और विजय का प्रतीक है। इंद्र और अग्नि के संयुक्त प्रभाव से जातक महत्वाकांक्षी, अथक परिश्रमी और अपने लक्ष्य को हासिल करके ही दम लेने वाले होते हैं।",
        },
        "strengths": {
            "en": [
                "Unstoppable perseverance; never abandons a long-term goal once declared",
                "Powerful combination of intellectual strategy and burning willpower",
                "Natural leadership in competitive fields, politics, and high stakes",
                "Capacity for late-blooming monumental triumphs after enduring tests",
            ],
            "bn": [
                "অদম্য অধ্যবসায়—একবার লক্ষ্য স্থির করলে সাফল্য না আসা পর্যন্ত থামেন না",
                "বুদ্ধিদীপ্ত পরিকল্পনা ও জলন্ত ইচ্ছাশক্তির অপূর্ব সংমিশ্রণ",
                "রাজনীতি, বিতর্ক ও প্রতিযোগিতামূলক ক্ষেত্রে স্বাভাবিক কর্তৃত্ব",
                "জীবনের প্রথমার্ধের কঠিন সংগ্রামের পর দ্বিতীয়ার্ধে অভূতপূর্ব বিজয় লাভ",
            ],
            "hi": [
                "अटूट धैर्य और लगन—एक बार संकल्प ले लिया तो पूरा करके ही विश्राम",
                "रणनीतिक सोच और प्रचंड इच्छाशक्ति का दुर्लभ संगम",
                "राजनीति, नेतृत्व और प्रतिस्पर्धात्मक परीक्षाओं में अग्रणी रहना",
                "प्रारंभिक संघर्षों के बाद जीवन के उत्तरार्ध में ऐतिहासिक सफलता",
            ],
        },
        "cautions_and_pitfalls": {
            "en": [
                "Obsessive jealousy of others' triumphs or comparing achievements bitterly",
                "Ruthless ambition trampling personal relationships along the way",
                "Burnout from relentless grinding without pause for gratitude",
                "Urinary tract infections, kidney stones, and reproductive inflammation",
            ],
            "bn": [
                "অন্যের সাফল্য দেখে অন্তরে ঈর্ষা ও নিজেকে প্রতিনিয়ত অন্যের সঙ্গে তুলনা করা",
                "নিজের উচ্চাকাঙ্ক্ষা পূরণের জন্য প্রিয়জন বা বন্ধুদের অনুভূতি পদদলিত করা",
                "বিরামহীন খাটুনি করতে গিয়ে শারীরিক ও মানসিক অবসাদে ভেঙে পড়া",
                "মূত্রথলিতে সংক্রমণ, কিডনিতে পাথর ও প্রজননতন্ত্রের প্রদাহ",
            ],
            "hi": [
                "दूसरों की उन्नति देखकर ईर्ष्या करना और अपनी तुलना करते रहना",
                "सफलता पाने के जुनून में अपनों की भावनाओं की अनदेखी करना",
                "अत्यधिक काम के दबाव से खुद को मानसिक रूप से थका देना",
                "मूत्र विकार, गुर्दे में पथरी और प्रजनन अंगों में समस्या",
            ],
        },
        "beneficial_actions_and_remedies": {
            "en": [
                "Worship Lord Muruga (Kartikeya) or Lord Shiva with red flowers",
                "Plant and tend a Kaith (Feronia) tree",
                "Practice conscious celebration of others' victories to purge envy",
                "Donate yellow sweets, brass vessels, or yellow pulses on Thursdays",
            ],
            "bn": [
                "শ্রী কার্তিকেয় বা দেবাদিদেব মহাদেবের চরণে লাল পদ্ম বা জবা নিবেদন",
                "কয়েতবেল গাছ লাগানো ও তার যত্ন নেওয়া",
                "অন্যের বিজয়ে মন খুলে আনন্দ প্রকাশ করে অন্তরের ঈর্ষা দূর করার অভ্যাস",
                "বৃহস্পতিবারে হলুদ মিষ্টি, পিতলের পাত্র বা ছোলার ডাল দরিদ্রকে দান",
            ],
            "hi": [
                "भगवान कार्तिकेय या शिवजी को लाल पुष्प अर्पित करें",
                "कैथ का वृक्ष लगाएं",
                "दूसरों की सफलता में प्रसन्न होना सीखें ताकि मन की ईर्ष्या मिट सके",
                "गुरुवार को पीले फल, पीतल के बर्तन या चने की दाल का दान करें",
            ],
        },
        "career_fields": {
            "en": ["Competitive Electoral Politics", "Trial Litigation & Criminal Defense", "High-Stakes Corporate Leadership", "Sports Athletics & Martial Arts", "Scientific Invention & Patent Development"],
            "bn": ["নির্বাচনী রাজনীতি ও প্রশাসন", "ফৌজদারি ও সাংবিধানিক আইন পেশা", "শীর্ষ কর্পোরেট এক্সিকিউটিভ নেতৃত্ব", "প্রতিযোগিতামূলক ক্রীড়া ও মার্শাল আর্ট", "বৈজ্ঞানিক আবিষ্কার ও পেটেন্ট গবেষণা"],
            "hi": ["सक्रिय राजनीति व जन सेवा", "आपराधिक कानून व वकालत", "कॉर्पोरेट प्रबंधन व सीईओ पद", "खेलकूद, एथलेटिक्स व मार्शल आर्ट", "वैज्ञानिक शोध व नवाचार"],
        },
    },
    {
        "index": 16,
        "name_en": "Anuradha",
        "name_bn": "অনুরাধা",
        "name_hi": "अनुराधा",
        "lord": "Saturn",
        "deity_en": "Mitra (God of Friendship, Harmony & Divine Light)",
        "deity_bn": "মিত্রদেব (পবিত্র মৈত্রী, সৌহার্দ্য ও দিব্য আলোর দেবতা)",
        "deity_hi": "मित्र देव (मित्रता व सौहार्द के देवता)",
        "symbol_en": "Lotus Flower / Triumphal Gateway",
        "symbol_bn": "পদ্মর ফুল / বিজয় তোরণ",
        "symbol_hi": "कमल का पुष्प / विजयी प्रवेश द्वार",
        "gana_en": "Deva",
        "gana_bn": "দেব",
        "gana_hi": "দেব",
        "yoni_en": "Deer (Female)",
        "yoni_bn": "হরিণ (স্ত্রী)",
        "yoni_hi": "मृग / हिरणी (स्त्री)",
        "nadi_en": "Madhya (Pitta)",
        "nadi_bn": "মধ্য (পিত্ত)",
        "nadi_hi": "मध्य (पित्त)",
        "sacred_tree_en": "Bakul / Spanish Cherry (Mimusops elengi)",
        "sacred_tree_bn": "বকুল গাছ",
        "sacred_tree_hi": "मौलश्री (बकुल)",
        "beej_mantra": "ॐ শনৈশ্চরায় নমঃ / ॐ মিত্রায় নমঃ",
        "lucky_color_en": "Deep Navy Blue & Lotus Crimson",
        "lucky_color_bn": "গাঢ় নীল ও পদ্মরাগ লাল",
        "lucky_color_hi": "गहरा नीला और गुलाबी लाल",
        "lucky_numbers": [8, 9],
        "lucky_gemstone_en": "Blue Sapphire (Neelam) or Amethyst",
        "lucky_gemstone_bn": "নীলা অথবা অ্যামেথিস্ট (কাটেলা)",
        "lucky_gemstone_hi": "नीलम अथवा जमुनिया (कटेला)",
        "padas": [
            {"pada": 1, "rashi_idx": 7, "navamsha": "Leo", "namakshar_en": "Na", "namakshar_bn": "না", "namakshar_hi": "ना"},
            {"pada": 2, "rashi_idx": 7, "navamsha": "Virgo", "namakshar_en": "Nee", "namakshar_bn": "নী", "namakshar_hi": "नी"},
            {"pada": 3, "rashi_idx": 7, "navamsha": "Libra", "namakshar_en": "Noo", "namakshar_bn": "নূ", "namakshar_hi": "नू"},
            {"pada": 4, "rashi_idx": 7, "navamsha": "Scorpio", "namakshar_en": "Ne", "namakshar_bn": "নে", "namakshar_hi": "ने"},
        ],
        "overview": {
            "en": "Anuradha is the lotus that blossoms above the muddy waters, representing devotion, resilience in adversity, and deep cosmic friendship. Ruled by Saturn in Mars' sign Scorpio, natives succeed far from home through quiet discipline.",
            "bn": "অনুরাধা পাঁকের মাঝে প্রস্ফুটিত শুচি শুভ্র পদ্মফুলের প্রতীক। প্রতিকূলতার মধ্যেও প্রীতি, ভক্তি ও বিশ্বস্ততার প্রতীক এটি। শনির শাসনে বৃশ্চিক রাশিস্থ এই জাতকরা জন্মস্থান থেকে দূরে গিয়ে প্রভূত উন্নতি ও যশ অর্জন করেন।",
            "hi": "अनुराधा नक्षत्र कीचड़ में खिलने वाले पवित्र कमल के समान है। यह मित्रता, ईश्वर भक्ति और संघर्षों के पार विजय का प्रतीक है। शनि के प्रभाव से जातक विदेश या जन्मभूमि से दूर जाकर अपार सफलता पाते हैं।",
        },
        "strengths": {
            "en": [
                "Unshakeable emotional loyalty, deep spiritual devotion, and heart-centered warmth",
                "Exceptional ability to build international bridges and foreign friendships",
                "Quiet discipline, patience under pressure, and enduring work ethic",
                "High capacity to organize dispersed communities toward noble missions",
            ],
            "bn": [
                "অকৃত্রিম হৃদয়বৃত্তি, গভীর ভক্তি ও বন্ধুদের প্রতি অটুট বিশ্বস্ততা",
                "বিদেশ বা দূরবর্তী স্থানে গিয়ে স্থায়ী সাফল্য ও সুসম্পর্ক গড়ে তোলার ক্ষমতা",
                "চাপের মুখেও অটল ধৈর্য, নীরব কর্মনিষ্ঠা ও চারিত্রিক দৃঢ়তা",
                "সমাজ ও বিভিন্ন মতের মানুষকে এক ছাতার তলায় এনে মহৎ কাজে উদ্বুদ্ধ করার গুণ",
            ],
            "hi": [
                "रिश्तों में प्रगाढ़ निष्ठा, ईश्वर में अटूट विश्वास और कोमल हृदय",
                "विदेश या दूरदराज के क्षेत्रों में जाकर नए संपर्क और प्रगति करने का कौशल",
                "विपत्ति में भी अडिग धैर्य, मौन रहकर कर्म करने की निष्ठा",
                "विभिन्न विचारधाराओं के लोगों को एकजुट करके बड़ा लक्ष्य पाने की क्षमता",
            ],
        },
        "cautions_and_pitfalls": {
            "en": [
                "Harboring suppressed sorrow, loneliness, or emotional secrecy",
                "Jealous vulnerabilities hidden beneath a calm smiling exterior",
                "Difficulty living peacefully in the ancestral hometown",
                "Digestive sluggishness, nasal/sinus congestion, and pelvic stiffness",
            ],
            "bn": [
                "ভেতরের দুঃখ ও একাকীত্ব বাইরে প্রকাশ না করে একা একা কষ্ট পাওয়া",
                "শান্ত মুখের আড়ালে তীব্র ঈর্ষা বা অভিমানে দগ্ধ হওয়া",
                "নিজের জন্মভূমিতে মানিয়ে নিতে কষ্ট হওয়া ও অস্বস্তি বোধ করা",
                "পেটের গোলযোগ, সাইনাস ও শ্রোণীদেশের (পেলভিস) সমস্যা",
            ],
            "hi": [
                "मन के दर्द और अकेलेपन को दबाकर रखना और अंदर ही अंदर घुलना",
                "शांत चेहरे के पीछे ईर्ष्या या उपेक्षा का गहरा घाव छुपाए रखना",
                "पैतृक स्थान पर शांति न मिलना और प्रवास की मजबूरी",
                "पाचन विकार, साइनस और शरीर के निचले भाग में दर्द",
            ],
        },
        "beneficial_actions_and_remedies": {
            "en": [
                "Plant and water a fragrant Bakul (Spanish Cherry) tree",
                "Worship Lord Shiva and perform regular meditation on the heart chakra",
                "Light a mustard oil lamp under a Peepal tree on Saturday evenings",
                "Donate blue blankets, iron utensils, or black sesame to elders on Saturdays",
            ],
            "bn": [
                "সুগন্ধি বকুল গাছ রোপণ করা ও তার যত্ন নেওয়া অত্যন্ত শুভ",
                "প্রতিদিন দেবাদিদেব মহাদেবের ধ্যান এবং অনাহত চক্রে শান্ত মনঃসংযোগ",
                "শনিবার সন্ধ্যায় অশ্বত্থ গাছের গোড়ায় সরিষার তেলের প্রদীপ প্রজ্বলন",
                "শনিবার বৃদ্ধ ও অসহায় মানুষকে কালো তিল, লোহার পাত্র বা কম্বল দান",
            ],
            "hi": [
                "मौलश्री (बकुल) का वृक्ष लगाएं और उसकी सेवा करें",
                "भगवान शिव की आराधना करें और हृदय चक्र पर ध्यान केंद्रित करें",
                "शनिवार की शाम को पीपल के पेड़ के नीचे सरसों के तेल का दीपक जलाएं",
                "शनिवार को वृद्धजनों को नीले कंबल अथवा लोहे के बर्तन दान करें",
            ],
        },
        "career_fields": {
            "en": ["International Foreign Relations & Diplomacy", "Deep Oceanography & Mining Exploration", "Music, Poetry & Mystical Arts", "Organizational Leadership & Community Trusts", "Holistic Psychiatry & Spiritual Counseling"],
            "bn": ["আন্তর্জাতিক কূটনীতি ও বৈদেশিক বাণিজ্য", "সমুদ্রবিজ্ঞান, খনিজ ও ভূগর্ভস্থ অনুসন্ধান", "সঙ্গীত, আধ্যাত্মিক কবিতা ও চারুকলা", "সামাজিক ট্রাস্ট ও স্বেচ্ছাসেবী সংগঠন পরিচালনা", "মনোচিকিৎসা ও আধ্যাত্মিক কাউন্সেলিং"],
            "hi": ["विदेश सेवा (IFS) व अंतरराष्ट्रीय संबंध", "समुद्र विज्ञान, खनन व भूगर्भ अन्वेषण", "संगीत, काव्य व सूफी कलाएं", "ट्रस्ट प्रबंधन व सामाजिक संगठन", "मनोचिकित्सा व आध्यात्मिक परामर्श"],
        },
    },
    {
        "index": 17,
        "name_en": "Jyeshtha",
        "name_bn": "জ্যেষ্ঠা",
        "name_hi": "ज्येष्ठा",
        "lord": "Mercury",
        "deity_en": "Indra (King of the Gods & Ruler of Storms)",
        "deity_bn": "ইন্দ্র (দেবতাদের মহারাজ ও বজ্রের অধিপতি)",
        "deity_hi": "देवराज इंद्र",
        "symbol_en": "Circular Amulet / Umbrella / Earring",
        "symbol_bn": "রক্ষাকবচ / রাজকীয় ছাতা / কর্ণাভরণ",
        "symbol_hi": "सुरक्षा ताबीज / छत्र / कुंडल",
        "gana_en": "Rakshasa",
        "gana_bn": "রাক্ষস",
        "gana_hi": "রাক্ষস",
        "yoni_en": "Deer (Male)",
        "yoni_bn": "হরিণ (পুং)",
        "yoni_hi": "मृग / हिरण (पुरुष)",
        "nadi_en": "Aadi (Vata)",
        "nadi_bn": "আদি (বাত)",
        "nadi_hi": "আদি (वात)",
        "sacred_tree_en": "Sal (Shorea robusta)",
        "sacred_tree_bn": "শাল গাছ",
        "sacred_tree_hi": "साल (साखू)",
        "beej_mantra": "ॐ বুধায় নমঃ / ॐ ইন্দ্রায় নমঃ",
        "lucky_color_en": "Emerald Green & Crimson Red",
        "lucky_color_bn": "পান্না সবুজ ও রক্তিম লাল",
        "lucky_color_hi": "पन्ना हरा और गहरा लाल",
        "lucky_numbers": [5, 1],
        "lucky_gemstone_en": "Emerald (Panna)",
        "lucky_gemstone_bn": "পান্না",
        "lucky_gemstone_hi": "पन्ना",
        "padas": [
            {"pada": 1, "rashi_idx": 7, "navamsha": "Sagittarius", "namakshar_en": "No", "namakshar_bn": "নো", "namakshar_hi": "नो"},
            {"pada": 2, "rashi_idx": 7, "navamsha": "Capricorn", "namakshar_en": "Ya", "namakshar_bn": "যা", "namakshar_hi": "या"},
            {"pada": 3, "rashi_idx": 7, "navamsha": "Aquarius", "namakshar_en": "Yee", "namakshar_bn": "যী", "namakshar_hi": "यी"},
            {"pada": 4, "rashi_idx": 7, "navamsha": "Pisces", "namakshar_en": "Yoo", "namakshar_bn": "যূ", "namakshar_hi": "यू"},
        ],
        "overview": {
            "en": "Jyeshtha represents the eldest, sovereign protector, holding supreme responsibility and battlefield command. Governed by Mercury in intense Scorpio and presided by Indra, natives possess sharp protective power, courage, and fierce pride.",
            "bn": "জ্যেষ্ঠা জ্যেষ্ঠ ভ্রাতা, সর্বপ্রধান অধিনায়ক এবং পরিবারের রক্ষাকর্তার প্রতীক। বুধের তীক্ষ্ণ বুদ্ধি এবং বৃশ্চিকের রহস্যময় শক্তিতে বলীয়ান এঁরা পরিবারের গুরুভার কাঁধে তুলে নেন। প্রচণ্ড আত্মমর্যাদা ও সাহসিকতা এঁদের মূল অলঙ্কার।",
            "hi": "ज्येष्ठा नक्षत्र ज्येष्ठता, सर्वोच्च सत्ता और रक्षक की शक्ति का प्रतीक है। देवराज इंद्र के प्रभाव से जातक स्वाभिमानी, साहसी, परिवार के संरक्षक और कठिन से कठिन चुनौतियों का डटकर सामना करने वाले होते हैं।",
        },
        "strengths": {
            "en": [
                "Exceptional courage to face crises head-on and protect dependents",
                "Sharp strategic intellect, administrative command, and executive authority",
                "Deep occult insights, psychological penetration, and lie-detection ability",
                "Honorable responsibility as the pillar of family or community",
            ],
            "bn": [
                "চরম সংকটের মুখে দাঁড়িয়ে বুক চিতিয়ে আশ্রিতজনকে রক্ষা করার সাহস",
                "তীক্ষ্ণ কৌশলগত বুদ্ধি, প্রশাসনিক নিয়ন্ত্রণ ও নেতৃত্বের দৃঢ়তা",
                "গূঢ় মনস্তত্ত্ব বোঝা এবং মিথ্যার মুখোশ নিমেষেই খসিয়ে দেওয়ার মেধা",
                "পরিবার বা সংগঠনের মূল স্তম্ভ হয়ে সমস্ত দায়িত্ব নিজের কাঁধে বহন করার মহত্ত্ব",
            ],
            "hi": [
                "संकट के समय सबसे आगे खड़े होकर अपनों की रक्षा करने का अद्भुत साहस",
                "कुशाग्र रणनीतिक बुद्धि, प्रशासनिक पकड़ और नेतृत्व क्षमता",
                "मनोवैज्ञानिक समझ और किसी के भी झूठ को पलक झपकते पकड़ लेने की कला",
                "परिवार या समाज का मुख्य आधार बनकर जिम्मेदारी निभाना",
            ],
        },
        "cautions_and_pitfalls": {
            "en": [
                "Hypersensitivity to perceived disrespect and harboring silent vengefulness",
                "Authoritarian dominance driving younger family members away",
                "Stubborn refusal to ask for help even when overwhelmed by burdens",
                "Pelvic, muscular, and colon distress; chronic shoulder tension",
            ],
            "bn": [
                "আত্মমর্যাদায় সামান্য আঁচ লাগলে অত্যন্ত ক্ষুব্ধ হওয়া ও মনে আক্রোশ পুষে রাখা",
                "অতিরিক্ত কর্তৃত্বপরায়ণ হয়ে অধস্তন বা ছোটদের মানসিক স্বাধীনতা খর্ব করা",
                "বিপদে পড়েও অহংকারের কারণে কারও কাছে সাহায্য চাইতে না পারা",
                "কোলোন, অর্শ, তলপেটে প্রদাহ ও কাঁধের পেশীতে তীব্র টান",
            ],
            "hi": [
                "अपमान बर्दाश्त न होना और मन में बदले की भावना पाल लेना",
                "अत्यधिक तानाशाही रवैया अपनाकर छोटों को नाराज कर देना",
                "कठिनाई में होने पर भी झूठे स्वाभिमान के कारण सहायता न मांगना",
                "बवासीर, आंतों में सूजन और कंधों व गर्दन में लगातार तनाव",
            ],
        },
        "beneficial_actions_and_remedies": {
            "en": [
                "Worship Lord Vishnu and Lord Hanuman regularly for humility and strength",
                "Plant and tend a sacred Sal tree",
                "Chant Vishnu Sahasranama on Wednesdays",
                "Donate green grams (moong dal), emeralds, or green cloth on Wednesdays",
            ],
            "bn": [
                "ভগবান শ্রীবিষ্ণু ও শ্রী হনুমানজির উপাসনা অহংকার দূর করে অন্তরে শক্তি জোগায়",
                "শালগাছ রোপণ ও তার সংরক্ষণ করা",
                "বুধবার বিষ্ণু সহস্রনাম পাঠ করা পরম কল্যাণকারী",
                "বুধবার সবুজ মুগ ডাল, সবুজ বস্ত্র বা ফল দরিদ্রকে দান",
            ],
            "hi": [
                "भगवान विष्णु और हनुमानजी की नित्य आराधना करें",
                "साल (साखू) का वृक्ष लगाएं",
                "बुधवार को विष्णु सहस्त्रनाम का पाठ करें",
                "बुधवार को साबुत मूंग दाल, हरे वस्त्र या फल दान करें",
            ],
        },
        "career_fields": {
            "en": ["Military Defense & Tactical Warfare", "Corporate Restructuring & Crisis Management", "Law Enforcement & Criminal Investigation", "Occult & Esoteric Research", "Senior Bureaucracy & Judicial Bench"],
            "bn": ["সামরিক প্রতিরক্ষা ও কৌশলগত কমান্ড", "কর্পোরেট পুনর্গঠন ও ক্রাইসিস ম্যানেজমেন্ট", "পুলিশ ও গোয়েন্দা তদন্ত", "গুপ্তবিদ্যা ও মনস্তাত্ত্বিক গবেষণা", "উচ্চ আমলাতন্ত্র ও বিচারবিভাগ"],
            "hi": ["सैन्य कमान व रक्षा रणनीति", "संकट प्रबंधन व कंपनी का कायाकल्प", "पुलिस सेवा व अपराध अनुसंधान", "रहस्य विद्याएं व गहन शोध", "वरिष्ठ नौकरशाही व न्यायपालिका"],
        },
    },
    {
        "index": 18,
        "name_en": "Mula",
        "name_bn": "মূলা",
        "name_hi": "मूल",
        "lord": "Ketu",
        "deity_en": "Nirriti (Goddess of Dissolution & Cosmic Roots)",
        "deity_bn": "নিরঋতি (মহাপ্রলয় ও মূল উৎসের অধিশ্বরী দেবী)",
        "deity_hi": "निरृति देवी (विनाश व मूल तत्व की देवी)",
        "symbol_en": "Tied Bundle of Roots / Elephant's Goad",
        "symbol_bn": "শিকড়ের গুচ্ছ / অঙ্কুশ",
        "symbol_hi": "जड़ों का बंधा हुआ गुच्छा / अंकुश",
        "gana_en": "Rakshasa",
        "gana_bn": "রাক্ষস",
        "gana_hi": "রাক্ষস",
        "yoni_en": "Dog (Male)",
        "yoni_bn": "শ্বান / কুকুর (পুং)",
        "yoni_hi": "श्वान / कुत्ता (पुरुष)",
        "nadi_en": "Aadi (Vata)",
        "nadi_bn": "আদি (বাত)",
        "nadi_hi": "आदि (वात)",
        "sacred_tree_en": "Semal / Silk Cotton (Bombax ceiba)",
        "sacred_tree_bn": "শিমুল গাছ",
        "sacred_tree_hi": "सेमल",
        "beej_mantra": "ॐ কেতবে নমঃ / ॐ নির্ঋতয়ে নমঃ",
        "lucky_color_en": "Golden Brown & Dark Crimson",
        "lucky_color_bn": "গাঢ় খয়েরি ও তামাটে লাল",
        "lucky_color_hi": "भूरा स्वर्णिम और गहरा लाल",
        "lucky_numbers": [7, 9],
        "lucky_gemstone_en": "Cat's Eye (Vaidurya)",
        "lucky_gemstone_bn": "বৈদূর্যমণি (ক্যাটস আই)",
        "lucky_gemstone_hi": "लहसुनिया (कैट्स आई)",
        "padas": [
            {"pada": 1, "rashi_idx": 8, "navamsha": "Aries", "namakshar_en": "Ye", "namakshar_bn": "য়ে", "namakshar_hi": "ये"},
            {"pada": 2, "rashi_idx": 8, "navamsha": "Taurus", "namakshar_en": "Yo", "namakshar_bn": "য়ো", "namakshar_hi": "यो"},
            {"pada": 3, "rashi_idx": 8, "navamsha": "Gemini", "namakshar_en": "Bha", "namakshar_bn": "ভা", "namakshar_hi": "भा"},
            {"pada": 4, "rashi_idx": 8, "navamsha": "Cancer", "namakshar_en": "Bhee", "namakshar_bn": "ভী", "namakshar_hi": "भी"},
        ],
        "overview": {
            "en": "Mula marks the galactic center, representing the root origin of existence and the transformative power of dissolution. Ruled by Ketu at the gateway of Sagittarius, natives possess fearlessness in uprooting falsehoods to reach the ultimate truth.",
            "bn": "মূলা গ্যালাক্সির কেন্দ্রবিন্দু এবং সৃষ্টির মূল উৎসের প্রতীক। এটি ধ্বংসের মধ্য দিয়ে পুনর্গঠন ও আমূল রূপান্তরের দ্যোতক। কেতু ও বৃহস্পতির সংযোগে জাতকরা অসত্যকে সমূলে উপড়ে ফেলে পরম সত্য ও জ্ঞানের সন্ধান করেন।",
            "hi": "मूल नक्षत्र ब्रह्मांड के केंद्र और अस्तित्व के मूल आधार का प्रतीक है। केतु के प्रभाव से जातक किसी भी बात की तह तक जाने वाले, सत्य के लिए पुराने ढर्रे को तोड़ देने वाले और क्रांतिकारी सोच वाले होते हैं।",
        },
        "strengths": {
            "en": [
                "Unmatched power to investigate the root causes of disease, problems, and mysteries",
                "Complete fearlessness in the face of radical change and upheaval",
                "Profound spiritual depth and philosophical detachment from material illusions",
                "Direct, uncompromising truthfulness that shatters pretenses",
            ],
            "bn": [
                "যে কোনো সমস্যা, রোগ বা রহস্যের একেবারে শিকড় পর্যন্ত অনুসন্ধান করার অতুলনীয় মেধা",
                "জীবনের চরম পরিবর্তন বা ঝড়ের মুখেও বিন্দুমাত্র ভয় না পেয়ে অবিচল থাকা",
                "গভীর আধ্যাত্মিক জ্ঞান এবং পার্থিব মোহমায়ার প্রতি আশ্চর্য নির্লিপ্ততা",
                "স্পষ্টবাদী ও আপসহীন সত্যভাষণ যা ভণ্ডামিকে এক নিমেষে চূর্ণ করে দেয়",
            ],
            "hi": [
                "किसी भी समस्या, रोग अथवा रहस्य के मूल कारण तक पहुंचने की अद्भुत प्रतिभा",
                "जीवन के बड़े उलटफेरों और तूफानों के सामने भी पूरी तरह निडर रहना",
                "गहरी दार्शनिक समझ और सांसारिक दिखावे से विरक्त रहने का भाव",
                "सत्य के प्रति अटूट निष्ठा और आडंबर को तुरंत उजागर करने का साहस",
            ],
        },
        "cautions_and_pitfalls": {
            "en": [
                "Destructive restlessness, abruptly uprooting relationships and homes",
                "Brutally blunt speech inflicting painful emotional scars on others",
                "Deep internal dissatisfaction bordering on nihilistic cynicism",
                "Sciatica, hip joint pains, and pelvic bone vulnerabilities",
            ],
            "bn": [
                "চঞ্চলতা ও ধ্বংসাত্মক মনোভাব—হঠাৎ সম্পর্ক ছিন্ন করে দূরে সরে যাওয়া",
                "নির্মম স্পষ্ট কথা বলে অন্যের মনে গভীর ক্ষত তৈরি করার অভ্যাস",
                "অন্তরের অতৃপ্তি ও ক্ষোভ থেকে সবকিছুকে অর্থহীন ভাবার নৈরাশ্য",
                "সায়াটিকা, কোমর ও নিতম্বের অস্থিসন্ধিতে তীব্র ব্যথার প্রবণতা",
            ],
            "hi": [
                "अचानक सब कुछ छोड़ देने या बने बनाए संबंधों को तोड़ देने की सनक",
                "अति कड़वे शब्दों से दूसरों के दिलों को छलनी कर देना",
                "भीतरी असंतोष के चलते हर बात में नकारात्मकता देखना",
                "साइटिका, कूल्हे के जोड़ों में दर्द और हड्डियों की कमजोरी",
            ],
        },
        "beneficial_actions_and_remedies": {
            "en": [
                "Worship Lord Ganesha with red flowers and Durva grass to anchor energy",
                "Plant and nurture a Semal (Silk Cotton) tree",
                "Serve and feed street dogs with love; respect elders and ascetics",
                "Donate roots (ginger, turmeric, sweet potatoes) or mustard blankets on Saturdays",
            ],
            "bn": [
                "শ্রী গণেশের চরণে রক্তজবা ও দূর্বাঘাস দিয়ে পূজা মনকে শান্ত ও স্থির রাখে",
                "শিমুল গাছ রোপণ করা ও প্রকৃতির পরিচর্যা করা",
                "পথের কুকুরদের আহার দেওয়া এবং সাধু-সন্তদের শ্রদ্ধা ও সেবা",
                "শনিবার মূলজাতীয় খাদ্য (আদা, হলুদ, মিষ্টি আলু) বা কম্বল দুঃস্থদের দান",
            ],
            "hi": [
                "भगवान गणेश को दूर्वा और लाल पुष्प अर्पित करके नित्य आराधना करें",
                "सेमल का वृक्ष लगाएं",
                "सड़क के कुत्तों को नियमित भोजन दें, साधु-संतों की सेवा करें",
                "शनिवार को जमीन के नीचे उगने वाली वस्तुएं (आलू, हल्दी, अदरक) दान करें",
            ],
        },
        "career_fields": {
            "en": ["Deep Investigative Research & Forensics", "Botanical & Herbal Root Medicine", "Geological Exploration & Petroleum Mining", "Philosophy, Asceticism & Religious Leadership", "Disaster Management & Demolition Engineering"],
            "bn": ["ফরেনসিক তদন্ত ও গভীর অপরাধ বিজ্ঞান", "ভেষজ উদ্ভিদ ও আয়ুর্বেদিক চিকিৎসা", "ভূতাত্ত্বিক খনিজ ও পেট্রোলিয়াম নিষ্কাশন", "দর্শনশাস্ত্র, যোগসাধনা ও আধ্যাত্মিক নেতৃত্ব", "দুর্যোগ ব্যবস্থাপনা ও প্রকৌশল"],
            "hi": ["फॉरेंसिक विज्ञान व गहन अपराध अनुसंधान", "आयुर्वेदिक व वानस्पतिक औषधि निर्माण", "भूगर्भ विज्ञान व पेट्रोलियम उत्खनन", "दर्शन, संन्यास व आध्यात्मिक उपदेश", "आपदा प्रबंधन व संरचनात्मक रूपांतरण"],
        },
    },
    {
        "index": 19,
        "name_en": "Purva Ashadha",
        "name_bn": "পূর্বাষাঢ়া",
        "name_hi": "पूर्वाषाढ़ा",
        "lord": "Venus",
        "deity_en": "Apah (The Cosmic Waters of Grace & Purification)",
        "deity_bn": "অপঃ / বরুণ (পবিত্র জল ও শুদ্ধিকরণের অধিপতি)",
        "deity_hi": "आपः (जल तत्व के देवता)",
        "symbol_en": "Winnowing Basket / Hand Fan",
        "symbol_bn": "কুলা / হাতপাখা",
        "symbol_hi": "सूप (अनाज फटकने का) / पंखा",
        "gana_en": "Manushya",
        "gana_bn": "মনুষ্য",
        "gana_hi": "मनुष्य",
        "yoni_en": "Monkey (Male)",
        "yoni_bn": "বানর / কপি (পুং)",
        "yoni_hi": "वानर / बंदर (पुरुष)",
        "nadi_en": "Madhya (Pitta)",
        "nadi_bn": "মধ্য (পিত্ত)",
        "nadi_hi": "मध्य (पित्त)",
        "sacred_tree_en": "Vetiver / Khus (Vetiveria zizanioides)",
        "sacred_tree_bn": "বেতগাছ / খসখস",
        "sacred_tree_hi": "खस (उशीर) / बेंत",
        "beej_mantra": "ॐ শুক্রায় নমঃ / ॐ অদ্ভ্যো নমঃ",
        "lucky_color_en": "Sea Green & Pearlescent White",
        "lucky_color_bn": "সমুদ্র সবুজ ও মুক্তাভ শুভ্র",
        "lucky_color_hi": "समुद्री हरा और श्वेत",
        "lucky_numbers": [6, 3],
        "lucky_gemstone_en": "Diamond (Heera) or White Sapphire",
        "lucky_gemstone_bn": "হীরে অথবা সাদা পোখরাজ",
        "lucky_gemstone_hi": "हीरा अथवा श्वेत पुखराज",
        "padas": [
            {"pada": 1, "rashi_idx": 8, "navamsha": "Leo", "namakshar_en": "Bhoo", "namakshar_bn": "ভূ", "namakshar_hi": "भू"},
            {"pada": 2, "rashi_idx": 8, "navamsha": "Virgo", "namakshar_en": "Dha", "namakshar_bn": "ধা", "namakshar_hi": "धा"},
            {"pada": 3, "rashi_idx": 8, "navamsha": "Libra", "namakshar_en": "Pha", "namakshar_bn": "ফা", "namakshar_hi": "फा"},
            {"pada": 4, "rashi_idx": 8, "navamsha": "Scorpio", "namakshar_en": "Dha", "namakshar_bn": "ঢা", "namakshar_hi": "ढा"},
        ],
        "overview": {
            "en": "Purva Ashadha is the invincible star of unshakeable conviction, purification, and joyous celebration. Ruled by Venus in visionary Sagittarius, natives possess inspiring eloquence, persuasive power, and majestic self-confidence.",
            "bn": "পূর্বাষাঢ়া অপরাজেয় আত্মবিশ্বাস এবং পবিত্র জলের মতো শুদ্ধিকরণের প্রতীক। ধনু রাশিতে শুক্রের প্রভাব এঁদের তেজস্বী বক্তা, অননুকরণীয় ব্যক্তিত্বসম্পন্ন, সুদূরপ্রসারী দূরদৃষ্টির অধিকারী এবং অপরাজেয় মনোভাবের অধিকারী করে তোলে।",
            "hi": "पूर्वाषाढ़ा नक्षत्र अजेय आत्मविश्वास, पवित्रता और वाक्पटुता का प्रतीक है। धनु राशि में शुक्र के प्रभाव से जातक ओजस्वी वक्ता, दूरदर्शी, स्वाभिमानी और किसी भी चुनौती के आगे कभी हार न मानने वाले होते हैं।",
        },
        "strengths": {
            "en": [
                "Unconquerable spirit and boundless self-confidence in difficult trials",
                "Powerful oratorical skills that sway, inspire, and purify large audiences",
                "Natural talent in philosophy, judicial advocacy, and creative literature",
                "Deep compassionate connection with waterways, nature, and animals",
            ],
            "bn": [
                "অপরাজেয় মনোবল—কোনো সংকট বা বিরোধিতাতেই কখনো নিজের বিশ্বাস না হারানো",
                "অনলবর্ষী ও অনুপ্রেরণাদায়ী বক্তৃতা দিয়ে হাজার হাজার মানুষকে উদ্বুদ্ধ করার ক্ষমতা",
                "দর্শনশাস্ত্র, আইন তর্ক এবং উচ্চমানের সৃজনশীল সাহিত্যে অনন্য পারদর্শিতা",
                "প্রকৃতি, নদী-সমুদ্র এবং পশুপাখির প্রতি গভীর মমতবোধ",
            ],
            "hi": [
                "अदम्य साहस और दृढ़ संकल्प—परिस्थितियां कितनी भी कठिन हों, आत्मबल न डिगना",
                "अद्भुत भाषण कला जिससे जनसमूह को प्रेरित और मंत्रमुग्ध कर दें",
                "दर्शन, साहित्य, कानून और सृजनात्मक लेखन में गहरी रुचि",
                "प्रकृति, जल स्रोतों और पशु-पक्षियों के प्रति गहरा स्नेह",
            ],
        },
        "cautions_and_pitfalls": {
            "en": [
                "Overweening arrogance, stubborn righteousness refusing counter-arguments",
                "Tendency to lecture others and overlook one's own blind spots",
                "Lavish over-spending on social celebrations and self-aggrandizement",
                "Water retention, bladder inflammation, and thigh/femur vulnerabilities",
            ],
            "bn": [
                "অতিরিক্ত অহংকার এবং নিজের মতকেই একমাত্র ঠিক মনে করে অন্যের কথা উড়িয়ে দেওয়া",
                "অন্যকে উপদেশ দিতে গিয়ে নিজের ভুলত্রুটি উপেক্ষা করার প্রবণতা",
                "উৎসব ও দেখনদারির পেছনে আয়ের অতিরিক্ত অমিতব্যয়িতা",
                "শরীরে জল জমা, মূত্রাশয়ের প্রদাহ এবং উরুর পেশীতে ব্যথা",
            ],
            "hi": [
                "अत्यधिक दर्प और अपनी बात को ही सही मानकर दूसरों को गलत ठहराना",
                "दूसरों को सीख देना परंतु अपनी कमियों की ओर ध्यान न देना",
                "दिखावे और उत्सवों में अंधाधुंध धन खर्च करने की आदत",
                "जल भराव (सूजन), मूत्राशय संबंधी रोग और जांघों में दर्द",
            ],
        },
        "beneficial_actions_and_remedies": {
            "en": [
                "Honor natural water bodies; keep rivers, lakes, and oceans clean",
                "Worship Goddess Lakshmi with fragrant white lotuses on Fridays",
                "Plant and tend Vetiver (Khus) or bamboo plants",
                "Donate water, cooling beverages, or white sweets to laborers on Fridays",
            ],
            "bn": [
                "নদী ও জলাশয় পরিষ্কার রাখা এবং জলের অপচয় সম্পূর্ণ বন্ধ করা",
                "শুক্রবার দেবী লক্ষ্মীর চরণে সুগন্ধি শ্বেতপদ্ম নিবেদন",
                "বেতগাছ বা সুগন্ধি খসখস গাছের পরিচর্যা করা",
                "শুক্রবার তৃষ্ণার্ত পথচারীকে বিশুদ্ধ জল, শরবত বা মিষ্টি দান",
            ],
            "hi": [
                "जल का आदर करें, नदियों व तालाबों को कभी दूषित न करें",
                "शुक्रवार को मां लक्ष्मी की आराधना करें और श्वेत पुष्प अर्पित करें",
                "खस या बेंत का पौधा लगाएं",
                "शुक्रवार को राहगीरों को शीतल जल, शर्बत या सफेद मिठाई दान करें",
            ],
        },
        "career_fields": {
            "en": ["Maritime Shipping & Ocean Trade", "Motivational Public Speaking & Authorship", "International Law & High Court Litigation", "Film Production, Scriptwriting & Theater", "Environmental Hydrology & Water Conservation"],
            "bn": ["নৌপরিবহন, বন্দর ও সামুদ্রিক বাণিজ্য", "অনুপ্রেরণাদায়ী বক্তা ও আন্তর্জাতিক লেখক", "উচ্চ আদালত ও আন্তর্জাতিক আইন পেশা", "চলচ্চিত্র পরিচালনা, চিত্রনাট্য ও নাট্যকলা", "পরিবেশবিদ্যা ও জলসম্পদ সংরক্ষণ"],
            "hi": ["समुद्री व्यापार, जहाजरानी व नौसेना", "प्रेरक वक्ता (Motivational Speaker) व लेखक", "उच्च न्यायालय व सुप्रीम कोर्ट में वकालत", "फिल्म निर्माण, पटकथा लेखन व निर्देशन", "जल संरक्षण व पर्यावरण विज्ञान"],
        },
    },
    {
        "index": 20,
        "name_en": "Uttara Ashadha",
        "name_bn": "উত্তরাষাঢ়া",
        "name_hi": "उत्तराषाढ़ा",
        "lord": "Sun",
        "deity_en": "Vishwadevas (Ten Universal Cosmic Deities of Dharma)",
        "deity_bn": "বিশ্বেদেবাগণ (ধর্ম, সত্য ও মহাজাগতিক ঐক্যের ১০ দেবতা)",
        "deity_hi": "विश्वेदेवा (धर्म व सत्य के दस सार्वभौमिक देव)",
        "symbol_en": "Elephant's Tusk / Small Cot",
        "symbol_bn": "হস্তীর দন্ত / ক্ষুদ্র খাট",
        "symbol_hi": "हाथी का दांत / छोटा पलंग",
        "gana_en": "Manushya",
        "gana_bn": "মনুষ্য",
        "gana_hi": "मनुष्य",
        "yoni_en": "Mongoose (Male)",
        "yoni_bn": "নকুল / বেজি (পুং)",
        "yoni_hi": "नकुल / नेवला (पुरुष)",
        "nadi_en": "Antya (Kapha)",
        "nadi_bn": "অন্ত্য (কফ)",
        "nadi_hi": "अंत्य (कফ)",
        "sacred_tree_en": "Jackfruit (Artocarpus heterophyllus)",
        "sacred_tree_bn": "কাঁঠাল গাছ",
        "sacred_tree_hi": "कटहल",
        "beej_mantra": "ॐ সূর্যায় নমঃ / ॐ বিশ্বেদেবেভ্যো নমঃ",
        "lucky_color_en": "Copper Gold & Pure White",
        "lucky_color_bn": "তামাটে সোনালী ও নিষ্কলঙ্ক শুভ্র",
        "lucky_color_hi": "ताम्र स्वर्णिम और शुद्ध श्वेत",
        "lucky_numbers": [1, 8],
        "lucky_gemstone_en": "Ruby (Manikya) or Blue Sapphire",
        "lucky_gemstone_bn": "চুনি অথবা নীলা",
        "lucky_gemstone_hi": "माणिक्य अथवा नीलम",
        "padas": [
            {"pada": 1, "rashi_idx": 8, "navamsha": "Sagittarius", "namakshar_en": "Bhe", "namakshar_bn": "ভে", "namakshar_hi": "भे"},
            {"pada": 2, "rashi_idx": 9, "navamsha": "Capricorn", "namakshar_en": "Bho", "namakshar_bn": "ভো", "namakshar_hi": "भो"},
            {"pada": 3, "rashi_idx": 9, "navamsha": "Aquarius", "namakshar_en": "Ja", "namakshar_bn": "জা", "namakshar_hi": "जा"},
            {"pada": 4, "rashi_idx": 9, "navamsha": "Pisces", "namakshar_en": "Jee", "namakshar_bn": "জী", "namakshar_hi": "जी"},
        ],
        "overview": {
            "en": "Uttara Ashadha represents final, enduring victory won through patience, unshakeable righteousness, and collective dharma. Governed by the Sun bridging Sagittarius and Capricorn, natives are deeply respected statesmen.",
            "bn": "উত্তরাষাঢ়া ধৈর্য, ন্যায়নিষ্ঠা এবং ধর্মের শক্তিতে অর্জিত চিরন্তন বিজয়ের প্রতীক। সূর্যের দীপ্তি ও শনির শৃঙ্খলার সমন্বয়ে এই জাতকরা অত্যন্ত বিনয়ী, গভীর শ্রদ্ধাশীল, আদর্শবাদী রাষ্ট্রনেতা এবং নির্ভরযোগ্য মানুষ হন।",
            "hi": "उत्तराषाढ़ा नक्षत्र सत्य, धैर्य और धर्म के मार्ग पर चलकर प्राप्त होने वाली अंतिम विजय का प्रतीक है। सूर्य और शनि के संतुलन से जातक अत्यंत गंभीर, कर्तव्यपरायण, आदरणीय और न्यायप्रिय राजनेता बनते हैं।",
        },
        "strengths": {
            "en": [
                "Unshakeable commitment to truth, duty, and higher moral codes",
                "Deep modesty and humility despite massive professional accomplishments",
                "Enduring stamina; climbs to the highest peaks of success methodically",
                "Universal brotherhood mindset that unites diverse people harmoniously",
            ],
            "bn": [
                "সত্য, কর্তব্য এবং উচ্চতর নীতিবোধের প্রতি আজীবন অবিচল নিষ্ঠা",
                "বিপুল সাফল্য ও ক্ষমতার অধিকারী হওয়া সত্ত্বেও অহংকারহীন পরম বিনয়",
                "ধৈর্য ও কঠোর পরিশ্রমের শক্তিতে ধীরে ধীরে সমাজের শীর্ষস্থানে আরোহণ",
                "বিশ্বজনীন ভ্রাতৃত্ববোধ যার মাধ্যমে সকল স্তরের মানুষকে আপন করে নেওয়া",
            ],
            "hi": [
                "कर्तव्य, सत्य और उच्च नैतिक मूल्यों के प्रति अटूट निष्ठा",
                "बड़ी से बड़ी सफलता पाने पर भी अहंकार न करना, सहज विनम्रता",
                "धैर्य और अनवरत परिश्रम से धीरे-धीरे सर्वोच्च पद तक पहुंचना",
                "सबको साथ लेकर चलने और सामाजिक समरसता स्थापित करने का गुण",
            ],
        },
        "cautions_and_pitfalls": {
            "en": [
                "Excessive austerity and melancholy; carrying the world's weight alone",
                "Rigid stubbornness when moral rules are questioned",
                "Difficulty expressing warm playfulness, appearing distant or aloof",
                "Knee joint pains, arthritis, skin dryness, and eye strain",
            ],
            "bn": [
                "অতিরিক্ত কঠোর আত্মসংযম এবং নিজের ওপর সব দায়িত্ব নিয়ে মনমরা থাকা",
                "নিয়মকানুনের ব্যাপারে অতিরিক্ত অনমনীয় ও আপসহীন একগুঁয়েমি",
                "মনের গভীর স্নেহ ও ভালোবাসা সহজে প্রকাশ করতে না পারা",
                "হাঁটুর জয়েন্টে ব্যথা, বাত, শুষ্ক ত্বক ও চোখের দুর্বলতা",
            ],
            "hi": [
                "अत्यधिक गंभीरता और अकेलापन—सबका बोझ अकेले ढोने का तनाव",
                "नियमों के प्रति इतने कठोर हो जाना कि कोई लचीलापन न रहे",
                "अपनी भावनाएं और स्नेह खुलकर व्यक्त न कर पाना, अलग-थलग दिखना",
                "घुटनों में दर्द, गठिया, त्वचा का सूखापन और आंखों में थकान",
            ],
        },
        "beneficial_actions_and_remedies": {
            "en": [
                "Offer Arghya to the morning Sun daily while reciting the Gayatri Mantra",
                "Plant and tend a Jackfruit tree; share its produce",
                "Worship Lord Ganesha and Lord Shiva regularly",
                "Donate wheat, jaggery, or copper to laborers and elders on Sundays",
            ],
            "bn": [
                "প্রতিদিন সকালে সূর্যপ্রণাম ও একমনে গায়ত্রী মন্ত্র জপ",
                "একটি কাঁঠাল গাছ রোপণ করা এবং তার ফল সকলকে বিলিয়ে দেওয়া",
                "শ্রী গণেশ ও দেবাদিদেব মহাদেবের নিয়মিত উপাসনা",
                "রবিবার গম, গুড় বা তামার পাত্র সৎ উদ্দেশ্যে দান করা",
            ],
            "hi": [
                "प्रतिदिन सूर्य को जल अर्पित करें और गायत्री मंत्र का पाठ करें",
                "कटहल का वृक्ष लगाएं और पर्यावरण की सेवा करें",
                "भगवान गणेश और शिवजी की नित्य पूजा करें",
                "रविवार को गेहूं, गुड़ अथवा तांबे के पात्र का दान करें",
            ],
        },
        "career_fields": {
            "en": ["Constitutional Law & Supreme Judiciary", "Civil Service & Chief Ministerial Bureaucracy", "Scientific Research Institutions & Think Tanks", "Military High Command & Defense Strategy", "Pioneering Infrastructure & Heavy Engineering"],
            "bn": ["সাংবিধানিক আইন ও সুপ্রিম জুডিশিয়ারি", "আইএএস (IAS) ও সর্বোচ্চ সরকারি আমলাতন্ত্র", "বৈজ্ঞানিক গবেষণা প্রতিষ্ঠান ও নীতি নির্ধারণ", "সামরিক হাই কমান্ড ও প্রতিরক্ষা কৌশল", "জাতীয় পরিকাঠামো ও ভারী প্রকৌশল শিল্প"],
            "hi": ["संवैधानिक कानून व सर्वोच्च न्यायालय में न्यायधीश", "भारतीय प्रशासनिक सेवा (IAS) व नीति आयोग", "वैज्ञानिक शोध संस्थान व थिंक टैंक", "सैन्य उच्च कमान व रक्षा रणनीति", "राष्ट्रीय अवसंरचना व भारी उद्योग"],
        },
    },
    {
        "index": 21,
        "name_en": "Shravana",
        "name_bn": "শ্রবণা",
        "name_hi": "श्रवण",
        "lord": "Moon",
        "deity_en": "Lord Vishnu (The Preserver & Cosmic Sustainer)",
        "deity_bn": "শ্রীবিষ্ণু (জগতের পালনকর্তা ও সত্যের প্রতীক)",
        "deity_hi": "भगवान श्री हरि विष्णु",
        "symbol_en": "Ear / Three Footprints",
        "symbol_bn": "কর্ণ (কান) / তিনটি ত্রিপাদ পদচিহ্ন",
        "symbol_hi": "कान / वामन देव के तीन पग",
        "gana_en": "Deva",
        "gana_bn": "দেব",
        "gana_hi": "দেব",
        "yoni_en": "Monkey (Female)",
        "yoni_bn": "বানর / কপি (স্ত্রী)",
        "yoni_hi": "वानर / बंदर (स्त्री)",
        "nadi_en": "Antya (Kapha)",
        "nadi_bn": "অন্ত্য (কফ)",
        "nadi_hi": "अंत्य (कफ)",
        "sacred_tree_en": "Akanda / Calotropis (Calotropis gigantea)",
        "sacred_tree_bn": "আকন্দ গাছ",
        "sacred_tree_hi": "मदार (आक)",
        "beej_mantra": "ॐ বিষ্ণবে নমঃ / ॐ চন্দ্রায় নমঃ",
        "lucky_color_en": "Sky Blue & Ocean Cyan",
        "lucky_color_bn": "আকাশি নীল ও সমুদ্র নীল",
        "lucky_color_hi": "आसमानी नीला और समुद्री नीला",
        "lucky_numbers": [2, 8],
        "lucky_gemstone_en": "Pearl (Moti) or Blue Sapphire",
        "lucky_gemstone_bn": "মুক্তো অথবা নীলা",
        "lucky_gemstone_hi": "मोती अथवा नीलम",
        "padas": [
            {"pada": 1, "rashi_idx": 9, "navamsha": "Aries", "namakshar_en": "Khi", "namakshar_bn": "খী", "namakshar_hi": "खी"},
            {"pada": 2, "rashi_idx": 9, "navamsha": "Taurus", "namakshar_en": "Khu", "namakshar_bn": "খূ", "namakshar_hi": "खू"},
            {"pada": 3, "rashi_idx": 9, "navamsha": "Gemini", "namakshar_en": "Khe", "namakshar_bn": "খে", "namakshar_hi": "खे"},
            {"pada": 4, "rashi_idx": 9, "navamsha": "Cancer", "namakshar_en": "Kho", "namakshar_bn": "খো", "namakshar_hi": "खो"},
        ],
        "overview": {
            "en": "Shravana is the star of attentive listening, learning, and preservation of sacred oral wisdom. Presided over by Lord Vishnu, natives are profound scholars, attentive listeners, ethical counselors, and seekers of knowledge.",
            "bn": "শ্রবণা গভীর মনোযোগ দিয়ে শ্রবণ, জ্ঞান অর্জন এবং পবিত্র সনাতন জ্ঞান রক্ষার প্রতীক। ভগবান শ্রীবিষ্ণুর প্রত্যক্ষ কৃপাধন্য এই জাতকরা অনন্য শ্রোতা, সুপণ্ডিত, ন্যায়পরায়ণ উপদেষ্টা এবং আজীবন শিক্ষার্থী হন।",
            "hi": "श्रवण नक्षत्र एकाग्र होकर सुनने, सीखने और ज्ञान के संरक्षण का प्रतीक है। भगवान विष्णु के आशीर्वाद से जातक उत्तम श्रोता, विद्वान, गंभीर, नीतिवान और आजीवन ज्ञान की खोज में रत रहने वाले होते हैं।",
        },
        "strengths": {
            "en": [
                "Exceptional active listening power; absorbs, synthesizes, and remembers complex knowledge",
                "Deep devotion, moral uprightness, and scholarly cultural refinement",
                "Talent in teaching, speechwriting, audio arts, and public guidance",
                "Capacity to preserve heritage and bridge ancient wisdom with modern applications",
            ],
            "bn": [
                "মনোযোগ দিয়ে শোনার দুর্লভ গুণ—যেকোনো কঠিন তত্ত্ব শুনেই হৃদয়ে ধারণ করা",
                "ঈশ্বরভক্তি, নিখাদ সততা এবং মার্জিত সামাজিক শিষ্টাচার",
                "শিক্ষাদান, ভাষণ রচনা, সঙ্গীত ও সমাজকে সঠিক দিশা দেখানোর মেধা",
                "প্রাচীন ঐতিহ্য সংরক্ষণ করে আধুনিক প্রজন্মের কাছে তা তুলে ধরার ক্ষমতা",
            ],
            "hi": [
                "उत्कृष्ट श्रवण क्षमता—जटिल से जटिल ज्ञान को सुनकर कंठस्थ कर लेना",
                "ईश्वर भक्ति, उच्च चारित्रिक शुचिता और बौद्धिक परिपक्वता",
                "शिक्षण, परामर्श, संगीत और जनमानस को सही राह दिखाने में दक्षता",
                "प्राचीन ज्ञान व संस्कृति को सुरक्षित रखकर आधुनिक रूप में प्रस्तुत करना",
            ],
        },
        "cautions_and_pitfalls": {
            "en": [
                "Vulnerability to deceptive flattery and malicious gossip heard from others",
                "Restless wanderlust in search of elusive spiritual mentors",
                "Over-sensitivity to rumors affecting personal reputation",
                "Ear infections, lymphatic imbalances, knee arthritis, and digestive slowness",
            ],
            "bn": [
                "অন্যের মিষ্টি কথা বা কানভাঙানি শুনে সহজে প্রভাবিত হওয়ার দুর্বলতা",
                "উপযুক্ত গুরুর সন্ধানে এদিক-ওদিক ছুটে গিয়ে বিভ্রান্ত হওয়া",
                "নিজের সম্মান ও অপপ্রচারের ব্যাপারে অতিরিক্ত সংবেদনশীল থাকা",
                "কানের সমস্যা, বাত, হাঁটুর ব্যথা ও হজমশক্তি দুর্বল হওয়া",
            ],
            "hi": [
                "दूसरों की बातों या अफवाहों में जल्दी आकर भ्रमित हो जाना",
                "सच्चे गुरु की तलाश में बेचैन होकर यहां-वहां भटकना",
                "अपनी छवि को लेकर अत्यधिक चिंतित व भावुक हो जाना",
                "कान के रोग, घुटनों में दर्द और कफ जनित समस्याएं",
            ],
        },
        "beneficial_actions_and_remedies": {
            "en": [
                "Chant Vishnu Sahasranama or Om Namo Bhagavate Vasudevaya daily",
                "Plant and tend an Akanda (Calotropis) plant",
                "Listen to classical sacred music or audiobooks to train the ear",
                "Donate books, audio learning aids, or milk on Mondays and Thursdays",
            ],
            "bn": [
                "প্রতিদিন একমনে 'ॐ নমো ভগবতে বাসুদেবায়' মন্ত্র জপ পরম শান্তি এনে দেয়",
                "আকন্দ গাছ লাগানো এবং দেবাদিদেব মহাদেবের চরণে আকন্দ ফুল নিবেদন",
                "উচ্চমানের ধ্রুপদী সঙ্গীত বা মহৎ বাণী নিয়মিত শ্রবণ করা",
                "সোমবার বা বৃহস্পতিবারে ছাত্রছাত্রীদের বইপত্র বা দুধ দান করা",
            ],
            "hi": [
                "प्रतिदिन 'ॐ नमो भगवते वासुदेवाय' अथवा विष्णु सहस्त्रनाम का पाठ करें",
                "आक (मदार) का पौधा लगाएं और शिवजी पर आक के फूल चढ़ाएं",
                "शास्त्रीय संगीत व प्रेरणादायक व्याख्यानों को एकाग्रता से सुनें",
                "सोमवार अथवा गुरुवार को निर्धन बच्चों को पुस्तकें व दूध दान करें",
            ],
        },
        "career_fields": {
            "en": ["Higher Academia, Linguistics & Literature", "Audio Engineering, Broadcasting & Podcasting", "Diplomatic Counseling & Mediation", "Publishing, Libraries & Archival Management", "Healthcare Administration & Nursing"],
            "bn": ["উচ্চশিক্ষা, ভাষাতত্ত্ব ও সাহিত্য চর্চা", "শব্দ প্রকৌশল (Audio), রেডিও ও পডকাস্টিং", "কূটনৈতিক পরামর্শ ও মধ্যস্থতা", "পুস্তকাগার, প্রকাশনা ও মহাফেজখানা পরিচালনা", "স্বাস্থ্য প্রশাসন ও নার্সিং পরিষেবা"],
            "hi": ["विश्वविद्यालयीन शिक्षण, भाषा विज्ञान व साहित्य", "ध्वनि अभियांत्रिकी (Sound), रेडियो व पॉडकास्ट", "राजनयिक परामर्श व मध्यस्थता", "पुस्तकालय प्रबंधन, प्रकाशन व अभिलेख", "स्वास्थ्य सेवा प्रशासन व नर्सिंग"],
        },
    },
    {
        "index": 22,
        "name_en": "Dhanishta",
        "name_bn": "ধনিষ্ঠা",
        "name_hi": "धनिष्ठा",
        "lord": "Mars",
        "deity_en": "Eight Vasus (Deities of Material Wealth & Light)",
        "deity_bn": "অষ্টবসু (ধনসম্পদ, প্রকৃতি ও ঐশ্বর্যের আট দেবতা)",
        "deity_hi": "अष्ट वसु (समृद्धि व प्रकृति के आठ देव)",
        "symbol_en": "Musical Drum (Damaru) / Flute",
        "symbol_bn": "ডমরু / বাঁশি / তবলা",
        "symbol_hi": "डमरू / बांसुरी",
        "gana_en": "Rakshasa",
        "gana_bn": "রাক্ষস",
        "gana_hi": "রাক্ষস",
        "yoni_en": "Lion (Female)",
        "yoni_bn": "সিংহ (স্ত্রী)",
        "yoni_hi": "सिंह / शेरनी (स्त्री)",
        "nadi_en": "Madhya (Pitta)",
        "nadi_bn": "মধ্য (পিত্ত)",
        "nadi_hi": "मध्य (पित्त)",
        "sacred_tree_en": "Shami / Khejri (Prosopis cineraria)",
        "sacred_tree_bn": "শমী গাছ",
        "sacred_tree_hi": "शमी (खेजड़ी)",
        "beej_mantra": "ॐ ভৌমায় নমঃ / ॐ বসুভ্যো নমঃ",
        "lucky_color_en": "Silver Metallic & Bright Coral",
        "lucky_color_bn": "রুপোলি মেটালিক ও উজ্জ্বল প্রবাল",
        "lucky_color_hi": "रुपहला मेटैलिक और चटक मूंगा",
        "lucky_numbers": [9, 8],
        "lucky_gemstone_en": "Red Coral (Moonga) or Blue Sapphire",
        "lucky_gemstone_bn": "রক্তপ্রবাল অথবা নীলা",
        "lucky_gemstone_hi": "मूंगा अथवा नीलम",
        "padas": [
            {"pada": 1, "rashi_idx": 9, "navamsha": "Leo", "namakshar_en": "Ga", "namakshar_bn": "গা", "namakshar_hi": "गा"},
            {"pada": 2, "rashi_idx": 9, "navamsha": "Virgo", "namakshar_en": "Gee", "namakshar_bn": "গী", "namakshar_hi": "गी"},
            {"pada": 3, "rashi_idx": 10, "navamsha": "Libra", "namakshar_en": "Goo", "namakshar_bn": "গূ", "namakshar_hi": "गू"},
            {"pada": 4, "rashi_idx": 10, "navamsha": "Scorpio", "namakshar_en": "Ge", "namakshar_bn": "গে", "namakshar_hi": "गे"},
        ],
        "overview": {
            "en": "Dhanishta represents the celestial rhythm of wealth, universal rhythm, and divine symphony. Governed by Mars bridging Capricorn and Aquarius, natives are gifted with musical timing, prosperity, and magnetic charisma.",
            "bn": "ধনিষ্ঠা অতুল ঐশ্বর্য, ছন্দময় সঙ্গীত এবং পার্থিব সমৃদ্ধির প্রতীক। অষ্টবসুর কৃপাধন্য এই জাতকরা মঙ্গল ও শনির বলিষ্ঠ প্রভাবে অনন্য সঙ্গীতশিল্পী, দক্ষ সংগঠক, বিপুল ধনাঢ্য এবং সমাজে প্রচণ্ড প্রভাবশালী ব্যক্তিত্ব হন।",
            "hi": "धनिष्ठा नक्षत्र अतुल्य धन, संगीत की लय और तेजस्विता का प्रतीक है। अष्ट वसुओं के आशीर्वाद और मंगल के पराक्रम से जातक संगीत प्रेमी, कुशल प्रबंधक, धनवान और अत्यंत लोकप्रिय होते हैं।",
        },
        "strengths": {
            "en": [
                "Innate mastery over rhythm, timing, music, dance, and poetry",
                "Remarkable capacity to acquire immense material wealth and property",
                "High courage, enterprise, and leadership in social movements",
                "Magnificent generosity; shares abundance freely with loved ones",
            ],
            "bn": [
                "ছন্দ, সুর, সঙ্গীত, নৃত্য ও কাব্যের ওপর জন্মগত আশ্চর্য দখল",
                "বিপুল ধনসম্পদ, স্থাবর সম্পত্তি এবং প্রতিপত্তি অর্জনের মেধা",
                "সাহসিকতা, স্পষ্টবাদিতা এবং সামাজিক সংস্কারে নেতৃত্বদানের ক্ষমতা",
                "মুক্তহস্ত দানশীলতা—নিজের প্রাচুর্য প্রিয়জনদের সঙ্গে ভাগ করে নেওয়ার আনন্দ",
            ],
            "hi": [
                "संगीत, नृत्य, कविता और समय प्रबंधन की अद्भुत स्वाभाविक समझ",
                "अपार धन, अचल संपत्ति और सामाजिक प्रतिष्ठा अर्जित करने की प्रतिभा",
                "साहसी, स्वाभिमानी और किसी भी सामाजिक बदलाव का नेतृत्व करने वाले",
                "उदार हृदय—अपनी समृद्धि का लाभ समाज और मित्रों को देने वाले",
            ],
        },
        "cautions_and_pitfalls": {
            "en": [
                "Insatiable thirst for fame, status, and recognition",
                "Stubborn arguments and domestic friction due to haughty independence",
                "Tendency towards materialism overriding spiritual values",
                "Ankle sprains, circulatory disorders, heart palpitations, and bone fractures",
            ],
            "bn": [
                "যশ, খ্যাতি ও পদমর্যাদার প্রতি অতৃপ্ত লোভ",
                "উগ্র স্বাধীনচেতা মনোভাবের কারণে দাম্পত্যে মতবিরোধ ও অশান্তি",
                "পার্থিব ধনের পেছনে ছুটতে গিয়ে আত্মিক শান্তি হারিয়ে ফেলা",
                "পায়ের গোড়ালি মচকানো, রক্তসঞ্চালনে সমস্যা ও হাড়ের আঘাতের ঝুঁকি",
            ],
            "hi": [
                "नाम, यश और पद पाने की अत्यधिक तृष्णा",
                "अति-स्वतंत्र स्वभाव के कारण वैवाहिक जीवन में तालमेल की कमी",
                "भौतिक सुखों की होड़ में आत्मिक शांति को भूल जाना",
                "टखने में चोट, रक्त संचार में बाधा और हड्डियों में दर्द",
            ],
        },
        "beneficial_actions_and_remedies": {
            "en": [
                "Learn or listen to percussion instruments (Damaru, drums, tabla)",
                "Plant and tend a Shami tree; light an oil lamp under it on Saturdays",
                "Worship Lord Shiva in his Nataraja (cosmic dancer) form",
                "Donate musical instruments, warm blankets, or copper vessels on Tuesdays",
            ],
            "bn": [
                "ডমরু, ঢাক, তবলা বা বাদ্যযন্ত্র বাজানো বা শ্রবণ করা মনকে শুদ্ধ করে",
                "শমী গাছ রোপণ করা এবং শনিবার সন্ধ্যায় তার তলায় প্রদীপ জ্বালানো",
                "নটরাজরূপী দেবাদিদেব মহাদেব ও শ্রী হনুমানজির উপাসনা",
                "মঙ্গলবার দরিদ্রকে তামার পাত্র, লাল মিষ্টি বা বাদ্যযন্ত্র উপহার দেওয়া",
            ],
            "hi": [
                "डमरू, तबला अथवा वाद्य यंत्रों का अभ्यास या मधुर संगीत सुनें",
                "शमी का वृक्ष लगाएं और शनिवार को उसके नीचे तेल का दीपक जलाएं",
                "नटराज रूप में भगवान शिव की पूजा करें और हनुमान चालीसा पढ़ें",
                "मंगलवार को तांबे के बर्तन अथवा जरूरतमंदों को वस्त्र दान करें",
            ],
        },
        "career_fields": {
            "en": ["Musical Performance, Composition & Choreography", "Real Estate Development & Wealth Management", "Surgeons & Sports Medicine Specialists", "Broadcasting, Sound Engineering & Film Direction", "Strategic Military Leadership"],
            "bn": ["সঙ্গীতশিল্প, সুরকার ও নৃত্য পরিচালনা", "রিয়েল এস্টেট ডেভেলপমেন্ট ও সম্পদ ব্যবস্থাপনা", "অস্ত্রোপচার ও ক্রীড়া চিকিৎসা বিশেষজ্ঞ", "সম্প্রচার মিডিয়া, শব্দ প্রকৌশল ও চলচ্চিত্র নির্মাণ", "সামরিক কমান্ড ও সুরক্ষা নেতৃত্ব"],
            "hi": ["संगीत, नृत्य निर्देशन व कला प्रदर्शन", "रियल एस्टेट, निर्माण व धन प्रबंधन", "शल्य चिकित्सा व स्पोर्ट्स मेडिसिन", "फिल्म निर्माण, साउंड इंजीनियरिंग व टीवी मीडिया", "सैन्य कमान व रक्षा सेवाएं"],
        },
    },
    {
        "index": 23,
        "name_en": "Shatabhisha",
        "name_bn": "শতভিষা",
        "name_hi": "शतभिषा",
        "lord": "Rahu",
        "deity_en": "Varuna (Cosmic Ocean of Truth & Celestial Waters)",
        "deity_bn": "বরুণদেব (মহাজাগতিক সত্য ও মহাবিস্ময়কর জলের অধিপতি)",
        "deity_hi": "वरुण देव (महासागर व जल के अधिपति)",
        "symbol_en": "100 Physicians / Empty Circle / 100 Stars",
        "symbol_bn": "শত চিকিৎসক / শূন্য বৃত্ত / শত নক্ষত্রের মালা",
        "symbol_hi": "सौ वैद्य / रिक्त चक्र (शून्य) / सौ तारे",
        "gana_en": "Rakshasa",
        "gana_bn": "রাক্ষস",
        "gana_hi": "রাক্ষস",
        "yoni_en": "Horse (Female)",
        "yoni_bn": "অশ্ব (স্ত্রী)",
        "yoni_hi": "अश्व / घोड़ी (स्त्री)",
        "nadi_en": "Aadi (Vata)",
        "nadi_bn": "আদি (বাত)",
        "nadi_hi": "आदि (वात)",
        "sacred_tree_en": "Kadamba (Neolamarckia cadamba)",
        "sacred_tree_bn": "কদম্ব গাছ",
        "sacred_tree_hi": "कदंब",
        "beej_mantra": "ॐ রাহবে নমঃ / ॐ বরুণায় নমঃ",
        "lucky_color_en": "Electric Blue & Aquamarine",
        "lucky_color_bn": "বিদ্যুৎ নীল ও অ্যাকোয়ামেরিন",
        "lucky_color_hi": "विद्युत नीला और चमकीला आसमानी",
        "lucky_numbers": [4, 8],
        "lucky_gemstone_en": "Hessonite Garnet (Gomed) or Blue Sapphire",
        "lucky_gemstone_bn": "গোমেদ অথবা নীলা",
        "lucky_gemstone_hi": "गोमेद अथवा नीलम",
        "padas": [
            {"pada": 1, "rashi_idx": 10, "navamsha": "Sagittarius", "namakshar_en": "Go", "namakshar_bn": "গো", "namakshar_hi": "गो"},
            {"pada": 2, "rashi_idx": 10, "navamsha": "Capricorn", "namakshar_en": "Sa", "namakshar_bn": "সা", "namakshar_hi": "सा"},
            {"pada": 3, "rashi_idx": 10, "navamsha": "Aquarius", "namakshar_en": "See", "namakshar_bn": "সী", "namakshar_hi": "सी"},
            {"pada": 4, "rashi_idx": 10, "navamsha": "Pisces", "namakshar_en": "Soo", "namakshar_bn": "সূ", "namakshar_hi": "सू"},
        ],
        "overview": {
            "en": "Shatabhisha, the star of a hundred physicians, represents profound healing, hidden mysteries, and cosmic truth. Ruled by Rahu in Aquarius and presided by Varuna, natives are visionary scientists, healers, and profound thinkers.",
            "bn": "শতভিষা শত চিকিৎসকের সমান ক্ষমতাসম্পন্ন এক মহৌষধির নক্ষত্র। এটি গূঢ় রহস্যভেদ, অলৌকিক নিরাময় এবং অসীম শূন্যতার প্রতীক। কুম্ভ রাশিতে রাহুর প্রভাব এঁদের অত্যন্ত দূরদর্শী বিজ্ঞানী, ডাক্তার, দার্শনিক ও গবেষক করে তোলে।",
            "hi": "शतभिषा नक्षत्र सौ वैद्यों की अचूक उपचार शक्ति और गूढ़ रहस्यों का प्रतीक है। कुंभ राशि में राहु के प्रभाव से जातक दूरदर्शी वैज्ञानिक, कुशल चिकित्सक, दार्शनिक और असाध्य समस्याओं का समाधान खोजने वाले होते हैं।",
        },
        "strengths": {
            "en": [
                "Uncanny talent in diagnosing complex, hidden illnesses and curing ailments",
                "Visionary scientific thinking, astronomical understanding, and high intellect",
                "Uncompromising integrity in seeking ultimate truth beyond societal illusions",
                "Ability to work in solitary seclusion with deep monastic focus",
            ],
            "bn": [
                "জটিল ও দুরারোগ্য ব্যাধির কারণ নির্ণয় এবং চিকিৎসায় বিস্ময়কর সাফল্য",
                "মহাকাশ বিজ্ঞান, আধুনিক প্রযুক্তি ও মহাজাগতিক সত্য উপলব্ধির প্রখর মেধা",
                "লৌকিক ভণ্ডামির ঊর্ধ্বে গিয়ে চরম সত্য উদঘাটনে আপসহীন একাগ্রতা",
                "একাকী নিভৃতে থেকে অসাধ্য সাধন ও গভীর গবেষণায় ডুবে থাকার শক্তি",
            ],
            "hi": [
                "जटिल एवं दुर्निदान रोगों की पहचान तथा उपचार में असाधारण सफलता",
                "अंतरिक्ष विज्ञान, आधुनिक प्रौद्योगिकी एवं ब्रह्मांडीय सत्य को समझने की प्रखर मेधा",
                "सामाजिक दिखावे से ऊपर उठकर परम सत्य की खोज में अडिग निष्ठा",
                "एकांत में रहकर कठिन साधना एवं गहन शोध में डूबे रहने की शक्ति",
            ],
        },
        "cautions_and_pitfalls": {
            "en": [
                "Extreme reclusiveness, loneliness, and emotional coldness",
                "Cynical distrust of everyone leading to complete isolation",
                "Vulnerability to substance dependencies or secret obsessions",
                "Cardiovascular irregularities, calf cramps, and mysterious undiagnosable symptoms",
            ],
            "bn": [
                "অতিরিক্ত সমাজবিচ্ছিন্নতা, একাকীত্ব এবং মানুষের প্রতি শীতল মনোভাব",
                "কাউকেই বিশ্বাস না করে মনের কষ্ট গোপন রাখার প্রবণতা",
                "নেশাজাতীয় দ্রব্য বা গোপনে কোনো ক্ষতিকর অভ্যাসে আসক্ত হওয়ার ঝুঁকি",
                "রক্তচাপের অস্বাভাবিক ওঠা-নামা, পায়ের গুলিতে খিঁচুনি ও জটিল উপসর্গ",
            ],
            "hi": [
                "अत्यधिक एकांतप्रियता और समाज से पूरी तरह कट जाने की प्रवृत्ति",
                "किसी पर भी विश्वास न करना और मन की व्यथा किसी से न कहना",
                "नशे या गुप्त व्यसनों की ओर आकर्षित होने का खतरा",
                "रक्तचाप में असंतुलन, पिंडलियों में दर्द और अज्ञात रोग",
            ],
        },
        "beneficial_actions_and_remedies": {
            "en": [
                "Worship Lord Shiva; recite the Maha Mrityunjaya Mantra 108 times daily",
                "Plant and tend a sacred Kadamba tree",
                "Avoid alcohol and synthetic intoxicants completely",
                "Donate medicines, blankets, or clean drinking water on Saturdays",
            ],
            "bn": [
                "প্রতিদিন মহামৃত্যুঞ্জয় মন্ত্র ১০৮ বার জপ মানসিক ও শারীরিক সুরক্ষা দেয়",
                "কদম্ব গাছ লাগানো এবং প্রকৃতিকে সতেজ রাখা",
                "মাদক ও কৃত্রিম নেশা থেকে আজীবন দূরে থাকা",
                "শনিবার দুঃস্থ রোগীদের বিনামূল্যে ওষুধ বা বিশুদ্ধ পানীয় জল দান",
            ],
            "hi": [
                "नित्य महामृत्युंजय मंत्र की कम से कम एक माला (108 बार) जप करें",
                "कदंब का वृक्ष लगाएं और उसकी सेवा करें",
                "सभी प्रकार के नशों और अनैतिक कार्यों से पूरी तरह दूर रहें",
                "शनिवार को असहाय रोगियों को नि:शुल्क दवाइयां अथवा जल दान करें",
            ],
        },
        "career_fields": {
            "en": ["Advanced Medical Research & Pharmacology", "Space Exploration & Astronomy", "Nuclear Physics & Quantum Computing", "Alternative Holistic Medicine & Naturopathy", "Cyber Intelligence & Cryptology"],
            "bn": ["উন্নত চিকিৎসাবিজ্ঞান ও ফার্মাকোলজি", "মহাকাশ গবেষণা ও জ্যোতির্বিজ্ঞান", "কোয়ান্টাম কম্পিউটিং ও পরমাণু পদার্থবিদ্যা", "বিকল্প প্রাকৃতিক চিকিৎসা ও রেইকি", "সাইবার গোয়েন্দা ও ক্রিপ্টোগ্রাফি"],
            "hi": ["उच्च चिकित्सा अनुसंधान व औषध विज्ञान", "अंतरिक्ष विज्ञान व खगोल शास्त्र", "क्वांटम कंप्यूटिंग व नाभिकीय भौतिकी", "प्राकृतिक चिकित्सा व योग", "साइबर सुरक्षा व कूटलेखन"],
        },
    },
    {
        "index": 24,
        "name_en": "Purva Bhadrapada",
        "name_bn": "পূর্বভাদ্রপদ",
        "name_hi": "पूर्वाभाद्रपद",
        "lord": "Jupiter",
        "deity_en": "Aja Ekapada (One-Footed Cosmic Serpent of Fire)",
        "deity_bn": "অজ একপাদ (একপদে দণ্ডায়মান অগ্নিরূপী রুদ্র)",
        "deity_hi": "अज एकपाद (भगवान शिव का एकाक्ष रूप)",
        "symbol_en": "Swords / Front Legs of Funeral Cot",
        "symbol_bn": "যুগল তরবারি / শববাহী খাটের অগ্রভাগ",
        "symbol_hi": "दो तलवारें / शव शैया के आगे के पाए",
        "gana_en": "Manushya",
        "gana_bn": "মনুষ্য",
        "gana_hi": "मनुष्य",
        "yoni_en": "Lion (Male)",
        "yoni_bn": "সিংহ (পুং)",
        "yoni_hi": "सिंह / शेर (पुरुष)",
        "nadi_en": "Aadi (Vata)",
        "nadi_bn": "আদি (বাত)",
        "nadi_hi": "आदि (वात)",
        "sacred_tree_en": "Mango (Mangifera indica)",
        "sacred_tree_bn": "আমগাছ",
        "sacred_tree_hi": "आम",
        "beej_mantra": "ॐ বৃহস্পতয়ে নমঃ / ॐ অজৈকপাদে নমঃ",
        "lucky_color_en": "Deep Silver & Ochre Yellow",
        "lucky_color_bn": "রুপোলি ও গেরুয়া হলুদ",
        "lucky_color_hi": "रुपहला और गेरुआ पीला",
        "lucky_numbers": [3, 4],
        "lucky_gemstone_en": "Yellow Sapphire (Pukhraj)",
        "lucky_gemstone_bn": "হলুদ পোখরাজ",
        "lucky_gemstone_hi": "पीला पुखराज",
        "padas": [
            {"pada": 1, "rashi_idx": 10, "navamsha": "Aries", "namakshar_en": "Se", "namakshar_bn": "সে", "namakshar_hi": "से"},
            {"pada": 2, "rashi_idx": 10, "navamsha": "Taurus", "namakshar_en": "So", "namakshar_bn": "সো", "namakshar_hi": "सो"},
            {"pada": 3, "rashi_idx": 10, "navamsha": "Gemini", "namakshar_en": "Da", "namakshar_bn": "দা", "namakshar_hi": "दा"},
            {"pada": 4, "rashi_idx": 11, "navamsha": "Cancer", "namakshar_en": "Dee", "namakshar_bn": "দী", "namakshar_hi": "दी"},
        ],
        "overview": {
            "en": "Purva Bhadrapada represents fiery penance, intense transformation, and mystical elevation. Bridging Aquarius and Pisces under Jupiter, natives possess profound spiritual intensity, intellectual brilliance, and ascetic power.",
            "bn": "পূর্বভাদ্রপদ কঠোর তপস্যা, আত্মশুদ্ধি এবং আধ্যাত্মিক উত্তরণের প্রতীক। কুম্ভ ও মীনের মিলনস্থলে বৃহস্পতির এই নক্ষত্র জাতকদের ক্ষুরধার মেধা, প্রবল ইচ্ছাশক্তি, বৈরাগ্য ও উচ্চতর দার্শনিক চেতনায় সমৃদ্ধ করে।",
            "hi": "पूर्वाभाद्रपद नक्षत्र तपस्या, आत्म-रूपांतरण और आध्यात्मिक ऊर्जा का प्रतीक है। गुरु के प्रभाव से जातक अत्यंत गंभीर, दार्शनिक, त्यागशील और जटिल आध्यात्मिक रहस्यों को समझने वाले होते हैं।",
        },
        "strengths": {
            "en": [
                "Profound capacity for intense spiritual discipline, tapasya, and meditation",
                "Fearless philosophical inquiry; shatters shallow dogmas and illusions",
                "High generosity towards causes of truth and justice",
                "Powerful oratorical impact capable of inspiring radical transformation",
            ],
            "bn": [
                "কঠোর তপস্যা, আত্মনিয়ন্ত্রণ এবং গভীর ধ্যানে নিমগ্ন হওয়ার শক্তি",
                "অন্ধবিশ্বাস ও কুসংস্কার ভেঙে সত্যের পক্ষে জোরালো অবস্থানের সাহস",
                "ন্যায় ও মানবতার পক্ষে সর্বস্ব পণ করে পাশে দাঁড়ানোর উদারতা",
                "উত্তেজক ও বিপ্লবী বক্তৃতা দিয়ে জনমানসে গভীর রূপান্তর আনার ক্ষমতা",
            ],
            "hi": [
                "कठोर आत्मसंयम, ध्यान और साधना करने की अद्भुत शक्ति",
                "रूढ़ियों को तोड़कर सत्य की निर्भीक खोज करने का साहस",
                "न्याय और मानवता के कल्याण हेतु सर्वस्व न्योछावर करने का भाव",
                "प्रभावशाली वाणी जिससे लोगों की सोच में क्रांतिकारी बदलाव आ जाए",
            ],
        },
        "cautions_and_pitfalls": {
            "en": [
                "Extreme emotional swings; oscillating between asceticism and passionate rage",
                "Dark, morbid fascinations or pessimistic anxieties about doom",
                "Harsh intolerance towards human weaknesses and mundane compromises",
                "Ankles, sole of feet inflammation, and liver/digestive toxicity",
            ],
            "bn": [
                "আবেগের চরম ওঠানামা—কখনও পরম বৈরাগী, আবার কখনও প্রচণ্ড রুদ্রমূর্তি",
                "মনমরা থাকা বা ভবিষ্যতের ধ্বংসচিন্তায় অহেতুক আতঙ্কিত হওয়া",
                "সাধারণ মানুষের দুর্বলতা সহ্য করতে না পেরে অতিরিক্ত কঠোর আচরণ",
                "পায়ের গোড়ালি ও পাতার ব্যথা, লিভারের সমস্যা ও পেটের গোলযোগ",
            ],
            "hi": [
                "अतिवादी स्वभाव—अत्यधिक वैराग्य अथवा भयंकर क्रोध के बीच झूलना",
                "नकारात्मक विचारों या अनहोनी की आशंका में खुद को परेशान करना",
                "दूसरों की सामान्य गलतियों के प्रति अत्यधिक असहिष्णु हो जाना",
                "टखनों व पैरों के तलवों में दर्द, लीवर संबंधी विकार",
            ],
        },
        "beneficial_actions_and_remedies": {
            "en": [
                "Worship Lord Shiva in his Rudra form; chant Rudra Gayatri Mantra",
                "Plant and tend a sacred Mango tree; distribute sweet mangoes",
                "Practice forgiveness and gentle empathy toward ordinary mortals",
                "Donate yellow pulses, saffron, or brass utensils on Thursdays",
            ],
            "bn": [
                "রুদ্ররূপী দেবাদিদেব মহাদেবের উপাসনা এবং রুদ্র গায়ত্রী জপ",
                "আমগাছ রোপণ করা এবং গ্রীষ্মকালে মধুর ফল বিতরণ করা",
                "সকল মানুষের প্রতি ক্ষমা ও মমতার কোমল দৃষ্টি অনুশীলন করা",
                "বৃহস্পতিবারে হলুদ ডাল, জাফরান বা ধর্মগ্রন্থ দান করা",
            ],
            "hi": [
                "भगवान शिव के रुद्र रूप की पूजा करें और रुद्र गायत्री का पाठ करें",
                "आम का वृक्ष लगाएं और उसकी देखभाल करें",
                "दूसरों के प्रति क्षमा और करुणा का भाव विकसित करें",
                "गुरुवार को चने की दाल, केसर अथवा धार्मिक पुस्तकें दान करें",
            ],
        },
        "career_fields": {
            "en": ["Astrophysics & Cosmology", "Occult Mysticism & Tantric Philosophy", "Psychiatric Rehabilitation & Addiction Recovery", "Cinematic Screenwriting & Dramatic Arts", "Humanitarian Reform & Disaster Relief"],
            "bn": ["জ্যোতিঃপদার্থবিজ্ঞান ও সৃষ্টিতত্ত্ব", "গুপ্তবিদ্যা ও তান্ত্রিক দর্শন", "মনোচিকিৎসা ও মাদকাসক্তি নিরাময় কেন্দ্র", "চলচ্চিত্র চিত্রনাট্য ও গম্ভীর নাট্যকলা", "মানবাধিকার ও দুর্যোগ ত্রাণ ব্যবস্থাপনা"],
            "hi": ["खगोल भौतिकी व ब्रह्मांड विज्ञान", "रहस्यमय विद्याएं व तंत्र दर्शन", "मानसिक पुनर्वास व नशामुक्ति केंद्र", "सिनेमाई पटकथा लेखन व गंभीर नाट्य कला", "मानवीय राहत कार्य व आपदा प्रबंधन"],
        },
    },
    {
        "index": 25,
        "name_en": "Uttara Bhadrapada",
        "name_bn": "উত্তরভাদ্রপদ",
        "name_hi": "उत्तराभाद्रपद",
        "lord": "Saturn",
        "deity_en": "Ahirbudhnya (Cosmic Serpent of the Oceanic Depths)",
        "deity_bn": "অহিরবুধ্ন্যা (পাতাল ও সমুদ্রগর্ভের পবিত্র শেষনাগ)",
        "deity_hi": "अहिर्बुध्न्य (समुद्र की गहराइयों के नाग देव)",
        "symbol_en": "Back Legs of Funeral Cot / Snake in Water",
        "symbol_bn": "শববাহী খাটের পশ্চাদ্ভাগ / জলে নিমগ্ন সর্প",
        "symbol_hi": "शव शैया के पीछे के पाए / जल में सर्प",
        "gana_en": "Manushya",
        "gana_bn": "মনুষ্য",
        "gana_hi": "मनुष्य",
        "yoni_en": "Cow (Female)",
        "yoni_bn": "গো / গাভী (স্ত্রী)",
        "yoni_hi": "गाय / गौमाता (स्त्री)",
        "nadi_en": "Madhya (Pitta)",
        "nadi_bn": "মধ্য (পিত্ত)",
        "nadi_hi": "मध्य (पित्त)",
        "sacred_tree_en": "Neem (Azadirachta indica)",
        "sacred_tree_bn": "নিমগাছ",
        "sacred_tree_hi": "नीम",
        "beej_mantra": "ॐ শনৈশ্চরায় নমঃ / ॐ অহির্বুধ্ন্যায় নমঃ",
        "lucky_color_en": "Deep Indigo & Forest Green",
        "lucky_color_bn": "গাঢ় নীল ও অরণ্য সবুজ",
        "lucky_color_hi": "गहरा नीला और वन हरा",
        "lucky_numbers": [8, 3],
        "lucky_gemstone_en": "Blue Sapphire (Neelam) or Yellow Sapphire",
        "lucky_gemstone_bn": "নীলা অথবা পোখরাজ",
        "lucky_gemstone_hi": "नीलम अथवा पुखराज",
        "padas": [
            {"pada": 1, "rashi_idx": 11, "navamsha": "Leo", "namakshar_en": "Du", "namakshar_bn": "দু", "namakshar_hi": "दु"},
            {"pada": 2, "rashi_idx": 11, "navamsha": "Virgo", "namakshar_en": "Tha", "namakshar_bn": "থ", "namakshar_hi": "थ"},
            {"pada": 3, "rashi_idx": 11, "navamsha": "Libra", "namakshar_en": "Jha", "namakshar_bn": "ঝ", "namakshar_hi": "झ"},
            {"pada": 4, "rashi_idx": 11, "navamsha": "Scorpio", "namakshar_en": "Na", "namakshar_bn": "ঞ", "namakshar_hi": "ञ"},
        ],
        "overview": {
            "en": "Uttara Bhadrapada represents the profound, tranquil wisdom of the ocean depths, Kundalini stability, and noble benevolence. Governed by Saturn in oceanic Pisces, natives are serene, charitable, spiritually enlightened, and deeply composed.",
            "bn": "উত্তরভাদ্রপদ সমুদ্রের অগাধ গভীরতার মতো শান্ত, স্থির প্রজ্ঞা ও কুন্ডলিনী শক্তির প্রতীক। মীন রাশিতে শনির সুষম প্রভাবে এই জাতকরা অত্যন্ত গম্ভীর, পরোপকারী, নির্লোভ, আত্মসংযমী এবং আধ্যাত্মিক উপলব্ধিতে সমুজ্জ্বল হন।",
            "hi": "उत्तराभाद्रपद नक्षत्र समुद्र की अतल गहराइयों जैसी शांति, कुण्डलिनी शक्ति और आत्मज्ञान का प्रतीक है। शनि के प्रभाव से जातक अत्यंत शांत, परोपकारी, धैर्यवान और दूसरों के कल्याण हेतु समर्पित होते हैं।",
        },
        "strengths": {
            "en": [
                "Immense emotional serenity and composed stability under chaotic crises",
                "Unconditional benevolence, charity, and protective shelter for the suffering",
                "Profound spiritual illumination and natural mastery over Kundalini energy",
                "Exceptional capacity for sustained meditation, scholarship, and writing",
            ],
            "bn": [
                "ভীষণ দুর্যোগ ও সংকটের মুখেও প্রশান্ত ও অচঞ্চল চিত্তে স্থির থাকা",
                "আর্ত ও পীড়িত মানুষকে নিঃশর্ত আশ্রয় ও খাদ্য দান করার মাতৃসুলভ মহত্ত্ব",
                "কুন্ডলিনী যোগ, ধ্যান ও আত্মজ্ঞানের গভীর আধ্যাত্মিক প্রকাশ",
                "দীর্ঘ সময় ধরে নিবিড় গবেষণা, গ্রন্থরচনা ও জ্ঞান সাধনায় লিপ্ত থাকার মেধা",
            ],
            "hi": [
                "भारी संकट में भी मन को अत्यंत शांत और संतुलित रखने की क्षमता",
                "दुखियों और असहायों को निस्वार्थ भाव से शरण और सहायता देना",
                "गहरा आत्मज्ञान, कुण्डलिनी योग और ध्यान में स्वाभाविक प्रवीणता",
                "गंभीर लेखन, शोध और ज्ञानार्जन के लिए दीर्घकालिक समर्पण",
            ],
        },
        "cautions_and_pitfalls": {
            "en": [
                "Excessive withdrawal from mundane world, neglecting earthly career duties",
                "Risk of melancholy, apathy, and carrying an overburdened heart",
                "Stubborn passivity when assertive action is immediately required",
                "Cold feet, lymphatic sluggishness, and foot bone/rheumatism sensitivities",
            ],
            "bn": [
                "সংসার ও পার্থিব কাজের প্রতি অতিরিক্ত বৈরাগ্য বা উদাসীনতা",
                "মনের মাঝে বিষণ্ণতা পুষে রাখা এবং কাজে উদ্যমের অভাব",
                "যেখানে দ্রুত সিদ্ধান্ত ও পদক্ষেপ প্রয়োজন, সেখানে অতিরিক্ত ঢিলেমি",
                "পায়ের পাতায় ফোলা ভাব, ঠাণ্ডা লাগা ও বাতজনিত দুর্বলতা",
            ],
            "hi": [
                "सांसारिक जिम्मेदारियों से विमुख होकर अत्यधिक वैरागी बन जाना",
                "मन में उदासी और अकेलेपन की भावना को अत्यधिक बढ़ावा देना",
                "तत्काल निर्णय लेने के समय अत्यधिक सुस्ती और विलंब करना",
                "पैरों में सूजन, गठिया, ठंड लगना और कफ का प्रकोप",
            ],
        },
        "beneficial_actions_and_remedies": {
            "en": [
                "Plant and tend a sacred Neem tree; honor its cleansing medicine",
                "Worship Lord Shiva and chant 'Om Namah Shivaya' with deep calm",
                "Offer pure water and food to destitute elders and saints",
                "Donate warm black blankets, mustard oil, or sesame to laborers on Saturdays",
            ],
            "bn": [
                "নিমগাছ রোপণ ও পরিচর্যা করা—এর ভেষজ গুণাবলি প্রকৃতির আশীর্বাদ",
                "প্রতিদিন শান্ত মনে 'ॐ নমঃ শিবায়' মন্ত্র জপ",
                "বৃদ্ধাশ্রমে সেবা এবং অসহায় সাধু-সন্ন্যাসীদের অন্নদান",
                "শনিবার মেহনতী ও দুঃস্থ মানুষকে কম্বল, সরিষার তেল বা কালো তিল দান",
            ],
            "hi": [
                "नीम का वृक्ष लगाएं और उसके औषधीय गुणों का सम्मान करें",
                "शांत भाव से 'ॐ नमः शिवाय' का नित्य 108 बार जप करें",
                "वृद्ध आश्रमों में सेवा करें और संतों को आदरपूर्वक भोजन कराएं",
                "शनिवार को जरूरतमंद श्रमिकों को कंबल अथवा सरसों का तेल दान करें",
            ],
        },
        "career_fields": {
            "en": ["Spiritual Monasticism & Yoga Philosophy", "Marine Biology & Oceanographic Preservation", "Psychotherapy & Hospice Caregiving", "Charitable Foundations & Social Justice", "High Judiciary & Ethical Governance"],
            "bn": ["যোগ দর্শন, সন্ন্যাস ও আধ্যাত্মিক পথপ্রদর্শন", "সমুদ্র জীববিদ্যা ও পরিবেশ সংরক্ষণ", "মনোচিকিৎসা ও অন্তিমকালীয় সেবা (হস্পিস কেয়ার)", "দাতব্য সংস্থা ও জনস্বার্থ রক্ষা", "উচ্চ বিচারবিভাগ ও নীতি প্রশাসন"],
            "hi": ["योग दर्शन, संन्यास व आध्यात्मिक मार्गदर्शन", "समुद्री जीव विज्ञान व पर्यावरण संरक्षण", "हॉस्पिस केयर व मानसिक सांत्वना सेवा", "धर्मार्थ न्यास व सामाजिक न्याय", "न्यायिक सेवाएं व उच्च प्रशासनिक पद"],
        },
    },
    {
        "index": 26,
        "name_en": "Revati",
        "name_bn": "রেবতী",
        "name_hi": "रेवती",
        "lord": "Mercury",
        "deity_en": "Pushan (The Nurturing Shepherd & Guardian of Safe Journeys)",
        "deity_bn": "পূষা (পথপ্রদর্শক, নিরাপদ যাত্রার অভিভাবক ও পশুপালক দেবতা)",
        "deity_hi": "पूषा देव (सुरक्षित यात्रा व पोषण के देवता)",
        "symbol_en": "Pair of Fish / Drum",
        "symbol_bn": "মীন যুগল (দুটি মাছ) / মৃদঙ্গ",
        "symbol_hi": "मछलियों का जोड़ा / मृदंग",
        "gana_en": "Deva",
        "gana_bn": "দেব",
        "gana_hi": "দেব",
        "yoni_en": "Elephant (Female)",
        "yoni_bn": "হস্তী / হাতি (স্ত্রী)",
        "yoni_hi": "हथिनी / गज (स्त्री)",
        "nadi_en": "Antya (Kapha)",
        "nadi_bn": "অন্ত্য (কফ)",
        "nadi_hi": "अंत्य (कफ)",
        "sacred_tree_en": "Mahua / Indian Butter Tree (Madhuca longifolia)",
        "sacred_tree_bn": "মহুয়া গাছ",
        "sacred_tree_hi": "महुआ",
        "beej_mantra": "ॐ বুধায় নমঃ / ॐ পূষ্ণে নমঃ",
        "lucky_color_en": "Golden Emerald & Sea Foam Green",
        "lucky_color_bn": "সোনালী পান্না ও সমুদ্রফেনা সবুজ",
        "lucky_color_hi": "स्वर्णिम पन्ना हरा और सी-ग्रीन",
        "lucky_numbers": [5, 3],
        "lucky_gemstone_en": "Emerald (Panna) or Yellow Sapphire",
        "lucky_gemstone_bn": "পান্না অথবা পোখরাজ",
        "lucky_gemstone_hi": "पन्ना अथवा पुखराज",
        "padas": [
            {"pada": 1, "rashi_idx": 11, "navamsha": "Sagittarius", "namakshar_en": "De", "namakshar_bn": "দে", "namakshar_hi": "दे"},
            {"pada": 2, "rashi_idx": 11, "navamsha": "Capricorn", "namakshar_en": "Do", "namakshar_bn": "দো", "namakshar_hi": "दो"},
            {"pada": 3, "rashi_idx": 11, "navamsha": "Aquarius", "namakshar_en": "Cha", "namakshar_bn": "চা", "namakshar_hi": "चा"},
            {"pada": 4, "rashi_idx": 11, "navamsha": "Pisces", "namakshar_en": "Chee", "namakshar_bn": "চী", "namakshar_hi": "ची"},
        ],
        "overview": {
            "en": "Revati, the final constellation of the zodiac, signifies completion, spiritual liberation (Moksha), and the safe return of the traveler. Ruled by Mercury in Jupiter's sign Pisces, natives are deeply compassionate, imaginative, and pure-hearted.",
            "bn": "রাশিচক্রের অন্তিম নক্ষত্র রেবতী মোক্ষ, পূর্ণতা এবং পথিককে নিরাপদ আশ্রয়ে পৌঁছে দেওয়ার প্রতীক। দেবগুরু বৃহস্পতির রাশিতে বুধের প্রভাবে এই জাতকরা অত্যন্ত দয়াবান, কল্পনাপ্রবণ, মধুরভাষী, সঙ্গীতপ্রেমী এবং পশুপ্রেমিক হন।",
            "hi": "रेवती राशि चक्र का अंतिम नक्षत्र है, जो मोक्ष, पूर्णता और यात्रा की सुखद समाप्ति का प्रतीक है। मीन राशि में बुध के प्रभाव से जातक अत्यंत दयालु, परोपकारी, कलाप्रेमी, मधुरभाषी और संवेदनशील होते हैं।",
        },
        "strengths": {
            "en": [
                "Boundless empathy and gentle protective devotion towards all living beings",
                "Charming, sweet eloquence and natural diplomatic artistry",
                "Exquisite creative imagination, musical resonance, and visionary poetry",
                "Innate spiritual innocence and blessing of safe travel and safe guidance",
            ],
            "bn": [
                "সকল জীবের প্রতি অসীম মমতা ও পরম স্নেহে ভরিয়ে দেওয়ার মনোভাব",
                "মধুর ও অমায়িক বাক্যালাপ যা শত্রুকেও বন্ধুতে পরিণত করে",
                "অসাধারণ সৃজনশীল কল্পনাশক্তি, সঙ্গীত ও কাব্যপ্রীতি",
                "নিরাপদ পথের সন্ধান দেওয়া ও ভ্রমণের সময় ঈশ্বরীয় সুরক্ষাবলয় লাভ",
            ],
            "hi": [
                "समस्त प्राणियों के प्रति असीम दया, करुणा और सेवाभाव",
                "अत्यंत मधुर और सम्मोहक वाणी जो विरोधियों को भी मित्र बना ले",
                "सृजनात्मक कल्पना, संगीत, कला व काव्य में अद्वितीय प्रतिभा",
                "दूसरों का सही मार्गदर्शन करना और ईश्वर की कृपा से सुरक्षित रहना",
            ],
        },
        "cautions_and_pitfalls": {
            "en": [
                "Over-gullibility and taking on other people's burdens until exhausted",
                "Escapism from harsh worldly responsibilities through daydreaming",
                "Lack of practical financial boundaries leading to being exploited",
                "Foot sensitivities, immune system weakness, and toxic fluid buildup",
            ],
            "bn": [
                "অতিরিক্ত সরলতার কারণে প্রতারিত হওয়া এবং অন্যের দুঃখ নিজের কাঁধে নিয়ে ভেঙে পড়া",
                "বাস্তব জীবনের কঠিন দায়িত্ব থেকে দিবাস্বপ্নে পালিয়ে বাঁচার প্রবণতা",
                "অর্থের ব্যাপারে হিসেবহীন হয়ে ঋণগ্রস্ত হওয়া বা ঠকে যাওয়া",
                "পায়ের পাতার সমস্যা, দুর্বল রোগপ্রতিরোধ ক্ষমতা ও ঠাণ্ডা লাগার ধাত",
            ],
            "hi": [
                "अत्यधिक भोलापन जिसके कारण लोग अनुचित लाभ उठा लेते हैं",
                "कठिन यथार्थ से मुंह मोड़कर खयाली पुलाव पकाने की आदत",
                "धन के मामलों में सीमा न रखना और आर्थिक नुकसान उठाना",
                "पैरों में दर्द, रोग प्रतिरोधक क्षमता में कमी और सर्दी-जुकाम",
            ],
        },
        "beneficial_actions_and_remedies": {
            "en": [
                "Feed fish in rivers or lakes with flour balls; protect aquatic life",
                "Plant and tend a Mahua tree; protect green pastures",
                "Worship Lord Vishnu and Goddess Radha on Wednesdays",
                "Donate green items, fruits, or stationeries to orphan children on Wednesdays",
            ],
            "bn": [
                "নদী বা পুকুরে মাছকে নিয়মিত আটার গুলি খাওয়ানো পরম শুভ",
                "মহুয়া গাছ রোপণ করা ও জীবজন্তুর সেবা করা",
                "বুধবার ভগবান শ্রীকৃষ্ণ ও রাধারাণীর চরণে ফুল ও তুলসী নিবেদন",
                "বুধবার অনাথ শিশুদের ফলমূল, মিষ্টি বা খাতা-কলম দান করা",
            ],
            "hi": [
                "तालाब या नदी में मछलियों को आटे की गोलियां खिलाएं",
                "महुआ का वृक्ष लगाएं और मूक पशुओं की सेवा करें",
                "बुधवार को भगवान श्री कृष्ण और राधा रानी की पूजा करें",
                "बुधवार को अनाथ बच्चों को फल, मिठाई अथवा अध्ययन सामग्री दान करें",
            ],
        },
        "career_fields": {
            "en": ["Veterinary Medicine & Animal Welfare", "Music, Creative Writing & Poetic Arts", "Travel, Tourism & Pilgrimage Logistics", "Philanthropic Foundations & Foster Care", "International Diplomacy & Peacekeeping"],
            "bn": ["পশুচিকিৎসা ও বন্যপ্রাণী সংরক্ষণ", "সঙ্গীতশিল্প, সৃজনশীল সাহিত্য ও কবিতা", "ভ্রমণ, পর্যটন ও তীর্থযাত্রা আয়োজন", "দাতব্য অনাথ আশ্রম ও সমাজকল্যাণ", "আন্তর্জাতিক শান্তি রক্ষা ও কূটনীতি"],
            "hi": ["पशु चिकित्सा व जीव रक्षा अभियान", "संगीत, काव्य रचना व ललित कलाएं", "पर्यटन, यात्रा प्रबंधन व तीर्थाटन", "अनाथालय, बाल कल्याण व समाज सेवा", "अंतरराष्ट्रीय शांति दूत व कूटनीति"],
        },
    },
]


# =============================================================================
# Tarabala (9 Taras Classification)
# =============================================================================

TARABALA_DEFINITIONS = [
    {
        "tara_index": 1,
        "name_en": "Janma Tara",
        "name_bn": "জন্ম তারা",
        "name_hi": "जन्म तारा",
        "is_auspicious": False,
        "significance_en": "Birth Star. Symbolizes personal physical body and self. Starting major new high-risk ventures or medical operations on this tara is avoided in classical Muhurta.",
        "significance_bn": "শারীরিক সত্ত্বা ও আত্মস্বরূপ। অত্যন্ত সংবেদনশীল হওয়ায় এই তারায় নতুন ঝুঁকিপূর্ণ কাজ বা অস্ত্রোপচার শাস্ত্রীয়ভাবে বর্জনীয়।",
        "significance_hi": "शरीर और स्वास्थ्य का सूचक। इस तारे में नई जोखिम भरी यात्रा अथवा शल्य चिकित्सा से बचना चाहिए।",
    },
    {
        "tara_index": 2,
        "name_en": "Sampat Tara",
        "name_bn": "সম্পদ তারা",
        "name_hi": "सम्पत् तारा",
        "is_auspicious": True,
        "significance_en": "Wealth & Prosperity. Highly auspicious for commerce, investments, trade agreements, and material prosperity.",
        "significance_bn": "ধনসম্পদ ও সমৃদ্ধি। নতুন ব্যবসা শুরু, বিনিয়োগ, জমি কেনাবেচা ও আর্থিক উন্নতির জন্য অত্যন্ত শুভ।",
        "significance_hi": "धन और ऐश्वर्य देने वाला। व्यापार आरंभ, निवेश और संपत्ति खरीदने के लिए अत्यंत श्रेष्ठ।",
    },
    {
        "tara_index": 3,
        "name_en": "Vipat Tara",
        "name_bn": "বিপদ তারা",
        "name_hi": "विपद् तारा",
        "is_auspicious": False,
        "significance_en": "Hazards & Obstacles. Prone to losses, misunderstandings, and impediments. Avoid signing contracts on these days.",
        "significance_bn": "বাধা ও বিপত্তি। এই তারায় নতুন চুক্তি স্বাক্ষর বা ভ্রমণ পরিহার করা শ্রেয়।",
        "significance_hi": "कष्ट और बाधाओं का सूचक। महत्वपूर्ण समझौतों और यात्राओं से इस दिन बचना चाहिए।",
    },
    {
        "tara_index": 4,
        "name_en": "Kshema Tara",
        "name_bn": "ক্ষেম তারা",
        "name_hi": "क्षेम तारा",
        "is_auspicious": True,
        "significance_en": "Well-Being & Safety. Blesses protection, recovery from ailments, peace of mind, and family harmony.",
        "significance_bn": "মঙ্গল ও নিরাপত্তা। শান্তি, রোগমুক্তি, পরিবারের কল্যাণ এবং শুভকাজের জন্য অতীব প্রশস্ত।",
        "significance_hi": "कल्याण और सुरक्षा। मानसिक शांति, रोगमुक्ति और पारिवारिक मांगलिक कार्यों के लिए उत्तम।",
    },
    {
        "tara_index": 5,
        "name_en": "Pratyak Tara",
        "name_bn": "প্রত্যক তারা",
        "name_hi": "प्रत्यक् तारा",
        "is_auspicious": False,
        "significance_en": "Obstacles & Enmity. Can trigger unexpected opposition, disagreements, and delays. Maintain silence and patience.",
        "significance_bn": "প্রতিবন্ধকতা ও শত্রুতা। অপ্রত্যাশিত বাধা ও বিরোধ তৈরি হতে পারে; ধৈর্য ও সংযম আবশ্যক।",
        "significance_hi": "विरोध और असफलता। कार्यों में रुकावटें आ सकती हैं, धैर्य से काम लें।",
    },
    {
        "tara_index": 6,
        "name_en": "Sadhana Tara",
        "name_bn": "সাধনা তারা",
        "name_hi": "साधना तारा",
        "is_auspicious": True,
        "significance_en": "Accomplishment & Success. Ideal for educational exams, research milestones, spiritual initiation, and creative production.",
        "significance_bn": "লক্ষ্যসিদ্ধি ও সাফল্য। পরীক্ষা, গবেষণা, মন্ত্রদীক্ষা এবং কঠিন কাজ সম্পূর্ণ করার জন্য পরম শুভ।",
        "significance_hi": "सिद्धि और सफलता। कठिन कार्यों की पूर्ति, शिक्षा, शोध और साधना के लिए सर्वोत्तम।",
    },
    {
        "tara_index": 7,
        "name_en": "Naidhana / Vadha Tara",
        "name_bn": "নিধন / বধ তারা",
        "name_hi": "निधन तारा",
        "is_auspicious": False,
        "significance_en": "Destruction & Acute Crisis. Highly inauspicious. Strictly avoid aggressive gambles, conflicts, and dangerous travel.",
        "significance_bn": "সংকট ও বিনাশ। অত্যন্ত সতর্ক থাকতে হবে; যে কোনো ঝুঁকিপূর্ণ পদক্ষেপ বা ঝগড়াবিবাদ বর্জনীয়।",
        "significance_hi": "गंभीर संकट का सूचक। कोई भी नया जोखिम भरा कदम न उठाएं, शांत रहें।",
    },
    {
        "tara_index": 8,
        "name_en": "Mitra Tara",
        "name_bn": "মিত্র তারা",
        "name_hi": "मित्र तारा",
        "is_auspicious": True,
        "significance_en": "Friendship & Alliance. Brings joy, social support, fruitful collaborations, and harmonious relationships.",
        "significance_bn": "বন্ধুত্ব ও সৌহার্দ্য। আনন্দ, শুভ যোগাযোগ, নতুন বন্ধুত্ব ও যৌথ উদ্যোগের জন্য দারুণ ফলদায়ক।",
        "significance_hi": "मित्रता और सहयोग। नए मित्रों से लाभ, साझेदारी और सामाजिक उत्सवों के लिए शुभ।",
    },
    {
        "tara_index": 9,
        "name_en": "Param Mitra Tara",
        "name_bn": "পরম মিত্র তারা",
        "name_hi": "परम मित्र तारा",
        "is_auspicious": True,
        "significance_en": "Supreme Ally & Fulfillment. Grants profound joy, mentorship, highest profits, and fulfillment of deep aspirations.",
        "significance_bn": "পরম মিত্র ও সৌভাগ্য। গভীর আনন্দ, গুরুকৃপা, সর্বোচ্চ লাভ ও মনোবাসনা পূর্ণকারী।",
        "significance_hi": "परम सौभाग्य और मित्र। बड़े लाभ, मनोकामना पूर्ति और दिव्य मार्गदर्शन देने वाला तारा।",
    },
]


def calculate_tarabala_table(birth_nakshatra_idx: int) -> list[dict[str, Any]]:
    """Calculates the 9-Tara Tarabala mapping across all 27 nakshatras from the birth nakshatra."""
    # 9 groups, each containing 3 Nakshatras
    groups: dict[int, list[str]] = {i: [] for i in range(1, 10)}

    for m in range(27):
        # 1-indexed count from birth nakshatra
        count = ((m - birth_nakshatra_idx) % 27) + 1
        tara_idx = ((count - 1) % 9) + 1
        groups[tara_idx].append(NAKSHATRAS_MASTER[m]["name_en"])

    result: list[dict[str, Any]] = []
    for defn in TARABALA_DEFINITIONS:
        t_idx = defn["tara_index"]
        result.append(
            {
                "tara_index": t_idx,
                "tara_name": defn["name_en"],
                "tara_name_bn": defn["name_bn"],
                "tara_name_hi": defn["name_hi"],
                "is_auspicious": defn["is_auspicious"],
                "significance": defn["significance_en"],
                "significance_bn": defn["significance_bn"],
                "significance_hi": defn["significance_hi"],
                "nakshatras": groups[t_idx],
            }
        )
    return result


# =============================================================================
# Canonical Avakahada Classifications from Moon Sign (Rashi)
# =============================================================================

RASHI_VARNA = [
    {"en": "Kshatriya (Warrior/Leader)", "bn": "ক্ষত্রিয়", "hi": "क्षत्रिय"},  # Aries
    {"en": "Vaishya (Merchant/Creator)", "bn": "বৈশ্য", "hi": "वैश्य"},  # Taurus
    {"en": "Shudra (Artisan/Worker)", "bn": "শূদ্র", "hi": "शूद्र"},  # Gemini
    {"en": "Brahmin (Priest/Scholar)", "bn": "ব্রাহ্মণ", "hi": "ब्राह्मण"},  # Cancer
    {"en": "Kshatriya (Warrior/Leader)", "bn": "ক্ষত্রিয়", "hi": "क्षत्रिय"},  # Leo
    {"en": "Vaishya (Merchant/Creator)", "bn": "বৈশ্য", "hi": "वैश्य"},  # Virgo
    {"en": "Shudra (Artisan/Worker)", "bn": "শূদ্র", "hi": "शूद्र"},  # Libra
    {"en": "Brahmin (Priest/Scholar)", "bn": "ব্রাহ্মণ", "hi": "ब्राह्मण"},  # Scorpio
    {"en": "Kshatriya (Warrior/Leader)", "bn": "ক্ষত্রিয়", "hi": "क्षत्रिय"},  # Sagittarius
    {"en": "Vaishya (Merchant/Creator)", "bn": "বৈশ্য", "hi": "वैश्य"},  # Capricorn
    {"en": "Shudra (Artisan/Worker)", "bn": "শূদ্র", "hi": "शूद्र"},  # Aquarius
    {"en": "Brahmin (Priest/Scholar)", "bn": "ব্রাহ্মণ", "hi": "ब्राह्मण"},  # Pisces
]

RASHI_TATVA = [
    {"en": "Agni (Fire)", "bn": "অগ্নি (তেজ)", "hi": "अग्नि"},  # Aries
    {"en": "Prithvi (Earth)", "bn": "মৃত্তিকা (পৃথিবী)", "hi": "पृथ्वी"},  # Taurus
    {"en": "Vayu (Air)", "bn": "বায়ু", "hi": "वायु"},  # Gemini
    {"en": "Jala (Water)", "bn": "জল", "hi": "जल"},  # Cancer
    {"en": "Agni (Fire)", "bn": "অগ্নি (তেজ)", "hi": "अग्नि"},  # Leo
    {"en": "Prithvi (Earth)", "bn": "মৃত্তিকা (পৃথিবী)", "hi": "पृथ्वी"},  # Virgo
    {"en": "Vayu (Air)", "bn": "বায়ু", "hi": "वायु"},  # Libra
    {"en": "Jala (Water)", "bn": "জল", "hi": "जल"},  # Scorpio
    {"en": "Agni (Fire)", "bn": "অগ্নি (তেজ)", "hi": "अग्नि"},  # Sagittarius
    {"en": "Prithvi (Earth)", "bn": "মৃত্তিকা (পৃথিবী)", "hi": "पृथ्वी"},  # Capricorn
    {"en": "Vayu (Air)", "bn": "বায়ু", "hi": "वायु"},  # Aquarius
    {"en": "Jala (Water)", "bn": "জল", "hi": "जल"},  # Pisces
]

RASHI_VASHYA = [
    {"en": "Chatuspada (Quadruped)", "bn": "চতুষ্পদ", "hi": "चतुष्पद"},  # Aries
    {"en": "Chatuspada (Quadruped)", "bn": "চতুষ্পদ", "hi": "चतुष्पद"},  # Taurus
    {"en": "Dwipada / Manava (Human)", "bn": "দ্বিপদ / মানব", "hi": "द्विपद / मानव"},  # Gemini
    {"en": "Jalachara (Water Dweller)", "bn": "জলচর", "hi": "जलचर"},  # Cancer
    {"en": "Vanachara / Simha (Forest Beast)", "bn": "বনচর / সিংহ", "hi": "वनचर / सिंह"},  # Leo
    {"en": "Dwipada / Manava (Human)", "bn": "দ্বিপদ / মানব", "hi": "द्विपद / मानव"},  # Virgo
    {"en": "Dwipada / Manava (Human)", "bn": "দ্বিপদ / মানব", "hi": "द्विपद / मानव"},  # Libra
    {"en": "Keeta (Insect / Scorpion)", "bn": "কীট", "hi": "कीट"},  # Scorpio
    {"en": "Dwipada & Chatuspada", "bn": "মানব ও চতুষ্পদ", "hi": "द्विपद व चतुष्पद"},  # Sagittarius
    {"en": "Jalachara & Chatuspada", "bn": "জলচর ও চতুষ্পদ", "hi": "जलचर व चतुष्पद"},  # Capricorn
    {"en": "Dwipada / Manava (Human)", "bn": "দ্বিপদ / মানব", "hi": "द्विपद / मानव"},  # Aquarius
    {"en": "Jalachara (Water Dweller)", "bn": "জলচর", "hi": "जलचर"},  # Pisces
]


def calculate_paya(moon_house_from_lagna: int) -> dict[str, str]:
    """Calculates Paya (Moon's foot of arrival) based on the House of Moon from Lagna (1 to 12).
    - Houses 1, 6, 11: Gold (Sona / স্বর্ণ) - High energy, tests character
    - Houses 2, 5, 9: Silver (Rupa / রৌপ্য) - Most auspicious, supreme comfort & fortune
    - Houses 3, 7, 10: Copper (Tamba / তাম্র) - Courageous, hard-working, victory
    - Houses 4, 8, 12: Iron (Loha / লৌহ) - Karmic endurance, discipline, trials
    """
    if moon_house_from_lagna in (1, 6, 11):
        return {
            "en": "Gold (Suvarna Paya) - Spiritually profound, tests humility and tests character before success",
            "bn": "স্বর্ণ পায়া (Gold) - আধ্যাত্মিক উত্তরণ, তবে অহংকার দমন ও কঠিন পরীক্ষার পর প্রতিষ্ঠা",
            "hi": "स्वर्ण पाया (Gold) - आध्यात्मिक उन्नति, अहंकार त्यागने पर बड़ी सफलता",
        }
    elif moon_house_from_lagna in (2, 5, 9):
        return {
            "en": "Silver (Rajata Paya) - Most auspicious; brings royal comfort, wealth, and smooth fortune",
            "bn": "রৌপ্য পায়া (Silver) - সর্বাধিক শুভ; রাজকীয় আরাম, সমৃদ্ধি ও নির্বিঘ্ন সৌভাগ্যদায়ক",
            "hi": "रजत पाया (Silver) - सर्वाधिक शुभ; राजसी सुख, धन-वैभव और सहज सफलता",
        }
    elif moon_house_from_lagna in (3, 7, 10):
        return {
            "en": "Copper (Tamra Paya) - Dynamic action; courage, victory in competition, and prosperity through effort",
            "bn": "তাম্র পায়া (Copper) - প্রচণ্ড কর্মদ্যোগ; সাহস, প্রতিযোগিতায় জয় ও স্বোপার্জিত সাফল্য",
            "hi": "ताम्र पाया (Copper) - पराक्रम और उद्यम; साहस, विजय और कर्म से अपार उन्नति",
        }
    else:  # 4, 8, 12
        return {
            "en": "Iron (Loha Paya) - Karmic endurance; demands immense discipline and perseverance to transform destiny",
            "bn": "লৌহ পায়া (Iron) - কঠোর তপস্যা ও সংযম; বাধা অতিক্রম করে জীবনের দ্বিতীয়ার্ধে সুদৃঢ় প্রতিষ্ঠা",
            "hi": "लौह पाया (Iron) - कर्मठता व अनुशासन; संघर्षों के बाद जीवन में सुदृढ़ आधार",
        }


# =============================================================================
# Classical Gandanta Rules & Dosha Detection
# =============================================================================

def calculate_gandanta(moon_lon: float, nak_idx: int, pada: int) -> dict[str, Any]:
    """Detects classical Gandanta (Junction of Water & Fire Signs).
    Covers the 3 critical Sandhi junctions:
    1. Ashlesha Pada 4 (Cancer end) & Magha Pada 1 (Leo start)
    2. Jyeshtha Pada 4 (Scorpio end) & Mula Pada 1 (Sagittarius start - Abhukta Mula)
    3. Revati Pada 4 (Pisces end) & Ashwini Pada 1 (Aries start)
    """
    gandanta_stars = {0, 8, 9, 17, 18, 26}
    if nak_idx not in gandanta_stars:
        return {
            "is_gandanta": False,
            "gandanta_type": "None",
            "junction_name_en": "No Gandanta (Safe)",
            "junction_name_bn": "গণ্ডান্ত মুক্ত (নিরাপদ)",
            "junction_name_hi": "गंडान्त मुक्त (सुरक्षित)",
            "severity": "None",
            "description_en": "Birth nakshatra does not fall on the delicate water-fire elemental junction.",
            "description_bn": "জন্ম নক্ষত্র কোনো জল ও অগ্নির সংযোগস্থল (গণ্ডান্ত)-এ অবস্থান করছে না।",
            "description_hi": "जन्म नक्षत्र किसी जल और अग्नि के संवेदनशील मिलन स्थल (गंडान्त) पर नहीं है।",
            "remedies_en": [],
            "remedies_bn": [],
            "remedies_hi": [],
        }

    # Abhukta Mula / Vrishchika-Dhanu Gandanta (Jyeshtha 4 & Mula 1)
    if (nak_idx == 17 and pada == 4) or (nak_idx == 18 and pada == 1):
        is_mula = (nak_idx == 18)
        return {
            "is_gandanta": True,
            "gandanta_type": "Abhukta Mula (Scorpio-Sagittarius Sandhi)",
            "junction_name_en": "Vrishchika-Dhanu Junction (Abhukta Mula)",
            "junction_name_bn": "বৃশ্চিক-ধনু সন্ধি (অভুক্ত মূলা গণ্ডান্ত)",
            "junction_name_hi": "वृश्चिक-धनु संधि (अभुक्त मूल गंडान्त)",
            "severity": "Extreme (Abhukta Mula)",
            "description_en": (
                f"Born in {('Mula Pada 1' if is_mula else 'Jyeshtha Pada 4')}, the most sensitive junction in Vedic astrology. "
                "Represents a profound spiritual transformation and karmic transition between Scorpio (Water) and Sagittarius (Fire)."
            ),
            "description_bn": (
                f"জাতক {('মূলা নক্ষত্রের ১ম পদে' if is_mula else 'জ্যেষ্ঠা নক্ষত্রের ৪র্থ পদে')} জন্মগ্রহণ করেছেন, যা শাস্ত্র মতে সর্বোচ্চ সংবেদনশীল 'অভুক্ত মূলা গণ্ডান্ত'। "
                "এটি গভীর আধ্যাত্মিক উত্তরণ ও ভাগ্যোন্নতির ইঙ্গিত দেয়, তবে শৈশবে স্বাস্থ্য ও পারিবারিক শান্তির জন্য বিশেষ শান্তির বিধান আবশ্যক।"
            ),
            "description_hi": (
                f"जातक का जन्म {('मूल नक्षत्र के प्रथम चरण' if is_mula else 'ज्येष्ठा नक्षत्र के चतुर्थ चरण')} में हुआ है, जो वैदिक ज्योतिष में 'अभुक्त मूल गंडान्त' कहलाता है। "
                "यह अत्यधिक संवेदनशील आध्यात्मिक परिवर्तन का सूचक है तथा इसकी शांति पूजा आवश्यक मानी जाती है।"
            ),
            "remedies_en": [
                "Perform Mula Shanti / Gandanta Shanti Puja exactly on the 27th day after birth when the Moon returns to the birth star.",
                "Donate a bronze vessel (Kamsa Patra) filled with pure cow ghee and gold/silver after seeing reflection.",
                "Worship Lord Ganesha regularly and recite Ketu Beej Mantra (Om Kem Ketave Namah) or Maha Mrityunjaya Mantra.",
                "Feed cows with green fodder on Wednesdays and Thursdays.",
            ],
            "remedies_bn": [
                "জন্মের ২৭তম দিনে চন্দ্র যখন পুনরায় এই নক্ষত্রে আসে তখন মূল শান্তি / গণ্ডান্ত শান্তি পূজা সম্পন্ন করুন।",
                "কাঁসার পাত্রে ঘৃত ঢেলে নিজের মুখ দেখে তা বস্ত্র ও দক্ষিণা সহ দান করা পরম কল্যাণকর।",
                "শ্রী গণেশের আরাধনা ও মহামৃত্যুঞ্জয় মন্ত্র নিয়মিত জপ করুন।",
                "বুধবার ও বৃহস্পতিবার গোমাতাকে কাঁচা ঘাস ও গুড় খাওয়ান।",
            ],
            "remedies_hi": [
                "जन्म के २७वें दिन जब चंद्रमा पुनः इसी नक्षत्र में आए तब मूल शांति/गंडान्त शांति पूजा करवाएं।",
                "कांस्य पात्र में शुद्ध घी भरकर उसमें छाया देखकर वस्त्र व दक्षिणा सहित दान करें।",
                "भगवान गणेश की आराधना एवं महामृत्युंजय मंत्र का नियमित पाठ करें।",
                "बुधवार और गुरुवार को गाय को हरा चारा व गुड़ खिलाएं।",
            ],
        }

    # Karka-Simha Gandanta (Ashlesha 4 & Magha 1)
    if (nak_idx == 8 and pada == 4) or (nak_idx == 9 and pada == 1):
        is_magha = (nak_idx == 9)
        return {
            "is_gandanta": True,
            "gandanta_type": "Karka-Simha Sandhi Gandanta",
            "junction_name_en": "Cancer-Leo Junction (Ashlesha-Magha Sandhi)",
            "junction_name_bn": "কর্কট-সিংহ সন্ধি (অশ্লেষা-মঘা গণ্ডান্ত)",
            "junction_name_hi": "कर्क-सिंह संधि (आश्लेषा-मघा गंडान्त)",
            "severity": "High",
            "description_en": (
                f"Born in {('Magha Pada 1' if is_magha else 'Ashlesha Pada 4')}, marking the intense psychic transition from Cancer (Water) to Leo (Fire). "
                "Bestows extraordinary spiritual depth and leadership qualities once balanced through Vedic rituals."
            ),
            "description_bn": (
                f"জাতক {('মঘা নক্ষত্রের ১ম পদে' if is_magha else 'অশ্লেষা নক্ষত্রের ৪র্থ পদে')} জন্মগ্রহণ করেছেন, যা কর্কট (জল) ও সিংহ (অগ্নি)-র গুরুত্বপূর্ণ গণ্ডান্ত সন্ধি। "
                "এটি গভীর মনস্তাত্ত্বিক উপলব্ধি ও নেতৃত্বক্ষমতা প্রদান করে, তবে আত্মনিয়ন্ত্রণ ও শান্তির বিধান অত্যন্ত শুভদায়ক।"
            ),
            "description_hi": (
                f"जातक का जन्म {('मघा नक्षत्र के प्रथम चरण' if is_magha else 'आश्लेषा नक्षत्र के चतुर्थ चरण')} में हुआ है, जो कर्क (जल) और सिंह (अग्नि) का गंडान्त मिलन है। "
                "यह जातक को असाधारण नेतृत्व व आध्यात्मिक क्षमता देता है।"
            ),
            "remedies_en": [
                "Perform Ashlesha/Magha Shanti Puja with Abhishek to Lord Shiva and Navagraha homa.",
                "Offer milk to Nagas / Shiva Lingam on Mondays and avoid gossiping or speaking ill of others.",
                "Donate black sesame seeds, copper vessel, or blankets to the needy.",
            ],
            "remedies_bn": [
                "ভগবান শিবের রুদ্রাভিষেক এবং অশ্লেষা/মঘা গণ্ডান্ত শান্তি পূজা সম্পন্ন করুন।",
                "প্রতি সোমবার শিবলিঙ্গে কাঁচা দুধ ও গঙ্গাজল অর্পণ করুন এবং পরনিন্দা বর্জন করুন।",
                "কালো তিল, তামার পাত্র অথবা কম্বল দুস্থদের দান করুন।",
            ],
            "remedies_hi": [
                "भगवान शिव का रुद्राभिषेक एवं गंडान्त शांति पूजा करवाएं।",
                "सोमवार को शिवलिंग पर कच्चा दूध व जल चढ़ाएं और परनिंदा से बचें।",
                "काले तिल, तांबे का पात्र या कंबल जरूरतमंदों को दान करें।",
            ],
        }

    # Meena-Mesha Gandanta (Revati 4 & Ashwini 1)
    if (nak_idx == 26 and pada == 4) or (nak_idx == 0 and pada == 1):
        is_ashw = (nak_idx == 0)
        return {
            "is_gandanta": True,
            "gandanta_type": "Meena-Mesha Sandhi Gandanta",
            "junction_name_en": "Pisces-Aries Junction (Revati-Ashwini Sandhi)",
            "junction_name_bn": "মীন-মেষ সন্ধি (রেবতী-অশ্বিনী গণ্ডান্ত)",
            "junction_name_hi": "मीन-मेष संधि (रेवती-अश्विनी गंडान्त)",
            "severity": "Moderate to High",
            "description_en": (
                f"Born in {('Ashwini Pada 1' if is_ashw else 'Revati Pada 4')}, marking the end of the 12th sign Pisces and the fresh dawn in Aries. "
                "Signifies a powerful rebirth, quick vitality, and extraordinary pioneering energy."
            ),
            "description_bn": (
                f"জাতক {('অশ্বিনী নক্ষত্রের ১ম পদে' if is_ashw else 'রেবতী নক্ষত্রের ৪র্থ পদে')} জন্মগ্রহণ করেছেন, যা রাশিচক্রের সমাপনী মীন (জল) ও সূচনাকারী মেষ (অগ্নি)-র গণ্ডান্ত সংযোগ। "
                "এটি জাতককে নতুন পথের দিশারী ও অতুলনীয় জীবনীশক্তি দেয়।"
            ),
            "description_hi": (
                f"जातक का जन्म {('अश्विनी नक्षत्र के प्रथम चरण' if is_ashw else 'रेवती नक्षत्र के चतुर्थ चरण')} में हुआ है, जो मीन (जल) और मेष (अग्नि) का संधि स्थल है। "
                "यह पुनर्जन्म व तेजस्विता का प्रतीक है।"
            ),
            "remedies_en": [
                "Perform Revati/Ashwini Nakshatra Shanti on the next arrival of the birth star.",
                "Feed green fodder or gram to horses or visit cowsheds on Tuesdays and Wednesdays.",
                "Chant Vishnu Sahasranama or Gayatri Mantra 108 times daily.",
            ],
            "remedies_bn": [
                "জন্ম নক্ষত্রের পুনরাগমনে রেবতী/অশ্বিনী শান্তি পূজা অনুষ্ঠান করুন।",
                "বুধবার ও মঙ্গলবার সবুজ ঘাস অথবা ছোলা অশ্ব বা গোমাতাকে খাওয়ান।",
                "প্রতিদিন ১০৮ বার গায়ত্রী মন্ত্র অথবা বিষ্ণু সহস্রনাম পাঠ করুন।",
            ],
            "remedies_hi": [
                "नक्षत्र की शांति पूजा संपन्न करवाएं।",
                "बुधवार और मंगलवार को घोड़ों या गायों को हरा चारा व चने खिलाएं।",
                "प्रतिदिन १०८ बार गायत्री मंत्र अथवा विष्णु सहस्रनाम का जप करें।",
            ],
        }

    # Born in a Gandanta Nakshatra but not in Sandhi Pada (e.g. Mula Pada 2, 3, 4)
    star_names = {0: "Ashwini", 8: "Ashlesha", 9: "Magha", 17: "Jyeshtha", 18: "Mula", 26: "Revati"}
    name = star_names.get(nak_idx, "Gandanta Star")
    return {
        "is_gandanta": False,
        "gandanta_type": "Mridu Gandanta Star (Safe from Sandhi Dosha)",
        "junction_name_en": f"{name} (Pada {pada} - Non-Sandhi Safe Zone)",
        "junction_name_bn": f"{name} ({pada} নং পদ - সন্ধি দোষ মুক্ত নিরাপদ অংশ)",
        "junction_name_hi": f"{name} (चरण {pada} - संधि दोष मुक्त सुरक्षित भाग)",
        "severity": "Low / Safe",
        "description_en": f"Born in {name} star, but safely placed in Pada {pada} away from the hazardous water-fire cusp.",
        "description_bn": f"জাতক {name} নক্ষত্রের {pada} নং পদে জন্মগ্রহণ করেছেন, যা সন্ধিদোষের বিপজ্জনক প্রান্ত থেকে সুরক্ষিত ও মুক্ত।",
        "description_hi": f"जातक {name} के चरण {pada} में है, जो संधि के अनिष्टकारी प्रभाव से सुरक्षित है।",
        "remedies_en": ["Regular devotion to the ruling deity of the star brings auspicious stability."],
        "remedies_bn": ["নক্ষত্র দেবতার নিয়মিত উপাসনা জাতকের জীবনে পরম স্থায়িত্ব ও সৌভাগ্য বয়ে আনে।"],
        "remedies_hi": ["नक्षत्र देवता की नियमित उपासना से जीवन में सुख-समृद्धि बनी रहती है।"],
    }


# =============================================================================
# Classical Pushkara Navamsha & Pushkara Bhaga Calculation
# =============================================================================

# Pushkara Bhaga degree points in each of the 12 signs
PUSHKARA_BHAGA_DEGREES = [21.0, 14.0, 18.0, 8.0, 19.0, 9.0, 24.0, 11.0, 23.0, 14.0, 19.0, 9.0]

def calculate_pushkara(rashi_idx: int, degree_in_sign: float, navamsha_sign: str, pada: int) -> dict[str, Any]:
    """Calculates whether the Moon is in Pushkara Navamsha (24 sacred zones)
    or Pushkara Bhaga (exact royal conferring degree).
    """
    is_pn = False
    is_pb = False

    # Check Pushkara Navamsha based on elemental triplicity
    if rashi_idx in (0, 4, 8):  # Fire: 7th (20°00'-23°20') and 9th (26°40'-30°00')
        if (20.0 <= degree_in_sign < 23.33333333) or (26.66666667 <= degree_in_sign <= 30.0):
            is_pn = True
    elif rashi_idx in (1, 5, 9):  # Earth: 3rd (6°40'-10°00') and 5th (13°20'-16°40')
        if (6.66666667 <= degree_in_sign < 10.0) or (13.33333333 <= degree_in_sign < 16.66666667):
            is_pn = True
    elif rashi_idx in (2, 6, 10):  # Air: 6th (16°40'-20°00') and 8th (23°20'-26°40')
        if (16.66666667 <= degree_in_sign < 20.0) or (23.33333333 <= degree_in_sign < 26.66666667):
            is_pn = True
    elif rashi_idx in (3, 7, 11):  # Water: 1st (0°00'-3°20') and 3rd (6°40'-10°00')
        if (0.0 <= degree_in_sign < 3.33333333) or (6.66666667 <= degree_in_sign < 10.0):
            is_pn = True

    # Check Pushkara Bhaga (within 1 degree of exact point)
    pb_target = PUSHKARA_BHAGA_DEGREES[rashi_idx]
    if abs(degree_in_sign - pb_target) <= 1.0:
        is_pb = True

    deg_d = int(degree_in_sign)
    deg_m = int(round((degree_in_sign - deg_d) * 60.0))
    deg_str = f"{deg_d}° {deg_m:02d}'"

    return {
        "is_pushkara_navamsha": is_pn,
        "is_pushkara_bhaga": is_pb,
        "navamsha_sign_en": navamsha_sign,
        "navamsha_sign_bn": navamsha_sign,
        "navamsha_sign_hi": navamsha_sign,
        "pada_number": pada,
        "degree_in_sign": round(degree_in_sign, 4),
        "degree_in_sign_formatted": deg_str,
        "significance_en": (
            "Sacred Pushkara Placement — Nourishes mental tranquility, heals planetary afflictions, and confers extraordinary spiritual merit."
            if (is_pn or is_pb) else "Standard Navamsha Placement."
        ),
        "significance_bn": (
            "পরম শুভ পুষ্কর নবাংশ স্থিতি — মানসিক প্রশান্তি, কোষ্ঠীর বহু অমঙ্গল নাশ এবং ভাগ্যোন্নতির স্বর্গীয় সঞ্জীবনী শক্তি প্রদান করে।"
            if (is_pn or is_pb) else "সাধারণ নবাংশ স্থিতি।"
        ),
        "significance_hi": (
            "परम शुभ पुष्कर नवांश स्थिति — मानसिक शांति, अरिष्टों का शमन एवं सौभाग्य की वृद्धि करने वाली दैवीय स्थिति।"
            if (is_pn or is_pb) else "सामान्य नवांश स्थिति।"
        ),
    }


# =============================================================================
# Vimshottari Dasha Balance at Birth
# =============================================================================

VIMSHOTTARI_YEARS: dict[str, int] = {
    "Ketu": 7,
    "Venus": 20,
    "Sun": 6,
    "Moon": 10,
    "Mars": 7,
    "Rahu": 18,
    "Jupiter": 16,
    "Saturn": 19,
    "Mercury": 17,
}

VIMSHOTTARI_NAMES_BN: dict[str, str] = {
    "Ketu": "কেতু",
    "Venus": "শুক্র",
    "Sun": "রবি / সূর্য",
    "Moon": "চন্দ্র",
    "Mars": "মঙ্গল",
    "Rahu": "রাহু",
    "Jupiter": "বৃহস্পতি",
    "Saturn": "শনি",
    "Mercury": "বুধ",
}

VIMSHOTTARI_NAMES_HI: dict[str, str] = {
    "Ketu": "केतु",
    "Venus": "शुक्र",
    "Sun": "सूर्य",
    "Moon": "चंद्र",
    "Mars": "मंगल",
    "Rahu": "राहु",
    "Jupiter": "गुरु / बृहस्पति",
    "Saturn": "शनि",
    "Mercury": "बुध",
}

def calculate_dasha_balance(star_lord: str, deg_in_nak: float) -> dict[str, Any]:
    """Calculates exact Vimshottari Mahadasha balance remaining at the birth instant."""
    total_cycle = VIMSHOTTARI_YEARS.get(star_lord, 7)
    nak_span = 360.0 / 27.0  # 13.33333333... degrees
    elapsed_frac = max(0.0, min(1.0, deg_in_nak / nak_span))
    remain_frac = max(0.0, min(1.0, 1.0 - elapsed_frac))

    total_remain_years = remain_frac * total_cycle
    b_years = int(total_remain_years)
    rem_months = (total_remain_years - b_years) * 12.0
    b_months = int(rem_months)
    b_days = int(round((rem_months - b_months) * 30.0))

    if b_days >= 30:
        b_days -= 30
        b_months += 1
    if b_months >= 12:
        b_months -= 12
        b_years += 1

    lord_en = star_lord
    lord_bn = VIMSHOTTARI_NAMES_BN.get(star_lord, star_lord)
    lord_hi = VIMSHOTTARI_NAMES_HI.get(star_lord, star_lord)

    fmt_en = f"{lord_en} Mahadasha: {b_years} Years, {b_months} Months, {b_days} Days remaining"
    fmt_bn = f"{lord_bn}-র মহাদশা ভোগ বাকি: {b_years} বছর, {b_months} মাস, {b_days} দিন"
    fmt_hi = f"{lord_hi} महादशा शेष: {b_years} वर्ष, {b_months} माह, {b_days} दिन"

    return {
        "dasha_lord_en": lord_en,
        "dasha_lord_bn": lord_bn,
        "dasha_lord_hi": lord_hi,
        "total_cycle_years": total_cycle,
        "balance_years": b_years,
        "balance_months": b_months,
        "balance_days": b_days,
        "balance_formatted_en": fmt_en,
        "balance_formatted_bn": fmt_bn,
        "balance_formatted_hi": fmt_hi,
        "elapsed_percentage": round(elapsed_frac * 100.0, 2),
        "remaining_percentage": round(remain_frac * 100.0, 2),
    }


# =============================================================================
# Real-Time Daily Transit Tara Bala (Ephemeris Transit)
# =============================================================================

TARA_NAMES = [
    {
        "step": 1,
        "name_en": "Janma Tara", "name_bn": "জন্ম তারা", "name_hi": "जन्म तारा",
        "is_auspicious": False,
        "status_en": "Caution / Body & Health Care",
        "status_bn": "সতর্কতা / স্বাস্থ্য ও মানসিক চাপ",
        "status_hi": "सावधानी / स्वास्थ्य व मानसिक सतर्कता",
        "guidance_en": "Today Moon activates your birth star. Avoid starting risky new projects; focus on routine tasks and self-care.",
        "guidance_bn": "আজ গোচর চন্দ্র আপনার জন্ম তারায় অবস্থান করছে। ঝুঁকিপূর্ণ নতুন চুক্তি বা ভ্রমণ এড়িয়ে চলুন; শান্তভাবে রুটিন কাজ করুন।",
        "guidance_hi": "आज गोचर चंद्र आपकी जन्म तारा पर है। जोखिम भरे नए कार्य टालें, स्वास्थ्य का ध्यान रखें।",
    },
    {
        "step": 2,
        "name_en": "Sampat Tara", "name_bn": "সম্পদ তারা", "name_hi": "संपत तारा",
        "is_auspicious": True,
        "status_en": "Highly Auspicious / Wealth & Gains",
        "status_bn": "পরম শুভ / অর্থলাভ ও উন্নতি",
        "status_hi": "अत्यंत शुभ / धन लाभ व प्रगति",
        "guidance_en": "Exceptional day for financial transactions, investments, career negotiations, and entering prosperous new partnerships.",
        "guidance_bn": "আর্থিক লেনদেন, ব্যবসায়িক নতুন চুক্তি, ইন্টারভিউ ও সম্পদ বৃদ্ধির জন্য অত্যন্ত শুভ ও ফলপ্রসূ দিন।",
        "guidance_hi": "आर्थिक लेन-देन, नए सौदे और धन वृद्धि के लिए अत्यंत अनुकूल व फलदायी दिन।",
    },
    {
        "step": 3,
        "name_en": "Vipat Tara", "name_bn": "বিপদ তারা", "name_hi": "विपत तारा",
        "is_auspicious": False,
        "status_en": "Inauspicious / Hurdles & Delays",
        "status_bn": "প্রতিকূল / বিঘ্ন ও বাধার আশঙ্কা",
        "status_hi": "अशुभ / विघ्न व बाधा की आशंका",
        "guidance_en": "Prone to sudden obstacles, disputes, or losses. Avoid major financial commitments, arguments, and rash travel.",
        "guidance_bn": "হঠাৎ বাধা, মতবিরোধ ও ক্ষতির আশঙ্কা রয়েছে। বিতর্ক এড়িয়ে চলুন এবং কোনো গুরুত্বপূর্ণ নতুন কাজে হাত দেবেন না।",
        "guidance_hi": "अचानक बाधाओं और विवादों की आशंका। बड़े निर्णयों और नई शुरुआतों से बचें।",
    },
    {
        "step": 4,
        "name_en": "Kshema Tara", "name_bn": "ক্ষেম তারা", "name_hi": "क्षेम तारा",
        "is_auspicious": True,
        "status_en": "Auspicious / Well-being & Prosperity",
        "status_bn": "অত্যন্ত শুভ / কল্যাণ ও সমৃদ্ধি",
        "status_hi": "शुभ / कल्याण व सुरक्षा",
        "guidance_en": "Brings comfort, protection, safe travel, and harmonious family life. Excellent for healing, buying property, and creative tasks.",
        "guidance_bn": "পারিবারিক আনন্দ, নিরাপদ যাত্রা, দীর্ঘমেয়াদী পরিকল্পনা ও শুভ উদ্যোগ সফল হওয়ার অনুকূল দিন।",
        "guidance_hi": "सुरक्षा, पारिवारिक सुख, मंगलमय यात्रा और नए रचनात्मक कार्यों के लिए उत्तम दिन।",
    },
    {
        "step": 5,
        "name_en": "Pratyak Tara", "name_bn": "প্রত্যরি তারা", "name_hi": "प्रत्यरि तारा",
        "is_auspicious": False,
        "status_en": "Inauspicious / Enmity & Friction",
        "status_bn": "প্রতিকূল / শত্রুতা ও বিরোধিতা",
        "status_hi": "अशुभ / शत्रुता व विरोध",
        "guidance_en": "Risk of misunderstandings, friction with rivals, and legal or administrative hurdles. Keep calm and avoid confrontation.",
        "guidance_bn": "শত্রুপক্ষের সক্রিয়তা বা কর্মক্ষেত্রে ভুল বোঝাবুঝির আশঙ্কা। শান্ত থাকুন এবং সংঘাত এড়িয়ে চলুন।",
        "guidance_hi": "विरोधियों की सक्रियता और मतभेद की आशंका। वाद-विवाद से बचें और संयम रखें।",
    },
    {
        "step": 6,
        "name_en": "Sadhana Tara", "name_bn": "সাধনা তারা", "name_hi": "साधना तारा",
        "is_auspicious": True,
        "status_en": "Extremely Auspicious / Accomplishment & Success",
        "status_bn": "সিদ্ধিদায়ক শুভ / অভীষ্ট সিদ্ধি ও জয়",
        "status_hi": "अत्यंत शुभ / कार्य सिद्धि व सफलता",
        "guidance_en": "Superb for focused study, difficult tasks, spiritual practices, competitive exams, and achieving goals through dedicated effort.",
        "guidance_bn": "কঠিন লক্ষ্য পূরণ, পড়াশোনা, আধ্যাত্মিক সাধনা এবং প্রতিযোগিতায় বিজয়ের জন্য অত্যন্ত শক্তিশালী ও শুভ দিন।",
        "guidance_hi": "कठिन लक्ष्यों की प्राप्ति, अध्ययन, साधना और परीक्षा-प्रतियोगिता में विजय के लिए श्रेष्ठ दिन।",
    },
    {
        "step": 7,
        "name_en": "Naidhana / Vadha Tara", "name_bn": "নিধন / বধ তারা", "name_hi": "निधन / वध तारा",
        "is_auspicious": False,
        "status_en": "High Caution Alert / Severe Danger & Peril",
        "status_bn": "লাল সতর্কতা / পরম অশুভ ও হানি",
        "status_hi": "गंभीर चेतावनी / परम अशुभ व हानि",
        "guidance_en": "Most hazardous Tara. Strictly avoid surgery, aggressive driving, risky financial speculations, and vital agreements today.",
        "guidance_bn": "সর্বাধিক সতর্কতার দিন। নতুন চুক্তি, অস্ত্রোপচার, ঝুঁকিপূর্ণ বিনিয়োগ ও ভ্রমণ কঠোরভাবে বর্জন করুন। মহামৃত্যুঞ্জয় জপ করুন।",
        "guidance_hi": "सर्वाधिक जोखिम भरा दिन। नए अनुबंध, शल्य चिकित्सा, जोखिम भरे निवेश और यात्रा से बचें।",
    },
    {
        "step": 8,
        "name_en": "Mitra Tara", "name_bn": "মিত্র তারা", "name_hi": "मित्र तारा",
        "is_auspicious": True,
        "status_en": "Auspicious / Friendship & Joy",
        "status_bn": "পরম শুভ / সৌহার্দ্য ও সুখবর",
        "status_hi": "शुभ / मित्रता व सहयोग",
        "guidance_en": "Fosters warm relationships, social gatherings, fruitful collaborations, and joyful meetings with mentors or allies.",
        "guidance_bn": "বন্ধুত্ব, সামাজিক মিলনমেলা, উচ্চপদস্থ ব্যক্তির সহায়তা ও পারস্পরিক সমঝোতার জন্য আনন্দময় শুভ দিন।",
        "guidance_hi": "मित्रों व वरिष्ठों से सहयोग, सुखद यात्रा और नए सामाजिक संबंधों के लिए अनुकूल दिन।",
    },
    {
        "step": 9,
        "name_en": "Ati-Mitra / Parama Mitra Tara", "name_bn": "পরম মিত্র তারা", "name_hi": "अति-मित्र तारा",
        "is_auspicious": True,
        "status_en": "Supreme Auspiciousness / Triumph & Highest Gains",
        "status_bn": "সর্বশ্রেষ্ঠ শুভ / চূড়ান্ত সাফল্য ও সৌভাগ্য",
        "status_hi": "परम शुभ / विजय व सर्वतोमुखी लाभ",
        "guidance_en": "Golden day. Blesses every sincere initiative with victory, honor, and long-lasting prosperity. Ideal for signing contracts.",
        "guidance_bn": "সুবর্ণ দিন। যেকোনো গুরুত্বপূর্ণ কাজ, শুভ চুক্তি স্বাক্ষর, গৃহপ্রবেশ বা বড় পদক্ষেপে বিজয় ও স্থায়ী সাফল্য নিশ্চিত করে।",
        "guidance_hi": "स्वर्ण दिवस। महत्वपूर्ण समझौतों, गृहप्रवेश और बड़े उपक्रमों में विजय व सफलता दिलाने वाला दिन।",
    },
]

def calculate_daily_tara_bala(swe_module, jd_now: float, birth_nak_idx: int) -> dict[str, Any]:
    """Calculates live real-time Tara Bala transit from the current Swiss Ephemeris Moon position."""
    swe_module.set_sid_mode(swe_module.SIDM_LAHIRI)
    calc_flags = swe_module.FLG_SIDEREAL | swe_module.FLG_SPEED
    moon_res, _ = swe_module.calc_ut(jd_now, swe_module.MOON, calc_flags)
    curr_moon_lon = moon_res[0] % 360.0

    nak_span = 360.0 / 27.0
    curr_nak_idx = int(curr_moon_lon / nak_span) % 27
    curr_meta = NAKSHATRAS_MASTER[curr_nak_idx]

    step = ((curr_nak_idx - birth_nak_idx) % 9) + 1  # 1 to 9
    tara_info = TARA_NAMES[step - 1]

    return {
        "current_moon_nakshatra_index": curr_nak_idx,
        "current_moon_nakshatra_name_en": curr_meta["name_en"],
        "current_moon_nakshatra_name_bn": curr_meta["name_bn"],
        "current_moon_nakshatra_name_hi": curr_meta["name_hi"],
        "tara_step": step,
        "tara_name_en": tara_info["name_en"],
        "tara_name_bn": tara_info["name_bn"],
        "tara_name_hi": tara_info["name_hi"],
        "is_auspicious": tara_info["is_auspicious"],
        "status_label_en": tara_info["status_en"],
        "status_label_bn": tara_info["status_bn"],
        "status_label_hi": tara_info["status_hi"],
        "guidance_en": tara_info["guidance_en"],
        "guidance_bn": tara_info["guidance_bn"],
        "guidance_hi": tara_info["guidance_hi"],
    }


# =============================================================================
# 7 Classical Nakshatra Dispositions & Totem Matrix
# =============================================================================

DISPOSITIONS_MASTER: list[dict[str, Any]] = [
    # 0: Ashwini
    {
        "disposition_en": "Kshipra / Laghu (Swift & Light)",
        "disposition_bn": "ক্ষিপ্র / লঘু (দ্রুত ও ক্ষিপ্র গতিশীল)",
        "disposition_hi": "क्षिप्र / लघु (तीव्र व फुर्तीला)",
        "gunas_en": "Rajas - Tamas - Rajas", "gunas_bn": "রজঃ - তমঃ - রজঃ", "gunas_hi": "रजस - तमस - रजस",
        "caste_varna_en": "Vaishya (Merchant)", "caste_varna_bn": "বৈশ্য", "caste_varna_hi": "वैश्य",
        "gender_en": "Male", "gender_bn": "পুরুষ", "gender_hi": "पुरुष",
        "direction_en": "South", "direction_bn": "দক্ষিণ", "direction_hi": "दक्षिण",
        "sacred_bird_en": "Wild Eagle / Falcon", "sacred_bird_bn": "বন ঈগল / বাজপাখি", "sacred_bird_hi": "जंगली चील / बाज",
        "suitable_activities_en": ["Medical treatments", "Taking medicines", "Starting journeys", "Sports & athletics", "Beginning trade transactions"],
        "suitable_activities_bn": ["চিকিৎসা গ্রহণ ও ঔষধ সেবন", "নতুন যাত্রা শুরু", "খেলাধুলা ও শরীরচর্চা", "বাণিজ্যিক লেনদেন শুরু"],
        "suitable_activities_hi": ["चिकित्सा आरंभ व औषधि सेवन", "यात्रा प्रारंभ", "खेलकूद", "व्यापारिक लेन-देन की शुरुआत"],
    },
    # 1: Bharani
    {
        "disposition_en": "Ugra / Krura (Fierce & Aggressive)",
        "disposition_bn": "উগ্র / ক্রূর (তীব্র ও আক্রমণাত্মক)",
        "disposition_hi": "उग्र / क्रूर (कठोर व उग्र)",
        "gunas_en": "Rajas - Rajas - Tamas", "gunas_bn": "রজঃ - রজঃ - তমঃ", "gunas_hi": "रजस - रजस - तमस",
        "caste_varna_en": "Mleccha (Outcaste)", "caste_varna_bn": "ম্লেচ্ছ", "caste_varna_hi": "म्लेच्छ",
        "gender_en": "Female", "gender_bn": "স্ত্রী", "gender_hi": "स्त्री",
        "direction_en": "West", "direction_bn": "পশ্চিম", "direction_hi": "पश्चिम",
        "sacred_bird_en": "Crow", "sacred_bird_bn": "কাক", "sacred_bird_hi": "कौआ",
        "suitable_activities_en": ["Demolition", "Filing lawsuits", "Confronting adversaries", "Surgical procedures", "Research into hidden things"],
        "suitable_activities_bn": ["পুরোনো ভাঙা বা অপসারণ", "মামলা দায়ের", "শত্রুদমন", "অস্ত্রোপচার", "গভীর গোপনীয় অনুসন্ধান"],
        "suitable_activities_hi": ["पुराने निर्माण का निष्कासन", "मुकदमा दायर करना", "शत्रु दमन", "शल्य चिकित्सा", "गूढ़ शोध"],
    },
    # 2: Krittika
    {
        "disposition_en": "Mishra / Sadharana (Mixed / Dual)",
        "disposition_bn": "মিশ্র / সাধারণ (উগ্র ও সৌম্যের মিশ্রণ)",
        "disposition_hi": "मिश्र / साधारण (उग्र व सौम्य का मेल)",
        "gunas_en": "Rajas - Rajas - Sattva", "gunas_bn": "রজঃ - রজঃ - সত্ত্ব", "gunas_hi": "रजस - रजस - सत्त्व",
        "caste_varna_en": "Brahmin", "caste_varna_bn": "ব্রাহ্মণ", "caste_varna_hi": "ब्राह्मण",
        "gender_en": "Female", "gender_bn": "স্ত্রী", "gender_hi": "स्त्री",
        "direction_en": "North", "direction_bn": "উত্তর", "direction_hi": "उत्तर",
        "sacred_bird_en": "Peacock", "sacred_bird_bn": "ময়ূর", "sacred_bird_hi": "मोर",
        "suitable_activities_en": ["Fire rituals (Homa)", "Metalwork & cooking", "Taking bold oaths", "Cutting ties with negative habits"],
        "suitable_activities_bn": ["অগ্নিহোত্র ও হোমযজ্ঞ", "ধাতুশিল্প ও রন্ধনকার্য", "কঠোর সংকল্প গ্রহণ", "বদভ্যাস ত্যাগের শুভ সূচনা"],
        "suitable_activities_hi": ["अग्निहोत्र व हवन", "धातु कार्य", "दृढ़ संकल्प", "बुरी आदतों का त्याग"],
    },
    # 3: Rohini
    {
        "disposition_en": "Dhruva / Sthira (Fixed & Permanent)",
        "disposition_bn": "ধ্রুব / স্থির (স্থায়ী ও চিরন্তন ভিত্তি)",
        "disposition_hi": "ध्रुव / स्थिर (स्थायी व सुदृढ़ नींव)",
        "gunas_en": "Rajas - Tamas - Rajas", "gunas_bn": "রজঃ - তমঃ - রজঃ", "gunas_hi": "रजस - तमस - रजस",
        "caste_varna_en": "Shudra", "caste_varna_bn": "শূদ্র", "caste_varna_hi": "शूद्र",
        "gender_en": "Female", "gender_bn": "স্ত্রী", "gender_hi": "स्त्री",
        "direction_en": "East", "direction_bn": "পূর্ব", "direction_hi": "पूर्व",
        "sacred_bird_en": "Owl", "sacred_bird_bn": "পেঁচা", "sacred_bird_hi": "उल्लू",
        "suitable_activities_en": ["Coronations & ceremonies", "Housewarming (Griha Pravesha)", "Laying foundation stones", "Marriage ceremonies", "Planting trees"],
        "suitable_activities_bn": ["গৃহপ্রবেশ ও নতুন গৃহনির্মাণ", "ভিত্তিপ্রস্তর স্থাপন", "বিবাহ অনুষ্ঠান", "বৃক্ষরোপণ ও স্থায়ী বিনিয়োগ"],
        "suitable_activities_hi": ["गृहप्रवेश", "नींव रखना", "विवाह संस्कार", "वृक्षारोपण व दीर्घकालिक निवेश"],
    },
    # 4: Mrigashira
    {
        "disposition_en": "Mridu / Maitra (Soft, Gentle & Tender)",
        "disposition_bn": "মৃদু / মৈত্রী (কোমল, শান্ত ও প্রণয়ময়)",
        "disposition_hi": "मृदु / मैत्र (कोमल व सौम्य)",
        "gunas_en": "Rajas - Tamas - Tamas", "gunas_bn": "রজঃ - তমঃ - রজঃ", "gunas_hi": "रजस - तमस - तमस",
        "caste_varna_en": "Servant / Shudra", "caste_varna_bn": "শূদ্র", "caste_varna_hi": "शूद्र",
        "gender_en": "Neuter", "gender_bn": "নপুংসক", "gender_hi": "नपुंसक",
        "direction_en": "South", "direction_bn": "দক্ষিণ", "direction_hi": "दक्षिण",
        "sacred_bird_en": "Hen / Partridge", "sacred_bird_bn": "বনমোরগ / তিতির", "sacred_bird_hi": "मुर्गी / तीतर",
        "suitable_activities_en": ["Romance & courtship", "Wearing fine jewelry & apparel", "Singing, arts & music", "Entering friendships", "Short pleasure trips"],
        "suitable_activities_bn": ["প্রণয় ও বিবাহ প্রস্তাব", "নতুন অলঙ্কার ও বস্ত্র পরিধান", "সঙ্গীত ও ললিতকলা চর্চা", "নতুন বন্ধুত্ব স্থাপন ও ভ্রমণ"],
        "suitable_activities_hi": ["प्रणय निवेदन", "आभूषण व वस्त्र धारण", "संगीत व कला", "मैत्री संबंध व आनंद यात्रा"],
    },
    # 5: Ardra
    {
        "disposition_en": "Teekshna / Daruna (Dreadful & Sharp)",
        "disposition_bn": "তীক্ষ্ণ / দারুণ (কঠোর, তীব্র ও রূপান্তরমূলক)",
        "disposition_hi": "तीक्ष्ण / दारुण (कठोर व संहारक)",
        "gunas_en": "Rajas - Sattva - Tamas", "gunas_bn": "রজঃ - সত্ত্ব - তমঃ", "gunas_hi": "रजस - सत्त्व - तमस",
        "caste_varna_en": "Butcher / Hunter", "caste_varna_bn": "ব্যাধ", "caste_varna_hi": "व्याध",
        "gender_en": "Female", "gender_bn": "স্ত্রী", "gender_hi": "स्त्री",
        "direction_en": "West", "direction_bn": "পশ্চিম", "direction_hi": "पश्चिम",
        "sacred_bird_en": "Heron / Black Raven", "sacred_bird_bn": "বক / দাঁড়কাক", "sacred_bird_hi": "बगुला / कौआ",
        "suitable_activities_en": ["Deep research & demolition", "Dispelling evil energies", "Confronting hard truths", "Tantric spiritual disciplines"],
        "suitable_activities_bn": ["গবেষণা ও গোপন তথ্য উন্মোচন", "অশুভ শক্তি বিনাশ", "কঠোর সিদ্ধান্ত কার্যকর করা", "তন্ত্র সাধনা ও প্রতিকার"],
        "suitable_activities_hi": ["गहन शोध कार्य", "अशुभ ऊर्जा का निवारण", "कठोर निर्णय लेना", "तांत्रिक साधना"],
    },
    # 6: Punarvasu
    {
        "disposition_en": "Chara / Chala (Movable & Dynamic)",
        "disposition_bn": "চর / চল (গতিশীল ও পরিবর্তনশীল)",
        "disposition_hi": "चर / चल (गतिशील व परिवर्तनकारी)",
        "gunas_en": "Rajas - Sattva - Rajas", "gunas_bn": "রজঃ - সত্ত্ব - রজঃ", "gunas_hi": "रजस - सत्त्व - रजस",
        "caste_varna_en": "Vaishya", "caste_varna_bn": "বৈশ্য", "caste_varna_hi": "वैश्य",
        "gender_en": "Male", "gender_bn": "পুরুষ", "gender_hi": "पुरुष",
        "direction_en": "North", "direction_bn": "উত্তর", "direction_hi": "उत्तर",
        "sacred_bird_en": "Swan", "sacred_bird_bn": "রাজহংস", "sacred_bird_hi": "हंस",
        "suitable_activities_en": ["Travel & relocations", "Buying vehicles", "Rebuilding projects", "Renewing friendships", "Starting recovery programs"],
        "suitable_activities_bn": ["ভ্রমণ ও বাসস্থান পরিবর্তন", "যানবাহন ক্রয়", "পুনর্বাসন ও সংস্কার কাজ", "পুরোনো সম্পর্ক জোড়া লাগানো"],
        "suitable_activities_hi": ["यात्रा व स्थानांतरण", "वाहन क्रय", "पुनर्निर्माण", "टूटे संबंधों का सुधार"],
    },
    # 7: Pushya
    {
        "disposition_en": "Kshipra / Laghu (Swift & Nourishing)",
        "disposition_bn": "ক্ষিপ্র / লঘু (শুভ, পুষ্টিকর ও দ্রুত ফলদায়ক)",
        "disposition_hi": "क्षिप्र / लघु (कल्याणकारी व शुभफलदायक)",
        "gunas_en": "Rajas - Tamas - Sattva", "gunas_bn": "রজঃ - তমঃ - সত্ত্ব", "gunas_hi": "रजस - तमस - सत्त्व",
        "caste_varna_en": "Kshatriya", "caste_varna_bn": "ক্ষত্রিয়", "caste_varna_hi": "क्षत्रिय",
        "gender_en": "Male", "gender_bn": "পুরুষ", "gender_hi": "पुरुष",
        "direction_en": "East", "direction_bn": "পূর্ব", "direction_hi": "पूर्व",
        "sacred_bird_en": "Snipe / Sea Crow", "sacred_bird_bn": "পানকৌড়ি / গাঙচিল", "sacred_bird_hi": "जलमुर्गी / पपीहा",
        "suitable_activities_en": ["All auspicious beginnings (except marriage)", "Financial investments", "Taking high office", "Spiritual initiations", "Purchasing gold"],
        "suitable_activities_bn": ["বিবাহ ব্যতীত সমস্ত শুভ আরম্ভ", "স্বর্ণ ও রত্ন ক্রয়", "ব্যাংকিং ও বিনিয়োগ", "দীক্ষা গ্রহণ ও গুরুপূজা"],
        "suitable_activities_hi": ["विवाह छोड़कर सभी शुभ कार्य", "स्वर्ण क्रय", "वित्तीय निवेश", "दीक्षा ग्रहण"],
    },
    # 8: Ashlesha
    {
        "disposition_en": "Teekshna / Daruna (Dreadful & Mystic)",
        "disposition_bn": "তীক্ষ্ণ / দারুণ (রহস্যময়, তীব্র ও ভেদনশীল)",
        "disposition_hi": "तीक्ष्ण / दारुण (रहस्यमयी व भेदनकारी)",
        "gunas_en": "Rajas - Sattva - Tamas", "gunas_bn": "রজঃ - সত্ত্ব - তমঃ", "gunas_hi": "रजस - सत्त्व - तमस",
        "caste_varna_en": "Outcaste", "caste_varna_bn": "ম্লেচ্ছ", "caste_varna_hi": "म्लेच्छ",
        "gender_en": "Female", "gender_bn": "স্ত্রী", "gender_hi": "स्त्री",
        "direction_en": "South", "direction_bn": "দক্ষিণ", "direction_hi": "दक्षिण",
        "sacred_bird_en": "Sparrow", "sacred_bird_bn": "চড়ুই", "sacred_bird_hi": "गौरैया",
        "suitable_activities_en": ["Occult & serpent worship", "Psychological warfare", "Administering antidotes", "Competitive litigation"],
        "suitable_activities_bn": ["গুপ্তবিদ্যা ও নাগপূজা", "কূটনৈতিক চাল ও কৌশল", "প্রতিযোগিতামূলক মামলা", "বিষহর চিকিৎসা"],
        "suitable_activities_hi": ["गुप्त विद्या व सर्प पूजन", "रणनीति निर्माण", "विवाद निपटाना", "औषधि शोध"],
    },
    # 9: Magha
    {
        "disposition_en": "Ugra / Krura (Fierce, Royal & Ancestral)",
        "disposition_bn": "উগ্র / ক্রূর (রাজকীয়, তেজস্বী ও পিতৃপুরুষ-সম্পৃক্ত)",
        "disposition_hi": "उग्र / क्रूर (प्रतापी व राजसी)",
        "gunas_en": "Tamas - Rajas - Rajas", "gunas_bn": "তমঃ - রজঃ - রজঃ", "gunas_hi": "तमस - रजस - रजस",
        "caste_varna_en": "Shudra", "caste_varna_bn": "শূদ্র", "caste_varna_hi": "शूद्र",
        "gender_en": "Female", "gender_bn": "স্ত্রী", "gender_hi": "स्त्री",
        "direction_en": "West", "direction_bn": "পশ্চিম", "direction_hi": "पश्चिम",
        "sacred_bird_en": "Male Eagle", "sacred_bird_bn": "পুরুষ ঈগল", "sacred_bird_hi": "नर चील",
        "suitable_activities_en": ["Ancestral rites (Shraddha)", "Assuming leadership roles", "Historical research", "Military actions", "Confronting authorities"],
        "suitable_activities_bn": ["পিতৃতর্পণ ও শ্রাদ্ধকর্ম", "উচ্চপদের দায়িত্ব গ্রহণ", "ঐতিহাসিক গবেষণা", "সাহসিক অভিযান"],
        "suitable_activities_hi": ["पितृ तर्पण व श्राद्ध", "उच्च पद का कार्यभार", "ऐतिहासिक शोध", "साहसिक कार्य"],
    },
    # 10: Purva Phalguni
    {
        "disposition_en": "Ugra / Krura (Passionate & Fierce)",
        "disposition_bn": "উগ্র / ক্রূর (প্রণয়োদ্দীপক ও প্রবল তেজসম্পন্ন)",
        "disposition_hi": "उग्र / क्रूर (तेजस्वी व विलासी)",
        "gunas_en": "Tamas - Rajas - Tamas", "gunas_bn": "তমঃ - রজঃ - তমঃ", "gunas_hi": "तमस - रजस - तमस",
        "caste_varna_en": "Brahmin", "caste_varna_bn": "ব্রাহ্মণ", "caste_varna_hi": "ब्राह्मण",
        "gender_en": "Female", "gender_bn": "স্ত্রী", "gender_hi": "स्त्री",
        "direction_en": "North", "direction_bn": "উত্তর", "direction_hi": "उत्तर",
        "sacred_bird_en": "Female Eagle", "sacred_bird_bn": "স্ত্রী ঈগল", "sacred_bird_hi": "मादा चील",
        "suitable_activities_en": ["Artistic creations", "Entertainment & leisure", "Social negotiations", "Romance", "Resolving disputes through charm"],
        "suitable_activities_bn": ["ললিতকলা ও নাটক", "বিনোদন ও অবকাশ যাপন", "প্রণয় ও সামাজিক আলাপচারিতা", "আকর্ষণের মাধ্যমে সমস্যার সমাধান"],
        "suitable_activities_hi": ["कला व मनोरंजन", "विश्राम व आमोद-प्रमोद", "प्रणय संबंध", "पारस्परिक समझौते"],
    },
    # 11: Uttara Phalguni
    {
        "disposition_en": "Dhruva / Sthira (Fixed & Generous)",
        "disposition_bn": "ধ্রুব / স্থির (স্থায়ী, উদার ও পৃষ্ঠপোষক)",
        "disposition_hi": "ध्रुव / स्थिर (स्थायी व उदार)",
        "gunas_en": "Tamas - Rajas - Sattva", "gunas_bn": "তমঃ - রজঃ - সত্ত্ব", "gunas_hi": "तमस - रजस - सत्त्व",
        "caste_varna_en": "Kshatriya", "caste_varna_bn": "ক্ষত্রিয়", "caste_varna_hi": "क्षत्रिय",
        "gender_en": "Female", "gender_bn": "স্ত্রী", "gender_hi": "स्त्री",
        "direction_en": "East", "direction_bn": "পূর্ব", "direction_hi": "पूर्व",
        "sacred_bird_en": "Blue Jay / Beetle", "sacred_bird_bn": "নীলকণ্ঠ পাখি", "sacred_bird_hi": "नीलकंठ",
        "suitable_activities_en": ["Marriage ceremonies", "Entering contracts", "Foundations of institutions", "Charitable foundations", "Long-term agreements"],
        "suitable_activities_bn": ["বিবাহ অনুষ্ঠান", "দীর্ঘমেয়াদী চুক্তি সম্পাদন", "জনকল্যাণমূলক কাজের সূচনা", "গৃহনির্মাণ ও ভিত্তিপ্রস্তর স্থাপন"],
        "suitable_activities_hi": ["विवाह संस्कार", "दीर्घकालिक अनुबंध", "संस्थानों की नींव", "परोपकारी कार्य"],
    },
    # 12: Hasta
    {
        "disposition_en": "Kshipra / Laghu (Swift & Dexterous)",
        "disposition_bn": "ক্ষিপ্র / লঘু (দক্ষ, চটপটে ও দ্রুত ফলদায়ক)",
        "disposition_hi": "क्षिप्र / लघु (कुशल व त्वरित)",
        "gunas_en": "Tamas - Tamas - Rajas", "gunas_bn": "তমঃ - তমঃ - রজঃ", "gunas_hi": "तमस - तमस - रजस",
        "caste_varna_en": "Vaishya", "caste_varna_bn": "বৈশ্য", "caste_varna_hi": "वैश्य",
        "gender_en": "Male", "gender_bn": "পুরুষ", "gender_hi": "पुरुष",
        "direction_en": "South", "direction_bn": "দক্ষিণ", "direction_hi": "दक्षिण",
        "sacred_bird_en": "Vulture / Kite", "sacred_bird_bn": "শকুনি / চিল", "sacred_bird_hi": "गिद्ध / चील",
        "suitable_activities_en": ["Handicrafts & surgery", "Commercial trade", "Magic & sleight of hand", "Starting journeys", "Astrological counseling"],
        "suitable_activities_bn": ["হস্তশিল্প ও কারিগরি বিদ্যা", "চিকিৎসা ও অস্ত্রোপচার", "বাণিজ্যিক লেনদেন", "জ্যোতিষ পরামর্শ ও নতুন শিক্ষা"],
        "suitable_activities_hi": ["हस्तशिल्प व कारीगरी", "व्यापारिक सौदे", "चिकित्सा कार्य", "ज्योतिष परामर्श"],
    },
    # 13: Chitra
    {
        "disposition_en": "Mridu / Maitra (Soft, Artistic & Sparkling)",
        "disposition_bn": "মৃদু / মৈত্রী (নান্দনিক, উজ্জ্বল ও শিল্পমণ্ডিত)",
        "disposition_hi": "मृदु / मैत्र (कलात्मक व चमत्कारी)",
        "gunas_en": "Tamas - Tamas - Tamas", "gunas_bn": "তমঃ - তমঃ - তমঃ", "gunas_hi": "तमस - तमस - तमस",
        "caste_varna_en": "Servant / Shudra", "caste_varna_bn": "শূদ্র", "caste_varna_hi": "शूद्र",
        "gender_en": "Female", "gender_bn": "স্ত্রী", "gender_hi": "स्त्री",
        "direction_en": "West", "direction_bn": "পশ্চিম", "direction_hi": "पश्चिम",
        "sacred_bird_en": "Woodpecker", "sacred_bird_bn": "কাঠঠোকরা", "sacred_bird_hi": "कठफोड़वा",
        "suitable_activities_en": ["Architectural design", "Fashion & fine jewelry", "Photography & interior decorating", "Fine arts & sculpting"],
        "suitable_activities_bn": ["স্থাপত্য নকশা ও ইন্টেরিয়র", "ফ্যাশন ও রত্নালঙ্কার তৈরি", "ফটোগ্রাফি ও চিত্রাঙ্কন", "মূর্তি ও ভাস্কর্য নির্মাণ"],
        "suitable_activities_hi": ["वास्तु व इंटीरियर डिजाइन", "फैशन व आभूषण निर्माण", "चित्रकला व मूर्तिकला"],
    },
    # 14: Swati
    {
        "disposition_en": "Chara / Chala (Movable, Free & Flexible)",
        "disposition_bn": "চর / চল (স্বাধীন, গতিশীল ও নমনীয়)",
        "disposition_hi": "चर / चल (स्वतंत्र व गतिशील)",
        "gunas_en": "Tamas - Tamas - Sattva", "gunas_bn": "তমঃ - তমঃ - সত্ত্ব", "gunas_hi": "तमस - तमस - सत्त्व",
        "caste_varna_en": "Outcaste", "caste_varna_bn": "ম্লেচ্ছ", "caste_varna_hi": "म्लेच्छ",
        "gender_en": "Female", "gender_bn": "স্ত্রী", "gender_hi": "स्त्री",
        "direction_en": "North", "direction_bn": "উত্তর", "direction_hi": "उत्तर",
        "sacred_bird_en": "Pigeon / Honey Buzzard", "sacred_bird_bn": "পায়রা", "sacred_bird_hi": "कबूतर",
        "suitable_activities_en": ["Air travel & long journeys", "Business expansion", "Learning music", "Planting crops", "Starting dynamic ventures"],
        "suitable_activities_bn": ["বিমানযাত্রা ও দূর ভ্রমণ", "ব্যবসা সম্প্রসারণ", "সঙ্গীত চর্চা", "কৃষিকাজ ও গতিশীল উদ্যোগ"],
        "suitable_activities_hi": ["हवाई यात्रा व दूरगमन", "व्यापार विस्तार", "संगीत साधना", "गतिशील उपक्रम"],
    },
    # 15: Vishakha
    {
        "disposition_en": "Mishra / Sadharana (Mixed / Dual Goal)",
        "disposition_bn": "মিশ্র / সাধারণ (লক্ষ্যভেদী ও দ্বৈত স্বভাব)",
        "disposition_hi": "मिश्र / साधारण (लक्ष्योन्मुखी व द्विविध)",
        "gunas_en": "Tamas - Sattva - Rajas", "gunas_bn": "তমঃ - সত্ত্ব - রজঃ", "gunas_hi": "तमस - सत्त्व - रजस",
        "caste_varna_en": "Outcaste", "caste_varna_bn": "ম্লেচ্ছ", "caste_varna_hi": "म्लेच्छ",
        "gender_en": "Female", "gender_bn": "স্ত্রী", "gender_hi": "स्त्री",
        "direction_en": "East", "direction_bn": "পূর্ব", "direction_hi": "पूर्व",
        "sacred_bird_en": "Red-tailed Falcon", "sacred_bird_bn": "লাল লেজযুক্ত বাজপাখি", "sacred_bird_hi": "लाल पूंछ वाला बाज",
        "suitable_activities_en": ["Ambitious achievements", "Competitive challenges", "Entering celebrations", "Ceremonies honoring deities", "Determined focus"],
        "suitable_activities_bn": ["উচ্চাকাঙ্ক্ষী লক্ষ্য পূরণ", "কঠোর প্রতিযোগিতামূলক কাজ", "উৎসব ও পূজা উদযাপন", "স্থির সংকল্প নিয়ে কাজ শুরু"],
        "suitable_activities_hi": ["महत्वाकांक्षी लक्ष्य साधना", "प्रतियोगिता", "उत्सव व पूजन", "दृढ़ निश्चय के कार्य"],
    },
    # 16: Anuradha
    {
        "disposition_en": "Mridu / Maitra (Soft, Devotional & Friendly)",
        "disposition_bn": "মৃদু / মৈত্রী (ভক্তিপূর্ণ, কোমল ও মৈত্রীপরায়ণ)",
        "disposition_hi": "मृदु / मैत्र (भक्तिपूर्ण व सौम्य)",
        "gunas_en": "Tamas - Sattva - Tamas", "gunas_bn": "তমঃ - সত্ত্ব - তমঃ", "gunas_hi": "तमस - सत्त्व - तमस",
        "caste_varna_en": "Shudra", "caste_varna_bn": "শূদ্র", "caste_varna_hi": "शूद्र",
        "gender_en": "Male", "gender_bn": "পুরুষ", "gender_hi": "पुरुष",
        "direction_en": "South", "direction_bn": "দক্ষিণ", "direction_hi": "दक्षिण",
        "sacred_bird_en": "Nightingale / Peacock", "sacred_bird_bn": "কোকিল / ময়ূর", "sacred_bird_hi": "कोयल / मोर",
        "suitable_activities_en": ["Deep friendships & partnerships", "Spiritual retreats & yoga", "Foreign travel", "Secret research", "Healing and wellness"],
        "suitable_activities_bn": ["আন্তরিক বন্ধুত্ব ও অংশীদারি", "যোগাভ্যাস ও আধ্যাত্মিক সাধনা", "বিদেশ যাত্রা", "গুপ্ত গবেষণা ও আরোগ্য লাভ"],
        "suitable_activities_hi": ["मैत्री संबंध व साझेदारी", "योग व साधना", "विदेश यात्रा", "गुप्त शोध"],
    },
    # 17: Jyeshtha
    {
        "disposition_en": "Teekshna / Daruna (Dreadful, Senior & Protective)",
        "disposition_bn": "তীক্ষ্ণ / দারুণ (জ্যেষ্ঠ, প্রখর ও কর্তৃত্বপূর্ণ)",
        "disposition_hi": "तीक्ष्ण / दारुण (ज्येष्ठ व प्रखर)",
        "gunas_en": "Tamas - Sattva - Sattva", "gunas_bn": "তমঃ - সত্ত্ব - সত্ত্ব", "gunas_hi": "तमस - सत्त्व - सत्त्व",
        "caste_varna_en": "Farmer / Shudra", "caste_varna_bn": "শূদ্র", "caste_varna_hi": "शूद्र",
        "gender_en": "Female", "gender_bn": "স্ত্রী", "gender_hi": "स्त्री",
        "direction_en": "West", "direction_bn": "পশ্চিম", "direction_hi": "पश्चिम",
        "sacred_bird_en": "Brahminy Duck / Chakravaka", "sacred_bird_bn": "চক্রবাক পাখি", "sacred_bird_hi": "चकवा",
        "suitable_activities_en": ["Assuming authority & command", "Dispelling conspiracies", "Family administration", "Severe protective disciplines"],
        "suitable_activities_bn": ["কর্তৃত্ব ও নেতৃত্বের দায়িত্ব গ্রহণ", "ষড়যন্ত্র দমন", "পারিবারিক প্রধানের সিদ্ধান্ত", "কঠোর সুরক্ষা ব্যবস্থা গ্রহণ"],
        "suitable_activities_hi": ["नेतृत्व व अधिकार ग्रहण", "षड्यंत्रों का निवारण", "संरक्षण व प्रबंधन"],
    },
    # 18: Mula
    {
        "disposition_en": "Teekshna / Daruna (Root, Piercing & Radical)",
        "disposition_bn": "তীক্ষ্ণ / দারুণ (মৌলিক, ভেদনশীল ও আমূল পরিবর্তনকারী)",
        "disposition_hi": "तीक्ष्ण / दारुण (मूलगामी व रूपांतरकारी)",
        "gunas_en": "Sattva - Rajas - Rajas", "gunas_bn": "সত্ত্ব - রজঃ - রজঃ", "gunas_hi": "सत्त्व - रजस - रजस",
        "caste_varna_en": "Butcher / Hunter", "caste_varna_bn": "ব্যাধ", "caste_varna_hi": "व्याध",
        "gender_en": "Neuter", "gender_bn": "নপুংসক", "gender_hi": "नपुंसक",
        "direction_en": "North", "direction_bn": "উত্তর", "direction_hi": "उत्तर",
        "sacred_bird_en": "Red-crested Vulture / Cock", "sacred_bird_bn": "বনমোরগ / রক্তচূড়া শকুন", "sacred_bird_hi": "जंगली मुर्गा / गिद्ध",
        "suitable_activities_en": ["Root-cause investigation", "Herbal remedies & medicine extraction", "Agriculture & planting roots", "Tearing down old structures"],
        "suitable_activities_bn": ["মূল কারণ অনুসন্ধান", "ভেষজ ঔষধ নিষ্কাশন", "শিকড়যুক্ত গাছ রোপণ", "পুরোনো জরাজীর্ণ ব্যবস্থা ভেঙে ফেলা"],
        "suitable_activities_hi": ["मूल कारणों की खोज", "औषधि निर्माण", "कृषि कार्य", "पुरातन का विध्वंस"],
    },
    # 19: Purva Ashadha
    {
        "disposition_en": "Ugra / Krura (Invincible & Fierce)",
        "disposition_bn": "উগ্র / ক্রূর (অপরাজেয়, তেজস্বী ও জয়ী)",
        "disposition_hi": "उग्र / क्रूर (अपराजेय व प्रतापी)",
        "gunas_en": "Sattva - Rajas - Tamas", "gunas_bn": "সত্ত্ব - রজঃ - তমঃ", "gunas_hi": "सत्त्व - रजस - तमस",
        "caste_varna_en": "Brahmin", "caste_varna_bn": "ব্রাহ্মণ", "caste_varna_hi": "ब्राह्मण",
        "gender_en": "Female", "gender_bn": "স্ত্রী", "gender_hi": "स्त्री",
        "direction_en": "East", "direction_bn": "পূর্ব", "direction_hi": "पूर्व",
        "sacred_bird_en": "Francolin / Partridge", "sacred_bird_bn": "তিতির পাখি", "sacred_bird_hi": "तीतर",
        "suitable_activities_en": ["Overcoming obstacles", "Water purification & marine ventures", "Inspiring mass movements", "Debating adversaries"],
        "suitable_activities_bn": ["কঠিন বাধা অতিক্রম", "জলসম্পদ ও নৌ-বাণিজ্য", "জনগণকে উদ্বুদ্ধকরণ", "তর্কযুদ্ধে বিজয়"],
        "suitable_activities_hi": ["बाधाओं पर विजय", "जल संसाधन व नौकायन", "जनता को प्रेरित करना", "वाद-विवाद"],
    },
    # 20: Uttara Ashadha
    {
        "disposition_en": "Dhruva / Sthira (Fixed, Regal & Victorious)",
        "disposition_bn": "ধ্রুব / স্থির (স্থায়ী, বিশ্বজনীন ও চূড়ান্ত বিজয়ী)",
        "disposition_hi": "ध्रुव / स्थिर (स्थायी व अंतिम विजयी)",
        "gunas_en": "Sattva - Rajas - Sattva", "gunas_bn": "সত্ত্ব - রজঃ - সত্ত্ব", "gunas_hi": "सत्त्व - रजस - सत्त्व",
        "caste_varna_en": "Kshatriya", "caste_varna_bn": "ক্ষত্রিয়", "caste_varna_hi": "क्षत्रिय",
        "gender_en": "Female", "gender_bn": "স্ত্রী", "gender_hi": "स्त्री",
        "direction_en": "South", "direction_bn": "দক্ষিণ", "direction_hi": "दक्षिण",
        "sacred_bird_en": "Stork", "sacred_bird_bn": "সারস পাখি", "sacred_bird_hi": "सारस",
        "suitable_activities_en": ["Laying permanent foundations", "Signing solemn pledges", "Coronations and appointments", "Founding organizations"],
        "suitable_activities_bn": ["স্থায়ী ভিত্তিপ্রস্তর স্থাপন", "গুরুত্বপূর্ণ চুক্তি সম্পাদন", "নতুন পদে দায়িত্ব গ্রহণ", "দীর্ঘস্থায়ী সংগঠন প্রতিষ্ঠা"],
        "suitable_activities_hi": ["स्थायी नींव रखना", "शपथ ग्रहण", "नई संस्थाओं की स्थापना", "दीर्घकालिक अनुबंध"],
    },
    # 21: Shravana
    {
        "disposition_en": "Chara / Chala (Movable, Receptive & Learning)",
        "disposition_bn": "চর / চল (শ্রবণশীল, গতিশীল ও জ্ঞানময়)",
        "disposition_hi": "चर / चल (श्रवणशील व ज्ञानवान)",
        "gunas_en": "Sattva - Tamas - Rajas", "gunas_bn": "সত্ত্ব - তমঃ - রজঃ", "gunas_hi": "सत्त्व - तमस - रजस",
        "caste_varna_en": "Outcaste", "caste_varna_bn": "ম্লেচ্ছ", "caste_varna_hi": "म्लेच्छ",
        "gender_en": "Female", "gender_bn": "স্ত্রী", "gender_hi": "स्त्री",
        "direction_en": "West", "direction_bn": "পশ্চিম", "direction_hi": "पश्चिम",
        "sacred_bird_en": "Curlew / Francolin", "sacred_bird_bn": "কাদাখোঁচা পাখি", "sacred_bird_hi": "कुररी / जलपक्षी",
        "suitable_activities_en": ["Listening to wisdom & discourses", "Studying languages", "University admissions", "Counseling & public speaking"],
        "suitable_activities_bn": ["জ্ঞানগর্ভ উপদেশ শ্রবণ", "ভাষা শিক্ষা ও উচ্চশিক্ষা", "বিশ্ববিদ্যালয়ে ভর্তি", "কাউন্সেলিং ও বক্তব্য প্রদান"],
        "suitable_activities_hi": ["ज्ञानोपदेश श्रवण", "उच्च शिक्षा व भाषा ज्ञान", "परामर्श व व्याख्यान"],
    },
    # 22: Dhanishta
    {
        "disposition_en": "Chara / Chala (Movable, Musical & Wealthy)",
        "disposition_bn": "চর / চল (সঙ্গীতময়, সুরসমৃদ্ধ ও ধনশালী)",
        "disposition_hi": "चर / चल (संगीतमय व धनवान)",
        "gunas_en": "Sattva - Tamas - Tamas", "gunas_bn": "সত্ত্ব - তমঃ - তমঃ", "gunas_hi": "सत्त्व - तमस - तमस",
        "caste_varna_en": "Servant / Shudra", "caste_varna_bn": "শূদ্র", "caste_varna_hi": "शूद्र",
        "gender_en": "Female", "gender_bn": "স্ত্রী", "gender_hi": "स्त्री",
        "direction_en": "North", "direction_bn": "উত্তর", "direction_hi": "उत्तर",
        "sacred_bird_en": "Golden Bee / Peacock", "sacred_bird_bn": "স্বর্ণালী মৌমাছি / ময়ূর", "sacred_bird_hi": "स्वर्ण मधुमक्खी / मोर",
        "suitable_activities_en": ["Musical performances", "Buying real estate & gems", "Team building & celebrations", "Martial leadership"],
        "suitable_activities_bn": ["সঙ্গীত ও নৃত্যকলা অনুষ্ঠান", "রিয়েল এস্টেট ও রত্ন ক্রয়", "দলগত নেতৃত্ব ও উৎসব উদযাপন", "বীরত্বপূর্ণ কর্ম"],
        "suitable_activities_hi": ["संगीत व वाद्य यंत्र", "संपत्ति व आभूषण क्रय", "सामूहिक आयोजन व उत्सव"],
    },
    # 23: Shatabhisha
    {
        "disposition_en": "Chara / Chala (Movable, Healing & Hundred Stars)",
        "disposition_bn": "চর / চল (নিরাময়কারী, গোপন ও শতভিষক)",
        "disposition_hi": "चर / चल (आरोग्यकारी व रहस्यमयी)",
        "gunas_en": "Sattva - Tamas - Sattva", "gunas_bn": "সত্ত্ব - তমঃ - সত্ত্ব", "gunas_hi": "सत्त्व - तमस - सत्त्व",
        "caste_varna_en": "Butcher / Hunter", "caste_varna_bn": "ব্যাধ", "caste_varna_hi": "व्याध",
        "gender_en": "Neuter", "gender_bn": "নপুংসক", "gender_hi": "नपुंसक",
        "direction_en": "South", "direction_bn": "দক্ষিণ", "direction_hi": "दक्षिण",
        "sacred_bird_en": "Black Raven", "sacred_bird_bn": "দাঁড়কাক", "sacred_bird_hi": "काला कौआ",
        "suitable_activities_en": ["Administering medicines & therapy", "Meditation in solitude", "Scientific research", "Astronomy & space science"],
        "suitable_activities_bn": ["জটিল রোগের চিকিৎসা ও থেরাপি", "নিভৃত ধ্যান", "বৈজ্ঞানিক গবেষণা", "জ্যোতির্বিজ্ঞান ও প্রযুক্তি"],
        "suitable_activities_hi": ["चिकित्सा व प्राकृतिक उपचार", "एकांत ध्यान", "वैज्ञानिक शोध"],
    },
    # 24: Purva Bhadrapada
    {
        "disposition_en": "Ugra / Krura (Fierce, Transformative & Ascetic)",
        "disposition_bn": "উগ্র / ক্রূর (তীব্র, রূপান্তরমূলক ও তপস্বী)",
        "disposition_hi": "उग्र / क्रूर (तपस्वी व रूपांतरकारी)",
        "gunas_en": "Sattva - Sattva - Rajas", "gunas_bn": "সত্ত্ব - সত্ত্ব - রজঃ", "gunas_hi": "সत्त्व - सत्त्व - रजस",
        "caste_varna_en": "Brahmin", "caste_varna_bn": "ব্রাহ্মণ", "caste_varna_hi": "ब्राह्मण",
        "gender_en": "Male", "gender_bn": "পুরুষ", "gender_hi": "पुरुष",
        "direction_en": "West", "direction_bn": "পশ্চিম", "direction_hi": "पश्चिम",
        "sacred_bird_en": "Pelican", "sacred_bird_bn": "গগনভেড়ী পাখি", "sacred_bird_hi": "हवासील / पेलिकन",
        "suitable_activities_en": ["Tantric disciplines", "Renunciation and intense study", "Confronting darkness", "Spiritual austerities"],
        "suitable_activities_bn": ["তপস্যা ও গভীর ধ্যান", "ত্যাগ ও শাস্ত্রীয় গভীর গবেষণা", "কঠিন পরিস্থিতি মোকাবেলা", "আত্মসমর্পণ"],
        "suitable_activities_hi": ["तपस्या व ध्यान", "गहन अध्ययन", "अंधकार पर विजय", "आध्यात्मिक वैराग्य"],
    },
    # 25: Uttara Bhadrapada
    {
        "disposition_en": "Dhruva / Sthira (Fixed, Wise & Deep Oceanic)",
        "disposition_bn": "ধ্রুব / স্থির (স্থায়ী, প্রাজ্ঞ ও অতল সমুদ্রবৎ গম্ভীর)",
        "disposition_hi": "ध्रुव / स्थिर (गंभीर व प्रज्ञावान)",
        "gunas_en": "Sattva - Sattva - Tamas", "gunas_bn": "সত্ত্ব - সত্ত্ব - তমঃ", "gunas_hi": "সत्त्व - सत्त्व - तमस",
        "caste_varna_en": "Kshatriya", "caste_varna_bn": "ক্ষত্রিয়", "caste_varna_hi": "क्षत्रिय",
        "gender_en": "Male", "gender_bn": "পুরুষ", "gender_hi": "पुरुष",
        "direction_en": "North", "direction_bn": "উত্তর", "direction_hi": "उत्तर",
        "sacred_bird_en": "Kotwal / King Crow", "sacred_bird_bn": "ফিঙে পাখি", "sacred_bird_hi": "कोतवाल / भुजंग",
        "suitable_activities_en": ["Deep contemplation", "Founding spiritual institutions", "Long-term investments", "Charity and water conservation"],
        "suitable_activities_bn": ["গভীর আত্মানুসন্ধান", "আধ্যাত্মিক আশ্রম বা প্রতিষ্ঠান স্থাপন", "দীর্ঘমেয়াদী নিরাপদ সঞ্চয়", "জল ও পরিবেশ সংরক্ষণ"],
        "suitable_activities_hi": ["गहन चिंतन", "आध्यात्मिक संस्थापन", "दीर्घकालिक निवेश", "परोपकार"],
    },
    # 26: Revati
    {
        "disposition_en": "Mridu / Maitra (Soft, Nourishing & Compassionate)",
        "disposition_bn": "মৃদু / মৈত্রী (কোমল, পুষ্টিকর, দয়ালু ও রক্ষক)",
        "disposition_hi": "मृदु / मैत्र (कोमल व दयालु)",
        "gunas_en": "Sattva - Sattva - Sattva", "gunas_bn": "সত্ত্ব - সত্ত্ব - সত্ত্ব", "gunas_hi": "সत्त्व - सत्त्व - सत्त्व",
        "caste_varna_en": "Shudra", "caste_varna_bn": "শূদ্র", "caste_varna_hi": "शूद्र",
        "gender_en": "Female", "gender_bn": "স্ত্রী", "gender_hi": "स्त्री",
        "direction_en": "East", "direction_bn": "পূর্ব", "direction_hi": "पूर्व",
        "sacred_bird_en": "Kestrel / Indian Robin", "sacred_bird_bn": "দোয়েল পাখি", "sacred_bird_hi": "कस्तूरी / दयाल पक्षी",
        "suitable_activities_en": ["Travel and sea voyages", "Adoption and child protection", "Fine arts & music", "Gemstone purchase", "Spiritual devotion"],
        "suitable_activities_bn": ["নিরাপদ ভ্রমণ ও নৌযাত্রা", "সন্তান দত্তক গ্রহণ ও শিশুদের সাহায্য", "সঙ্গীত ও সুকুমার শিল্প চর্চা", "রত্নপাথর ধারণ"],
        "suitable_activities_hi": ["सुखद यात्रा व जलयात्रा", "बाल कल्याण", "ललित कला व संगीत", "रत्न धारण"],
    },
]

def get_nakshatra_disposition(nak_idx: int) -> dict[str, Any]:
    """Returns classical disposition, gunas, bird, direction, and suitable activities for the nakshatra."""
    return DISPOSITIONS_MASTER[nak_idx % 27]

