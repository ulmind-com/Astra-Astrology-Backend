"""Multilingual translations for all 12 Rashis (Moon Signs):
English (en), Bengali (bn), Hindi (hi) covering:
- Overview
- Strengths
- Cautions & Pitfalls (কী কী থেকে সাবধান থাকবেন / सावधानियां)
- Beneficial Remedies & Actions (কী করলে ভালো হবে / शुभ उपाय)
- Element, Modality, Polarity, Body Governance
- Lucky Gemstone, Colors, Day, Deity, Career Fields
"""

RASHI_TRANSLATIONS: dict[int, dict[str, dict]] = {
    # -------------------------------------------------------------------------
    # 0. ARIES (মেষ / मेष)
    # -------------------------------------------------------------------------
    0: {
        "en": {
            "name": "Aries",
            "element": "Fiery",
            "modality": "Movable / Cardinal",
            "polarity": "Masculine / Positive (Odd sign)",
            "body_parts": "Head, brain, forehead, skull, cranial vessels",
            "nature": "Dynamic, enterprising, valiant, energetic, impulsive, leadership-driven",
            "overview": (
                "Ruled by Mars, Aries represents the spark of life and initial impulse. "
                "Individuals with Moon in Aries are natural pioneers who thrive on action, challenges, "
                "and courageous initiatives. They possess a lean physique, prominent forehead, sharp gaze, "
                "and spontaneous enthusiasm."
            ),
            "strengths": [
                "Fearless leadership and pioneering initiative",
                "High stamina, quick problem solving, and determination",
                "Honest, direct, and straightforward communication",
                "Protective towards dependents and team members",
            ],
            "cautions_and_pitfalls": [
                "Hot temper, rash irritability, and speaking without forethought",
                "Impulsive financial gambles and leaping before looking",
                "Starting many ambitious projects but losing momentum halfway through",
                "Prone to headaches, migraines, fevers, and face/head injuries due to rush",
                "Inability to accept delays, advice, or subordination gracefully",
            ],
            "beneficial_actions_and_remedies": [
                "Daily morning meditation or slow breathwork (Pranayama) to cool Mars fire",
                "Recite Hanuman Chalisa or Kartikeya Stotra on Tuesdays for mental calm",
                "Channel intense energy into sports, martial arts, gym, or executive management",
                "Donate red lentils (masoor dal), copper vessels, or sweet jaggery on Tuesdays",
                "Practice pausing for 10 seconds before reacting in heated arguments",
            ],
            "career_fields": [
                "Defense, police, military & security",
                "Surgery, medicine & emergency services",
                "Entrepreneurship, venture capital & startup leadership",
                "Engineering, mechanics, real estate & construction",
                "Athletics, competitive sports & sports training",
            ],
            "lucky_color": "Crimson Red, Coral & Saffron",
            "lucky_gemstone": "Red Coral (Moonga)",
            "lucky_day": "Tuesday",
            "ruling_deity": "Lord Hanuman & Lord Kartikeya",
            "compatible_rashis": ["Leo", "Sagittarius", "Gemini", "Aquarius"],
        },
        "bn": {
            "name": "মেষ",
            "element": "অগ্নি তত্ত্ব",
            "modality": "চর রাশি (Movable)",
            "polarity": "পুরুষ / ধনাত্মক (বিষম রাশি)",
            "body_parts": "মাথা, মস্তিষ্ক, কপাল, খুলি এবং রক্তনালী",
            "nature": "উদ্যমী, সাহসী, পরাক্রমশালী, স্পষ্টভাষী, নেতৃত্বমুখী ও তেজস্বী",
            "overview": (
                "মঙ্গল গ্রহ দ্বারা শাসিত মেষ রাশি হলো জীবনের সূচনা ও প্রাণশক্তির প্রতীক। "
                "মেষ রাশির জাতক-জাতিকারা জন্মগতভাবে অগ্রদূত ও নির্ভীক হয়ে থাকেন। তারা যে কোনো চ্যালেঞ্জ গ্রহণ করতে ভালোবাসেন "
                "এবং যেকোনো কাজে দ্রুত নেতৃত্ব দিতে পারেন।"
            ),
            "strengths": [
                "নির্ভীক নেতৃত্বদান এবং যেকোনো কাজে তাৎক্ষণিক অগ্রণী ভূমিকা গ্রহণ",
                "উচ্চ শারীরিক সহনশীলতা, প্রত্যুৎপন্নমতিত্ব এবং দৃঢ় সংকল্প",
                "সরাসরি, অকপট এবং সত্যবাদী কথাবার্তা",
                "অধীনস্থ ও দুর্বল মানুষদের রক্ষা করার আন্তরিক মনোভাব",
            ],
            "cautions_and_pitfalls": [
                "উগ্র মেজাজ, দ্রুত রেগে যাওয়া এবং চিন্তা না করে হঠাৎ কথা বলা থেকে সাবধান",
                "যাচাই না করে হুটহাট ঝুঁকিপূর্ণ আর্থিক সিদ্ধান্ত বা ফাটকা ব্যবসায় জড়ানো",
                "একসাথে একাধিক কাজ শুরু করে মাঝপথে ধৈর্য ও উৎসাহ হারিয়ে ফেলা",
                "অতিরিক্ত তাড়াহুড়ো ও অস্থিরতার কারণে মাথা বা মুখে আঘাতের ঝুঁকি",
                "কাজে অনাকাঙ্ক্ষিত দেরি, অন্যের ভালো উপদেশ বা অধীনতা সহজে মেনে নিতে না পারা",
            ],
            "beneficial_actions_and_remedies": [
                "প্রতিদিন সকালে প্রাণায়াম ও ধ্যানের মাধ্যমে মনের অতিরিক্ত উত্তেজনা শান্ত রাখুন",
                "প্রতি মঙ্গলবার ভক্তিভরে শ্রী হনুমান চালিসা বা কার্তিকেয় স্তোত্র পাঠ করুন",
                "অতিরিক্ত শারীরিক শক্তিকে শরীরচর্চা, যোগাসন বা গঠনমূলক কাজে নিয়োজিত করুন",
                "মঙ্গলবার লাল মুসুর ডাল, তামার সামগ্রী বা লাল মিষ্টান্ন অভাবীদের দান করুন",
                "উত্তেজিত পরিস্থিতিতে তাৎক্ষণিক প্রতিক্রিয়া না জানিয়ে অন্তত ১০ সেকেন্ড শান্ত থাকুন",
            ],
            "career_fields": [
                "প্রতিরক্ষা, পুলিশ, সেনাবহিনী ও নিরাপত্তা বিভাগ",
                "শল্যচিকিৎসা (সার্জারি), চিকিৎসাবিজ্ঞান ও জরুরি স্বাস্থ্যসেবা",
                "উদ্যোক্তা, স্টার্টআপ নেতৃত্ব ও ব্যবসা প্রশাসন",
                "মেকানিক্যাল ইঞ্জিনিয়ারিং, রিয়েল এস্টেট ও নির্মাণশিল্প",
                "ক্রীড়া, অ্যাথলেটিক্স ও সামরিক প্রশিক্ষণ",
            ],
            "lucky_color": "গাঢ় লাল, প্রবাল ও জাফরান",
            "lucky_gemstone": "রক্ত প্রবাল (Red Coral)",
            "lucky_day": "মঙ্গলবার",
            "ruling_deity": "ভগবান হনুমান ও কার্তিকেয়",
            "compatible_rashis": ["সিংহ", "ধনু", "মিথুন", "কুম্ভ"],
        },
        "hi": {
            "name": "मेष",
            "element": "अग्नि तत्व",
            "modality": "चर राशि (Movable)",
            "polarity": "पुरुष / धनात्मक (विषम राशि)",
            "body_parts": "मस्तिष्क, सिर, ललाट, कपाल और रक्त वाहिकाएं",
            "nature": "ऊर्जावान, साहसी, पराक्रमी, स्पष्टवादी, नेतृत्व-कुशल एवं ओजस्वी",
            "overview": (
                "मंगल ग्रह द्वारा शासित मेष राशि जीवन की ऊर्जा और साहस का प्रतीक है। "
                "मेष राशि के जातक जन्मजात रूप से साहसी और किसी भी कार्य में अग्रणी भूमिका निभाने वाले होते हैं। "
                "वे चुनौतियों का डटकर मुकाबला करते हैं और स्वतंत्र विचार रखते हैं।"
            ),
            "strengths": [
                "निर्भीक नेतृत्व और कठिन परिस्थितियों में तुरंत निर्णय लेने की क्षमता",
                "उच्च शारीरिक ऊर्जा, त्वरित समाधान और अटूट संकल्प शक्ति",
                "स्पष्ट, ईमानदार और सच्चा व्यवहार",
                "आश्रितों और साथियों की रक्षा करने की स्वाभाविक भावना",
            ],
            "cautions_and_pitfalls": [
                "उग्र स्वभाव, शीघ्र क्रोधित होना और बिना सोचे-समझे कटु वचन बोलने से बचें",
                "जल्दबाजी में वित्तीय जोखिम या सट्टेबाजी के मामलों में नुकसान उठाना",
                "अनेक कार्य एक साथ शुरू करके बीच में ही उत्साह खो देना",
                "जल्दबाजी के कारण सिरदर्द, माइग्रेन या सिर-चेहरे पर चोट का जोखिम",
                "काम में देरी, दूसरों की नेक सलाह या किसी के अधीन काम करने में असहज होना",
            ],
            "beneficial_actions_and_remedies": [
                "प्रतिदिन सुबह प्राणायाम और ध्यान द्वारा मानसिक शांति बनाए रखें",
                "प्रत्येक मंगलवार को श्री हनुमान चालीसा या सुंदरकांड का पाठ करें",
                "अतिरिक्त ऊर्जा को खेलकूद, व्यायाम या रचनात्मक कार्यों में लगाएं",
                "मंगलवार को लाल मसूर की दाल, तांबे का बर्तन या गुड़ का दान करें",
                "क्रोध या विवाद की स्थिति में तुरंत बोलने के बजाय १० सेकंड मौन रहें",
            ],
            "career_fields": [
                "सेना, पुलिस, रक्षा एवं सुरक्षा सेवाएं",
                "शल्य चिकित्सा (सर्जरी), चिकित्सा एवं आपातकालीन सेवाएं",
                "उद्यमिता, व्यापारिक नेतृत्व एवं स्टार्टअप",
                "मैकेनिकल इंजीनियरिंग, निर्माण एवं रियल एस्टेट",
                "खेलकूद, एथलेटिक्स एवं सुरक्षा परामर्श",
            ],
            "lucky_color": "गहरा लाल, मूंगा रंग एवं केसरिया",
            "lucky_gemstone": "लाल मूंगा (Red Coral)",
            "lucky_day": "मंगलवार",
            "ruling_deity": "भगवान श्री हनुमान एवं कार्तिकेय",
            "compatible_rashis": ["सिंह", "धनु", "मिथुन", "कुंभ"],
        },
    },

    # -------------------------------------------------------------------------
    # 1. TAURUS (বৃষ / वृषभ)
    # -------------------------------------------------------------------------
    1: {
        "en": {
            "name": "Taurus",
            "element": "Earthy",
            "modality": "Fixed / Static",
            "polarity": "Feminine / Negative (Even sign)",
            "body_parts": "Face, neck, throat, vocal cords, thyroid, chin",
            "nature": "Stable, loyal, patient, luxury-loving, artistic, dependable, methodical",
            "overview": (
                "Ruled by Venus, Taurus embodies stability, endurance, and sensual beauty. "
                "Those with Moon in Taurus have a peaceful demeanor, attractive face, fine teeth, and "
                "an eye for aesthetics. They value financial security, domestic comfort, and lasting loyalty."
            ),
            "strengths": [
                "Rock-solid dependability, patience, and loyalty",
                "Superb financial planning and resource management",
                "Refined taste in fine arts, music, culinary delights, and luxury",
                "Calm resilience under pressure and steadfast endurance",
            ],
            "cautions_and_pitfalls": [
                "Extreme stubbornness and resistance to necessary modern changes",
                "Overindulgence in heavy food, sweets, and material luxuries",
                "Tendency towards sluggishness, procrastination, and physical lethargy",
                "Possessiveness and insecurity in emotional relationships",
                "Vulnerability to throat infections, vocal strain, and thyroid imbalances",
            ],
            "beneficial_actions_and_remedies": [
                "Embrace flexibility and practice letting go of rigid mental stances",
                "Worship Goddess Mahalakshmi on Fridays; offer white flowers and kheer",
                "Regular throat gargling and vocal care; spend time in lush gardens/nature",
                "Donate white garments, rice, dairy products, or silver items on Fridays",
                "Incorporate light cardio and outdoor walking into your daily routine",
            ],
            "career_fields": [
                "Banking, financial advisory, wealth management & accounting",
                "Fashion, jewelry, cosmetics, beauty & interior design",
                "Culinary arts, restaurant business, hospitality & luxury hotels",
                "Music, singing, fine arts & voice artistry",
                "Agriculture, horticulture & luxury real estate",
            ],
            "lucky_color": "White, Cream, Pearl & Rose Pink",
            "lucky_gemstone": "Diamond (Heera) or White Sapphire",
            "lucky_day": "Friday",
            "ruling_deity": "Goddess Lakshmi",
            "compatible_rashis": ["Virgo", "Capricorn", "Cancer", "Pisces"],
        },
        "bn": {
            "name": "বৃষ",
            "element": "পৃথ্বী তত্ত্ব (Earth)",
            "modality": "স্থির রাশি (Fixed)",
            "polarity": "স্ত্রী / ঋণাত্মক (সম রাশি)",
            "body_parts": "মুখমণ্ডল, গলা, কণ্ঠনালী, থাইরয়েড ও চিবুক",
            "nature": "ধৈর্যশীল, বিশ্বস্ত, শান্ত, সৌন্দর্যপ্রিয়, বাস্তববাদী ও নির্ভরযোগ্য",
            "overview": (
                "শুক্র গ্রহের শাসনাধীন বৃষ রাশি স্থায়িত্ব, সৌন্দর্য ও সমৃদ্ধির প্রতীক। "
                "বৃষ রাশির জাতক-জাতিকাদের ব্যক্তিত্ব শান্ত ও সৌম্য। তারা আর্থিক নিরাপত্তা, পারিবারিক শান্তি "
                "এবং রুচিশীল জীবনযাপন পছন্দ করেন।"
            ),
            "strengths": [
                "অটল ধৈর্য, নির্ভরযোগ্যতা এবং আজীবন অটুট আনুগত্য",
                "উচ্চমানের অর্থনৈতিক পরিকল্পনা ও সম্পদ সঞ্চয় করার অসাধারণ ক্ষমতা",
                "শিল্পকলা, সংগীত, রসনা বিলাস ও সৌন্দর্যের গভীর সমঝদার",
                "যেকোনো প্রতিকূল পরিস্থিতিতেও শান্ত থেকে পরিস্থিতি সামলানোর ক্ষমতা",
            ],
            "cautions_and_pitfalls": [
                "চরম একগুঁয়ে মনোভাব এবং প্রয়োজনীয় গঠনমূলক পরিবর্তনকে অস্বীকার করা",
                "অতিরিক্ত মিষ্টি, গুরুপাক খাদ্য এবং অলস বিলাসবহুল অভ্যাসে আসক্তি",
                "কাজে দীর্ঘসূত্রতা, আলস্য এবং শারীরিক স্থবিরতার প্রবণতা",
                "সম্পর্কের ক্ষেত্রে অতিরিক্ত অধিকারবোধ ও নিরাপত্তাহীনতায় ভোগা",
                "গলা ও শ্বাসনালীর সংক্রমণ, থাইরয়েড ও কণ্ঠস্বরের দুর্বলতা থেকে সাবধান",
            ],
            "beneficial_actions_and_remedies": [
                "মানসিক নমনীয়তা বৃদ্ধি করুন এবং অন্যের যৌক্তিক মতামতের প্রতি শ্রদ্ধাশীল হন",
                "প্রতি শুক্রবার মা মহালক্ষ্মীর আরাধনা করুন এবং সাদা ফুল বা পায়েস নিবেদন করুন",
                "কণ্ঠের যত্ন নিন এবং মানসিক প্রশান্তির জন্য সুদৃশ্য বাগান ও প্রকৃতির সান্নিধ্যে সময় কাটান",
                "শুক্রবার সাদা পোশাক, চাল, দুধ বা মিষ্টান্ন অভাবীদের দান করুন",
                "দৈনিক নিয়মিত প্রাতঃভ্রমণ ও শরীরচর্চা করুন যাতে অলসতা দূর হয়",
            ],
            "career_fields": [
                "ব্যাংকিং, ফিন্যান্সিয়াল প্ল্যানিং ও সম্পদ ব্যবস্থাপনা",
                "ফ্যাশন, জুয়েলারি, কসমেটিকস ও ইন্টেরিয়র ডিজাইন",
                "হোটেল ম্যানেজমেন্ট, ক্যাটারিং ও খাদ্যপণ্য ব্যবসা",
                "সংগীত, চারুকলা, কন্ঠশিল্পী ও বিজ্ঞাপন জগৎ",
                "কৃষিশিল্প, নার্সারি ও আবাসন (রিয়েল এস্টেট)",
            ],
            "lucky_color": "দুধসাদা, ক্রিম, মুক্তা ও হালকা গোলাপি",
            "lucky_gemstone": "হীরক (Diamond) বা সাদা অপাল",
            "lucky_day": "শুক্রবার",
            "ruling_deity": "দেবী মহালক্ষ্মী",
            "compatible_rashis": ["কন্যা", "মকর", "কর্কট", "মীন"],
        },
        "hi": {
            "name": "वृषभ",
            "element": "पृथ्वी तत्व",
            "modality": "स्थिर राशि (Fixed)",
            "polarity": "स्त्री / ऋणात्मक (सम राशि)",
            "body_parts": "मुख, गला, कंठ, थायरॉयड ग्रंथि और ठोड़ी",
            "nature": "धैर्यवान, निष्ठावान, शांत, कलाप्रिय, व्यावहारिक और सुदृढ़",
            "overview": (
                "शुक्र देव द्वारा शासित वृषभ राशि स्थिरता, सौंदर्य और सुख-समृद्धि का प्रतीक है। "
                "वृषभ राशि के जातक शांत स्वभाव, आकर्षक व्यक्तित्व और व्यावहारिक सोच वाले होते हैं। "
                "वे जीवन में आर्थिक सुरक्षा और पारिवारिक सामंजस्य को सर्वोच्च प्राथमिकता देते हैं।"
            ),
            "strengths": [
                "अटूट धैर्य, विश्वसनीयता और जीवनपर्यंत निभाने वाली वफादारी",
                "उत्कृष्ट वित्तीय समझ और संपत्ति संचय करने की अद्भुत कला",
                "संगीत, ललित कला, उत्तम भोजन और विलासिता के पारखी",
                "दबाव और विपरीत परिस्थितियों में भी शांत रहकर कार्य करने की क्षमता",
            ],
            "cautions_and_pitfalls": [
                "अत्यधिक जिद्दी स्वभाव और आवश्यक बदलावों का विरोध करने से बचें",
                "अत्यधिक गरिष्ठ भोजन, मिष्ठान्न और शारीरिक आलस्य में लिप्तता",
                "काम को टालने की आदत और अत्यधिक सुस्ती का शिकार होना",
                "पारिवारिक या प्रेम संबंधों में अत्यधिक अधिकार जताना",
                "गले के संक्रमण, आवाज में खराश और थायरॉयड की समस्याओं के प्रति सतर्क रहें",
            ],
            "beneficial_actions_and_remedies": [
                "अपने विचारों में लचीलापन लाएं और दूसरों की राय का भी सम्मान करें",
                "शुक्रवार को माता महालक्ष्मी की पूजा करें और सफेद पुष्प या खीर अर्पित करें",
                "गले की उचित देखभाल करें और प्राकृतिक उद्यानों में समय व्यतीत करें",
                "शुक्रवार को सफेद वस्त्र, चावल, दूध, मिश्री या चांदी की वस्तु का दान करें",
                "दैनिक जीवन में सुबह की सैर और हल्का व्यायाम अनिवार्य रूप से शामिल करें",
            ],
            "career_fields": [
                "बैंकिंग, वित्तीय परामर्श एवं धन प्रबंधन",
                "फैशन डिजाइनिंग, आभूषण, सौंदर्य प्रसाधन एवं इंटीरियर डिजाइन",
                "होटल प्रबंधन, खाद्य उद्योग एवं रेस्तरां व्यवसाय",
                "संगीत, गायन, अभिनय एवं कलात्मक क्षेत्र",
                "कृषि, बागवानी एवं रियल एस्टेट",
            ],
            "lucky_color": "सफेद, क्रीम, मोती जैसा रंग एवं हल्का गुलाबी",
            "lucky_gemstone": "हीरा (Diamond) या सफेद पुखराज",
            "lucky_day": "शुक्रवार",
            "ruling_deity": "माता महालक्ष्मी",
            "compatible_rashis": ["कन्या", "मकर", "कर्क", "मीन"],
        },
    },

    # -------------------------------------------------------------------------
    # 2. GEMINI (মিথুন / मिथुन)
    # -------------------------------------------------------------------------
    2: {
        "en": {
            "name": "Gemini",
            "element": "Airy",
            "modality": "Dual / Common",
            "polarity": "Masculine / Positive (Odd sign)",
            "body_parts": "Shoulders, arms, hands, respiratory system, nervous system",
            "nature": "Intellectual, witty, communicative, curious, versatile, social",
            "overview": (
                "Ruled by Mercury, Gemini is the master of communication, intellect, and versatility. "
                "Moon in Gemini bestows a youthful appearance, curious eyes, eloquent speech, and "
                "an agile mind that absorbs knowledge like a sponge. They excel in networking, writing, "
                "and information exchange."
            ),
            "strengths": [
                "Brilliant conversationalist and sharp verbal acumen",
                "Quick mental adaptability and capacity to multitask",
                "Insatiable curiosity and fast learning curve",
                "Youthful zest, humor, and friendly interpersonal charm",
            ],
            "cautions_and_pitfalls": [
                "Restless mind leading to chronic anxiety and nervous exhaustion",
                "Indecision and scattering energy across too many half-done ideas",
                "Superficial interest without drilling down to mastery",
                "Tendency to gossip or change commitments abruptly",
                "Respiratory sensitivities, bronchial congestion, and sleep irregularity",
            ],
            "beneficial_actions_and_remedies": [
                "Practice single-tasking; complete one project before starting the next",
                "Chant Lord Ganesha Mantras (`Om Gan Ganapataye Namaha`) on Wednesdays",
                "Feed green grass or spinach to cows; donate books or stationery to students",
                "Daily breathwork (Anulom-Vilom Pranayama) to calm overstimulated nerves",
                "Maintain a written gratitude journal to anchor scattered thoughts",
            ],
            "career_fields": [
                "Journalism, media, content writing, publishing & broadcasting",
                "Software engineering, IT, telecommunications & data networks",
                "Marketing, public relations, sales & advertising",
                "Teaching, linguistics, translation & corporate training",
                "Trade, commerce, brokerage & diplomacy",
            ],
            "lucky_color": "Emerald Green, Light Yellow & Mint",
            "lucky_gemstone": "Emerald (Panna)",
            "lucky_day": "Wednesday",
            "ruling_deity": "Lord Ganesha & Lord Vishnu",
            "compatible_rashis": ["Libra", "Aquarius", "Aries", "Leo"],
        },
        "bn": {
            "name": "মিথুন",
            "element": "বায়ু তত্ত্ব (Air)",
            "modality": "দ্বিস্বভাব রাশি (Dual)",
            "polarity": "পুরুষ / ধনাত্মক (বিষম রাশি)",
            "body_parts": "কাঁধ, হাত, বাহু, শ্বাসযন্ত্র ও স্নায়ুতন্ত্র",
            "nature": "বুদ্ধিদীপ্ত, কৌতূহলী, বাগ্মী, চঞ্চল, রসিক ও বহুমুখী প্রতিভাধর",
            "overview": (
                "বুধ গ্রহের শাসনাধীন মিথুন রাশি যোগাযোগ, প্রজ্ঞা ও বুদ্ধিমত্তার প্রতীক। "
                "মিথুন রাশির জাতক-জাতিকারা সদা তরুণ ও প্রাণবন্ত। তাদের তীক্ষ্ণ মেধা ও বাকপটুতার কারণে তারা সহজে যেকোনো "
                "মহলে মধ্যমণি হয়ে উঠতে পারেন।"
            ),
            "strengths": [
                "অসাধারণ বাকপটুতা ও যেকোনো আসর মাতিয়ে তোলার ক্ষমতা",
                "দ্রুত নতুন বিষয় শেখার প্রতিভা ও বহুমুখী কর্মদক্ষতা",
                "তীব্র কৌতূহল এবং তথ্য আহরণ ও বিশ্লেষণের বিশেষ ক্ষমতা",
                "মিষ্টভাষী, রসিক এবং সহজ-সরল সামাজিক মেলামেশা",
            ],
            "cautions_and_pitfalls": [
                "অস্থির মন, অতিরিক্ত দুশ্চিন্তা এবং মানসিক অবসাদের ঝুঁকি থেকে সাবধান",
                "একসাথে অনেক বিষয়ে মনোযোগ ছড়িয়ে দিয়ে কোনো একটিও সম্পন্ন না করা",
                "গভীরভাবে কোনো বিষয় না জেনে কেবল ভাসা-ভাসা তথ্যের উপর নির্ভর করা",
                "কথা দিয়ে কথা না রাখা বা সিদ্ধান্ত ঘন ঘন বদলানোর প্রবণতা",
                "শ্বাসনালীর সংবেদনশীলতা, অনিয়মিত ঘুম ও স্নায়বিক চাপ",
            ],
            "beneficial_actions_and_remedies": [
                "একটি সময়ে একটি নির্দিষ্ট কাজে সম্পূর্ণ মনোযোগ দিয়ে তা শেষ করুন",
                "প্রতি বুধবার ভগবান শ্রী গণেশ অথবা বিষ্ণু সহস্রনাম পাঠ করুন",
                "গরুকে কাঁচা সবুজ ঘাস বা পালং শাক খাওয়ান এবং শিক্ষার্থীদের বই-খাতা দান করুন",
                "স্নায়ুকে শান্ত রাখতে নিয়মিত অনুলোম-বিলোম প্রাণায়াম ও মেডিটেশন করুন",
                "প্রতিদিনের গুরুত্বপূর্ণ কাজগুলো ডায়েরিতে লিখে তালিকাভুক্ত করুন",
            ],
            "career_fields": [
                "সাংবাদিকতা, গণমাধ্যম, কন্টেন্ট রাইটিং ও পাবলিশিং",
                "সফটওয়্যার ইঞ্জিনিয়ারিং, আইটি, টেলিকম ও ডাটা অ্যানালিটিক্স",
                "মার্কেটিং, পিআর, সেলস ও আন্তর্জাতিক বাণিজ্য",
                "শিক্ষকতা, অনুবাদ, ভাষা বিশেষজ্ঞ ও মানবসম্পদ ব্যবস্থাপনা",
                "দালালি, শেয়ার বাজার ও কূটনৈতিক যোগাযোগ",
            ],
            "lucky_color": "পান্না সবুজ, হালকা হলুদ ও পুদিনা রঙ",
            "lucky_gemstone": "পান্না (Emerald)",
            "lucky_day": "বুধবার",
            "ruling_deity": "ভগবান শ্রী গণেশ ও শ্রী বিষ্ণু",
            "compatible_rashis": ["তুলা", "কুম্ভ", "মেষ", "সিংহ"],
        },
        "hi": {
            "name": "मिथुन",
            "element": "वायु तत्व",
            "modality": "द्विस्वभाव राशि (Dual)",
            "polarity": "पुरुष / धनात्मक (विषम राशि)",
            "body_parts": "कंधे, हाथ, भुजाएं, श्वसन प्रणाली और तंत्रिका तंत्र",
            "nature": "बुद्धिमान, जिज्ञासु, वाकपटु, चंचल, मिलनसार और बहुमुखी",
            "overview": (
                "बुध देव द्वारा शासित मिथुन राशि संचार, बुद्धि और चपलता की प्रतीक है। "
                "मिथुन राशि के जातक तीव्र बुद्धि, हास्य विनोद और उत्कृष्ट संवाद क्षमता के धनी होते हैं। "
                "वे हमेशा कुछ नया सीखने और दूसरों से संपर्क स्थापित करने के लिए तत्पर रहते हैं।"
            ),
            "strengths": [
                "उत्कृष्ट संवाद शैली और प्रभावशाली भाषण कला",
                "तीव्र बौद्धिक क्षमता और एक साथ कई काम करने का हुनर",
                "असीम जिज्ञासा और तेजी से सीखने की प्रवृत्ति",
                "सदाबहार ऊर्जा, मित्रतापूर्ण व्यवहार और सामाजिक आकर्षण",
            ],
            "cautions_and_pitfalls": [
                "चंचल मन, अत्यधिक चिंता और मानसिक तनाव के प्रति सजग रहें",
                "एक साथ बहुत सी चीजें शुरू करके किसी को भी पूरा न करने की आदत से बचें",
                "किसी विषय की गहराई में जाए बिना केवल सतही ज्ञान पर निर्भर रहना",
                "वादों से मुकरना या बार-बार अपने निर्णय बदलने की प्रवृत्ति",
                "श्वसन तंत्र की संवेदनशीलता, अनिद्रा और स्नायु दुर्बलता",
            ],
            "beneficial_actions_and_remedies": [
                "एक समय में केवल एक ही काम पूरा करने का दृढ़ नियम बनाएं",
                "प्रत्येक बुधवार को भगवान गणेश की पूजा करें और दूर्वा अर्पित करें",
                "गाय को हरा चारा या पालक खिलाएं और निर्धन छात्रों को पुस्तकें दान करें",
                "मन और नसों को शांत रखने के लिए नियमित अनुलोम-विलोम प्राणायाम करें",
                "दैनिक योजनाएं डायरी में लिखकर काम को व्यवस्थित करें",
            ],
            "career_fields": [
                "पत्रकारिता, मीडिया, लेखन एवं जनसंपर्क",
                "सॉफ्टवेयर, आईटी, दूरसंचार एवं डेटा नेटवर्किंग",
                "विपणन (मार्केटिंग), बिक्री एवं विज्ञापन",
                "अध्यापन, भाषा विज्ञान, अनुवाद एवं परामर्श",
                "वाणिज्य, दलाली एवं व्यापारिक मध्यस्थता",
            ],
            "lucky_color": "पन्ना हरा, हल्का पीला एवं पिस्ता रंग",
            "lucky_gemstone": "पन्ना (Emerald)",
            "lucky_day": "बुधवार",
            "ruling_deity": "भगवान श्री गणेश एवं श्री हरि विष्णु",
            "compatible_rashis": ["तुला", "कुंभ", "मेष", "सिंह"],
        },
    },

    # -------------------------------------------------------------------------
    # 3. CANCER (কর্কট / कर्क)
    # -------------------------------------------------------------------------
    3: {
        "en": {
            "name": "Cancer",
            "element": "Watery",
            "modality": "Movable / Cardinal",
            "polarity": "Feminine / Negative (Even sign)",
            "body_parts": "Chest, breasts, stomach, digestive tract, diaphragm",
            "nature": "Empathetic, intuitive, maternal, protective, emotional, nostalgic",
            "overview": (
                "As the natural domicile of the Moon, Cancer vibrates with deep emotion, intuition, "
                "and protective devotion. Those with Moon in Cancer are deeply caring, devoted to family, "
                "and sensitive to environmental energies. They have an expressive face, gentle eyes, and a "
                "magnetic warmth."
            ),
            "strengths": [
                "Unrivaled intuition, psychic sensitivity, and emotional depth",
                "Profound loyalty to family, home, and trusted loved ones",
                "Exceptional memory and nurturing, healing presence",
                "High emotional intelligence and creative imagination",
            ],
            "cautions_and_pitfalls": [
                "Fluctuating mood swings synchronized with waxing/waning moon cycles",
                "Clinging to past grievances, hurt feelings, and toxic attachments",
                "Emotional eating or digestive upset triggered by stress",
                "Defensive shell that shuts out well-meaning friends when hurt",
                "Over-sensitivity to minor criticisms or perceived rejection",
            ],
            "beneficial_actions_and_remedies": [
                "Take blessings from your mother or elder maternal figures regularly",
                "Offer raw milk and clean water (Jala Abhishekam) to Shiva Lingam on Mondays",
                "Drink water stored in clean silver cups or containers",
                "Donate white items (milk, rice, sugar, silver, white sweets) on Mondays",
                "Spend peaceful moments by water bodies (lakes, rivers, seas) to reset emotions",
            ],
            "career_fields": [
                "Medicine, nursing, pediatrics, psychology & counseling",
                "Hospitality, catering, culinary arts & dairy farming",
                "Real estate, home decor, architecture & interior design",
                "Education, childcare, social welfare & NGO leadership",
                "Marine industries, shipping, creative writing & poetry",
            ],
            "lucky_color": "Pearl White, Silver & Sea Green",
            "lucky_gemstone": "Natural Pearl (Moti) or Moonstone",
            "lucky_day": "Monday",
            "ruling_deity": "Lord Shiva & Goddess Parvati",
            "compatible_rashis": ["Scorpio", "Pisces", "Taurus", "Virgo"],
        },
        "bn": {
            "name": "কর্কট",
            "element": "জল তত্ত্ব (Water)",
            "modality": "চর রাশি (Movable)",
            "polarity": "স্ত্রী / ঋণাত্মক (সম রাশি)",
            "body_parts": "বুক, স্তন, পাকস্থলী, পরিপাকতন্ত্র ও মধ্যচ্ছদা",
            "nature": "সংবেদনশীল, স্নেহময়, সহানুভূতিশীল, মাতৃসুলভ, আবেগপ্রবণ ও দূরদর্শী",
            "overview": (
                "চন্দ্রের নিজস্ব রাশি কর্কট হলো আবেগ, অন্তর্দৃষ্টি ও মাতৃত্বের প্রতীক। "
                "কর্কট রাশির জাতক-জাতিকারা অত্যন্ত মায়াশীল ও পরিবারকেন্দ্রিক। তারা অন্যের মনের অবস্থা সহজে অনুভব করতে পারেন "
                "এবং যেকোনো পরিবেশকে নিজের উষ্ণ স্নেহ দিয়ে ভরিয়ে তোলেন।"
            ),
            "strengths": [
                "অতুলনীয় অন্তর্দৃষ্টি ও অন্যের মনের অনুভূতি বুঝতে পারার ক্ষমতা",
                "পরিবার ও আপনজনদের প্রতি গভীর ভালোবাসা ও আজীবন বিশ্বস্ততা",
                "অসাধারণ স্মৃতিশক্তি ও মানুষকে মানসিক সান্ত্বনা দেওয়ার বিশেষ গুণ",
                "উচ্চ আবেগী বুদ্ধিমত্তা ও সৃজনশীল কল্পনাশক্তির সমাহার",
            ],
            "cautions_and_pitfalls": [
                "চন্দ্রের তিথির মতো মেজাজের ঘন ঘন ওঠানামা (Mood Swings) থেকে সাবধান",
                "অতীতের তিক্ত স্মৃতি ও আঘাতকে আঁকড়ে ধরে বর্তমানকে নষ্ট করা",
                "মানসিক চাপের কারণে অতিরিক্ত খাওয়া বা পেটের সমস্যায় ভোগা",
                "আঘাত পেলে নিজের খোলসে গুটিয়ে গিয়ে শুভাকাঙ্ক্ষীদের দূরে সরিয়ে দেওয়া",
                "সামান্য সমালোচনা বা প্রত্যাখ্যানে অতিরিক্ত সংবেদনশীল হওয়া",
            ],
            "beneficial_actions_and_remedies": [
                "মায়ের সেবা করুন এবং প্রতিদিন বড়দের চরণ স্পর্শ করে আশীর্বাদ নিন",
                "প্রতি সোমবার শিবলিঙ্গে কাঁচা দুধ ও পরিষ্কার জল দিয়ে জলাভিষেক করুন",
                "রুপোর পাত্রে জল পানের অভ্যাস করুন যা চন্দ্রের তেজকে শান্ত রাখে",
                "সোমবার সাদা বস্ত্র, চাল, দুধ বা চিনি অভাবীদের দান করুন",
                "নদী বা সমুদ্রের শান্ত পরিবেশে সময় কাটিয়ে মানসিক শান্তি পুনরুদ্ধার করুন",
            ],
            "career_fields": [
                "চিকিৎসা, নার্সিং, শিশু বিশেষজ্ঞ ও মনস্তাত্ত্বিক পরামর্শদান",
                "হোটেল শিল্প, ক্যাটারিং, রন্ধনশিল্প ও দুগ্ধজাত পণ্যের ব্যবসা",
                "আবাসন (রিয়েল এস্টেট), হোম ডেকোরেশন ও স্থাপত্যশিল্প",
                "শিক্ষা, শিশুকল্যাণ ও সমাজসেবামূলক প্রতিষ্ঠান পরিচালনা",
                "নৌপরিবহন, সামুদ্রিক বাণিজ্য, কবিতা ও সাহিত্য রচনা",
            ],
            "lucky_color": "মুক্তা সাদা, রুপালি ও হালকা সমুদ্র-সবুজ",
            "lucky_gemstone": "খাঁটি মুক্তা (Natural Pearl)",
            "lucky_day": "সোমবার",
            "ruling_deity": "ভগবান দেবাদিদেব মহাদেব ও মা পার্বতী",
            "compatible_rashis": ["বৃশ্চিক", "মীন", "বৃষ", "কন্যা"],
        },
        "hi": {
            "name": "कर्क",
            "element": "जल तत्व",
            "modality": "चर राशि (Movable)",
            "polarity": "स्त्री / ऋणात्मक (सम राशि)",
            "body_parts": "छाती, स्तन, आमाशय, पाचन तंत्र और हृदय क्षेत्र",
            "nature": "संवेदनशील, करुणामयी, मातृवत, रक्षात्मक, भावुक और निष्ठावान",
            "overview": (
                "चंद्र देव के आधिपत्य वाली कर्क राशि भावनाओं, अंतर्ज्ञान और ममता का प्रतीक है। "
                "कर्क राशि के जातक अत्यधिक संवेदनशील, स्नेही और परिवार के प्रति समर्पित होते हैं। "
                "उनमें दूसरों की भावनाओं को बिना कहे समझ लेने की अद्भुत ईश्वरप्रदत्त क्षमता होती है।"
            ),
            "strengths": [
                "अद्वितीय अंतर्ज्ञान और सूक्ष्म भावनात्मक संवेदनशीलता",
                "परिवार और प्रियजनों के प्रति अटूट निष्ठा और समर्पण",
                "अद्भुत स्मरण शक्ति और आत्मीयता से घाव भरने की क्षमता",
                "उच्च भावनात्मक बुद्धिमत्ता और समृद्ध रचनात्मक कल्पना",
            ],
            "cautions_and_pitfalls": [
                "मूड में तेजी से उतार-चढ़ाव और अत्यधिक भावुकता से बचें",
                "पुरानी कड़वी यादों और दुखों को मन में पकड़कर बैठे रहना",
                "तनाव के कारण गलत खानपान और पेट की समस्याओं का शिकार होना",
                "जरा सी बात पर आहत होकर अपनों से दूरी बना लेना",
                "छोटी-मोटी आलोचना से अत्यधिक आहत हो जाना",
            ],
            "beneficial_actions_and_remedies": [
                "अपनी माता की सेवा करें और प्रतिदिन उनका आशीर्वाद प्राप्त करें",
                "सोमवार को शिवलिंग पर कच्चा दूध और जल अर्पित करें",
                "चांदी के गिलास में जल पीने की आदत बनाएं, इससे मानसिक शांति मिलती है",
                "सोमवार को सफेद वस्त्र, चावल, दूध या चीनी का दान करें",
                "शांत जलस्रोतों (नदी या समुद्र) के किनारे समय बिताकर ध्यान लगाएं",
            ],
            "career_fields": [
                "चिकित्सा, नर्सिंग, बाल रोग विशेषज्ञ एवं मनोवैज्ञानिक परामर्श",
                "होटल प्रबंधन, खानपान एवं डेयरी उद्योग",
                "रियल एस्टेट, गृह सज्जा एवं वास्तुकला",
                "शिक्षा, बाल कल्याण एवं समाज सेवा",
                "नौवहन, समुद्री व्यापार, कविता एवं रचनात्मक लेखन",
            ],
            "lucky_color": "मोती जैसा सफेद, चांदी रंग एवं हल्का हरा",
            "lucky_gemstone": "सच्चा मोती (Pearl) या मूनस्टोन",
            "lucky_day": "सोमवार",
            "ruling_deity": "भगवान शिव एवं माता पार्वती",
            "compatible_rashis": ["वृश्चिक", "मीन", "वृषभ", "कन्या"],
        },
    },

    # -------------------------------------------------------------------------
    # 4. LEO (সিংহ / सिंह)
    # -------------------------------------------------------------------------
    4: {
        "en": {
            "name": "Leo",
            "element": "Fiery",
            "modality": "Fixed / Static",
            "polarity": "Masculine / Positive (Odd sign)",
            "body_parts": "Heart, upper back, spine, solar plexus, vitality",
            "nature": "Royal, charismatic, generous, noble, confident, authoritative",
            "overview": (
                "Ruled by the Sun, Leo represents royalty, nobility, and natural majesty. "
                "Moon in Leo individuals have a regal presence, broad chest, commanding voice, and "
                "a golden warmth that draws others in. They are born to lead, inspire, and create lasting "
                "impact with unshakeable dignity."
            ),
            "strengths": [
                "Natural charisma, leadership, and magnetic presence",
                "Magnanimous generosity and loyalty to followers",
                "High creative courage, self-confidence, and dignity",
                "Optimistic enthusiasm that elevates any group or team",
            ],
            "cautions_and_pitfalls": [
                "Inflated ego, false pride, and intolerance of criticism",
                "Commanding or authoritarian attitude that alienates peers",
                "Vulnerability to flattery from dishonest individuals",
                "Overworking heart/circulatory system; spine and postural strain",
                "Refusing to seek assistance when facing personal vulnerability",
            ],
            "beneficial_actions_and_remedies": [
                "Offer water (Surya Arghya) to the rising morning Sun with Gayatri Mantra",
                "Practice humble leadership and actively praise teammates' achievements",
                "Respect father, teachers, and authority figures with genuine reverence",
                "Donate wheat, copper, or jaggery to the needy on Sundays",
                "Maintain cardiovascular wellness with moderate aerobics and back stretches",
            ],
            "career_fields": [
                "Governance, politics, civil services & senior administrative roles",
                "Corporate executive leadership (CEO/Director) & management",
                "Entertainment, acting, theater, film directing & fine arts",
                "Jewelry trade, gold, bullion markets & luxury retail",
                "Motivational speaking, coaching & brand ambassadorship",
            ],
            "lucky_color": "Royal Gold, Sun Orange & Crimson",
            "lucky_gemstone": "Ruby (Manikya)",
            "lucky_day": "Sunday",
            "ruling_deity": "Lord Surya (The Sun God)",
            "compatible_rashis": ["Aries", "Sagittarius", "Gemini", "Libra"],
        },
        "bn": {
            "name": "সিংহ",
            "element": "অগ্নি তত্ত্ব (Fire)",
            "modality": "স্থির রাশি (Fixed)",
            "polarity": "পুরুষ / ধনাত্মক (বিষম রাশি)",
            "body_parts": "হৃৎপিণ্ড, মেরুদণ্ড, পিঠের উপরিভাগ ও জীবনীশক্তি",
            "nature": "রাজকীয়, মহানুভব, তেজস্বী, আত্মবিশ্বাসী, প্রভারশালী ও উদার",
            "overview": (
                "গ্রহরাজ সূর্য দ্বারা শাসিত সিংহ রাশি আভিজাত্য, নেতৃত্ব ও রাজসিক মহিমার প্রতীক। "
                "সিংহ রাশির জাতক-জাতিকারা স্বাভাবিকভাবেই কর্তৃত্বপরায়ণ ও আত্মমর্যাদাসম্পন্ন। তারা মানুষের শ্রদ্ধা ও ভালোবাসা অর্জন করতে পারেন "
                "এবং যেকোনো দলকে দক্ষতার সাথে পরিচালনা করার ক্ষমতা রাখেন।"
            ),
            "strengths": [
                "সহজাত নেতৃত্বগুণ, ব্যক্তিত্বের অমোঘ আকর্ষণ ও রাজকীয় তেজ",
                "বিশাল হৃদয়, উদার দানশীলতা এবং অনুসারীদের প্রতি আজীবন সুরক্ষা",
                "উচ্চ আত্মবিশ্বাস, কাজের প্রতি সততা এবং সৃজনশীল প্রতিভা",
                "যেকোনো দলকে অনুপ্রাণিত করার অসাধারণ ক্ষমতা",
            ],
            "cautions_and_pitfalls": [
                "অতিরিক্ত অহংকার, মিথ্যা আত্মমর্যাদাবোধ এবং সমালোচনা সহ্য না করতে পারা",
                "অন্যের উপর নিজের মতামত জোর করে চাপিয়ে দেওয়ার কর্তৃত্ববাদী মানসিকতা",
                "চাটুকার ও অসৎ মানুষের মিষ্টি কথায় বিভ্রান্ত হওয়া থেকে সাবধান",
                "হৃদযন্ত্র, মেরুদণ্ড এবং রক্তচাপের প্রতি অবহেলা করা",
                "প্রয়োজনের সময়েও অহংকারের কারণে অন্যের সাহায্য না চাওয়া",
            ],
            "beneficial_actions_and_remedies": [
                "প্রতিদিন সকালে উদীয়মান সূর্যকে তামার পাত্রে জল অর্পণ (সূর্য অর্ঘ্য) করুন",
                "নেতৃত্ব দেওয়ার সময় দলের সদস্যদের কাজের প্রশংসা ও সম্মান করুন",
                "পিতা, শিক্ষক ও গুরুজনদের প্রতি আন্তরিক শ্রদ্ধা বজায় রাখুন",
                "রবিবার গম, গুড় বা তামার সামগ্রী অভাবীদের দান করুন",
                "হৃদযন্ত্রের সুরক্ষায় নিয়মিত হালকা ব্যায়াম ও পিঠের স্ট্রেচিং করুন",
            ],
            "career_fields": [
                "সরকারি প্রশাসন, সিভিল সার্ভিস ও রাজনৈতিক নেতৃত্ব",
                "কর্পোরেট শীর্ষ নির্বাহি (CEO/ডিরেক্টর) ও উচ্চতর ব্যবস্থাপনা",
                "অভিনয়, চলচ্চিত্র পরিচালনা, নাট্যশিল্প ও গ্ল্যামার জগত",
                "স্বর্ণালঙ্কার, রত্ন ব্যবসা ও প্রিমিয়াম লাক্সারি ব্র্যান্ড",
                "অনুপ্রেরণাদায়ী বক্তা ও ব্র্যান্ড অ্যাম্বাসেডর",
            ],
            "lucky_color": "রাজকীয় সোনালি, গাঢ় কমলা ও রক্তিম লাল",
            "lucky_gemstone": "চুনী বা রুবি (Ruby)",
            "lucky_day": "রবিবার",
            "ruling_deity": "ভগবান সূর্যদেব",
            "compatible_rashis": ["মেষ", "ধনু", "মিথুন", "তুলা"],
        },
        "hi": {
            "name": "सिंह",
            "element": "अग्नि तत्व",
            "modality": "स्थिर राशि (Fixed)",
            "polarity": "पुरुष / धनात्मक (विषम राशि)",
            "body_parts": "हृदय, रीढ़ की हड्डी, ऊपरी पीठ और जीवन शक्ति",
            "nature": "राजसी, उदार, आत्मविश्वासी, प्रभावशाली, साहसी और गरिमामयी",
            "overview": (
                "सूर्य देव द्वारा शासित सिंह राशि शौर्य, तेज और नेतृत्व का प्रतीक है। "
                "सिंह राशि के जातक राजा के समान प्रभावशाली, स्वाभिमानी और विशाल हृदय वाले होते हैं। "
                "वे जहां भी जाते हैं, अपनी उपस्थिति से सबको प्रभावित करते हैं और नेतृत्व संभालते हैं।"
            ),
            "strengths": [
                "स्वाभाविक नेतृत्व क्षमता, चुंबकीय व्यक्तित्व और प्रभावशाली वाणी",
                "उदारता, निष्ठा और अपने साथियों की रक्षा करने का जज्बा",
                "उच्च आत्मसम्मान, अदम्य साहस और रचनात्मक क्षमता",
                "हौसला बढ़ाने वाला सकारात्मक और प्रेरणादायक दृष्टिकोण",
            ],
            "cautions_and_pitfalls": [
                "झूठा अहंकार, अत्यधिक स्वाभिमान और आलोचना सहन न कर पाना",
                "दूसरों पर अपना हुक्म चलाने और तानाशाही रवैया अपनाने से बचें",
                "चापलूसी करने वाले लोगों की बातों में आकर गलत निर्णय लेना",
                "हृदय, रीढ़ की हड्डी और रक्तचाप की समस्याओं को अनदेखा करना",
                "जरूरत पड़ने पर भी अहंकारवश दूसरों से मदद न मांगना",
            ],
            "beneficial_actions_and_remedies": [
                "प्रतिदिन सुबह तांबे के लोटे से सूर्यदेव को अर्घ्य दें और गायत्री मंत्र जपें",
                "विनम्रतापूर्वक नेतृत्व करें और अपने साथियों की खुलकर सराहना करें",
                "पिता, गुरु और वरिष्ठजनों का हृदय से सम्मान करें",
                "रविवार को गेहूं, तांबा या गुड़ का दान जरूरतमंदों को करें",
                "हृदय और पीठ को स्वस्थ रखने के लिए नियमित व्यायाम और योग करें",
            ],
            "career_fields": [
                "सरकारी सेवा, राजनीति, प्रशासनिक पद एवं सिविल सर्विसेज",
                "कॉर्पोरेट लीडरशिप (सीईओ/निदेशक) एवं उच्च प्रबंधन",
                "सिनेमा, अभिनय, निर्देशन एवं नाट्य कला",
                "स्वर्ण आभूषण, रत्न व्यापार एवं लग्जरी उत्पाद",
                "मोटिवेशनल स्पीकर एवं ब्रांड एम्बेसडर",
            ],
            "lucky_color": "स्वर्णिम पीला, गहरा नारंगी एवं लाल",
            "lucky_gemstone": "माणिक्य (Ruby)",
            "lucky_day": "रविवार",
            "ruling_deity": "भगवान सूर्यनारायण",
            "compatible_rashis": ["मेष", "धनु", "मिथुन", "तुला"],
        },
    },

    # -------------------------------------------------------------------------
    # 5. VIRGO (কন্যা / कन्या)
    # -------------------------------------------------------------------------
    5: {
        "en": {
            "name": "Virgo",
            "element": "Earthy",
            "modality": "Dual / Common",
            "polarity": "Feminine / Negative (Even sign)",
            "body_parts": "Abdomen, digestive tract, intestines, spleen, nervous system",
            "nature": "Analytical, meticulous, methodical, observant, helpful, health-conscious",
            "overview": (
                "Ruled by Mercury, Virgo represents purity, discernment, and analytical precision. "
                "Moon in Virgo endows an observant intellect, polite manners, neat habits, and "
                "a natural drive to be of practical service. They possess sharp analytical skills and "
                "an eye for flawless craftsmanship."
            ),
            "strengths": [
                "Incisive analytical intellect and attention to micro-details",
                "Practical problem solving and exceptional organizational skills",
                "Modest, dependable, and genuinely devoted to helping others",
                "High standards of health, hygiene, and craftsmanship",
            ],
            "cautions_and_pitfalls": [
                "Hyper-critical mindset picking faults in self and loved ones",
                "Chronic overthinking and anxiety over minor uncertainties",
                "Digestive sensitivities, irritable bowel, and stress-induced stomach cramps",
                "Getting bogged down in trivial details and missing the big picture",
                "Hesitancy to take bold leaps due to fear of imperfection",
            ],
            "beneficial_actions_and_remedies": [
                "Practice self-compassion and accept that perfection is an impossible benchmark",
                "Chant Vishnu Sahasranama or Budha Beej Mantra on Wednesdays",
                "Feed fresh green spinach or green vegetables to cows on Wednesdays",
                "Donate stationery, textbooks, or green lentils (moong dal) to students",
                "Maintain gut health with probiotics, light fiber-rich meals, and routine walks",
            ],
            "career_fields": [
                "Data analysis, statistics, research science & audit",
                "Medicine, pharmacy, nutrition & healthcare administration",
                "Software quality assurance, architecture & systems engineering",
                "Editing, proofreading, library science & technical writing",
                "Accounting, chartered accountancy & financial auditing",
            ],
            "lucky_color": "Leaf Green, Navy Blue & Pure White",
            "lucky_gemstone": "Emerald (Panna) or Peridot",
            "lucky_day": "Wednesday",
            "ruling_deity": "Lord Vishnu & Lord Ganesha",
            "compatible_rashis": ["Taurus", "Capricorn", "Cancer", "Scorpio"],
        },
        "bn": {
            "name": "কন্যা",
            "element": "পৃথ্বী তত্ত্ব (Earth)",
            "modality": "দ্বিস্বভাব রাশি (Dual)",
            "polarity": "স্ত্রী / ঋণাত্মক (সম রাশি)",
            "body_parts": "পেট, অন্ত্র, পরিপাকতন্ত্র, প্লীহা ও স্নায়ুতন্ত্র",
            "nature": "বিশ্লেষণী, খুঁতখুঁতে, বাস্তববাদী, বিনম্র, সুশৃঙ্খল ও সেবাপরায়ণ",
            "overview": (
                "বুধ গ্রহের অধীন কন্যা রাশি পবিত্রতা, বুদ্ধিমত্তা ও সূক্ষ্ম বিশ্লেষণের প্রতীক। "
                "কন্যা রাশির জাতক-জাতিকারা অত্যন্ত শৃঙ্খলাপ্রিয়, পরিচ্ছন্ন এবং কাজে নিখুঁত হতে ভালোবাসেন। "
                "তারা গভীর পর্যবেক্ষণ ক্ষমতা দিয়ে যেকোনো জটিল সমস্যার বাস্তবসম্মত সমাধান বের করতে পারেন।"
            ),
            "strengths": [
                "তীক্ষ্ণ পর্যবেক্ষণ ক্ষমতা এবং খুঁটিনাটি বিষয় নিখুঁতভাবে বিশ্লেষণ করার দক্ষতা",
                "অসাধারণ সাংগঠনিক শৃঙ্খলা এবং বাস্তবমুখী কর্মপরিকল্পনা",
                "বিনয়ী, বিশ্বস্ত এবং অন্যের প্রয়োজনে নিস্বার্থভাবে পাশে দাঁড়ানোর গুণ",
                "স্বাস্থ্য ও পরিচ্ছন্নতার প্রতি উচ্চমানের সচেতনতা",
            ],
            "cautions_and_pitfalls": [
                "সবকিছুতে নিখুঁত হতে গিয়ে অতিরিক্ত খুঁতখুঁতে স্বভাব ও নিজের উপর অতিরিক্ত চাপ নেওয়া",
                "সামান্য ত্রুটিতে গভীর অবসাদ ও নেতিবাচক চিন্তায় নিমজ্জিত হওয়া",
                "হজমের গোলযোগ, পেটের দুর্বলতা এবং স্নায়বিক টানাপোড়েন থেকে সাবধান",
                "অতিরিক্ত হিসাব-নিকাশ করতে গিয়ে সুন্দর সুযোগ হাতছাড়া করা",
                "অন্যের ভুল ধরিয়ে দিতে গিয়ে কঠোর বাক্য প্রয়োগ করা",
            ],
            "beneficial_actions_and_remedies": [
                "কাজের মাঝে বিশ্রাম নিন এবং নিজের ত্রুটিগুলোকে ক্ষমাসুন্দর দৃষ্টিতে দেখুন",
                "প্রতি বুধবার শ্রী বিষ্ণু সহস্রনাম বা গণেশ অথর্বশীর্ষ পাঠ করুন",
                "সবুজ শাকসবজি বা কচি ঘাস গরুকে খাওয়ান",
                "অসহায় বা দরিদ্র পড়ুয়াদের পড়াশোনার উপকরণ দিয়ে সহায়তা করুন",
                "পেটের সুরক্ষায় খাঁটি ও সহজপাচ্য পুষ্টিকর খাবার গ্রহণ করুন",
            ],
            "career_fields": [
                "ডাটা সায়েন্স, পরিসংখ্যান, বৈজ্ঞানিক গবেষণা ও অডিট",
                "চিকিৎসা, ফার্মাসিউটিক্যালস, পুষ্টিবিজ্ঞান ও স্বাস্থ্যসেবা",
                "সফটওয়্যার কোয়ালিটি টেস্টিং ও সিস্টেমস ইঞ্জিনিয়ারিং",
                "সম্পাদনা, টেকনিক্যাল রাইটিং ও লাইব্রেরি সায়েন্স",
                "চার্টার্ড অ্যাকাউন্ট্যান্সি ও আর্থিক নিরীক্ষা",
            ],
            "lucky_color": "গাঢ় সবুজ, নেভি ব্লু ও ধবধবে সাদা",
            "lucky_gemstone": "পান্না (Emerald)",
            "lucky_day": "বুধবার",
            "ruling_deity": "ভগবান শ্রী হরি বিষ্ণু",
            "compatible_rashis": ["বৃষ", "মকর", "কর্কট", "বৃশ্চিক"],
        },
        "hi": {
            "name": "कन्या",
            "element": "पृथ्वी तत्व",
            "modality": "द्विस्वभाव राशि (Dual)",
            "polarity": "स्त्री / ऋणात्मक (सम राशि)",
            "body_parts": "उदर, आंतें, पाचन संस्थान और तंत्रिका तंत्र",
            "nature": "विश्लेषणात्मक, सूक्ष्मदर्शी, व्यावहारिक, विनम्र, व्यवस्थित और सेवाभावी",
            "overview": (
                "बुध ग्रह द्वारा शासित कन्या राशि शुद्धता, विवेक और विश्लेषण की प्रतीक है। "
                "कन्या राशि के जातक परिश्रमी, सुव्यवस्थित और हर कार्य को पूरी सटीकता से करने वाले होते हैं। "
                "उनकी तार्किक क्षमता और व्यावहारिक दृष्टिकोण उन्हें उत्कृष्ट योजनाकार बनाता है।"
            ),
            "strengths": [
                "सूक्ष्म विवरणों को परखने की अद्भुत क्षमता और तीक्ष्ण बुद्धि",
                "व्यावहारिक समस्या निवारण और त्रुटिहीन प्रबंधन कौशल",
                "निस्वार्थ सेवा भाव, विनम्रता और भरोसेमंद आचरण",
                "स्वास्थ्य, स्वच्छता और गुणवत्ता के प्रति उच्च जागरूकता",
            ],
            "cautions_and_pitfalls": [
                "हर बात में अत्यधिक पूर्णता (Perfection) चाहना और कमियां निकालना",
                "अत्यधिक सोच-विचार और छोटी बातों पर गहरी चिंता करना",
                "पाचन विकार, पेट की समस्याएं और मानसिक तनाव के प्रति सजग रहें",
                "अत्यधिक विश्लेषण के चक्कर में लाभदायक अवसरों को गंवा देना",
                "दूसरों की आलोचना करते समय अप्रिय शब्द बोल देना",
            ],
            "beneficial_actions_and_remedies": [
                "यह स्वीकार करें कि कोई भी पूर्ण नहीं होता; खुद को भी थोड़ा विश्राम दें",
                "बुधवार को श्री विष्णु सहस्रनाम या गणेश संकटनाशन स्तोत्र पढ़ें",
                "गौमाता को हरा चारा या पालक खिलाएं",
                "निर्धन विद्यार्थियों को पुस्तकें या हरी मूंग की दाल का दान करें",
                "पाचन तंत्र को स्वस्थ रखने के लिए सुपाच्य और सात्विक भोजन लें",
            ],
            "career_fields": [
                "डेटा विश्लेषण, अनुसंधान, सांख्यिकी एवं ऑडिटिंग",
                "चिकित्सा, फार्मेसी, पोषण विज्ञान एवं स्वास्थ्य प्रबंधन",
                "सॉफ्टवेयर टेस्टिंग, सिस्टम आर्किटेक्चर एवं प्रोग्रामिंग",
                "संपादन, प्रूफरीडिंग एवं तकनीकी लेखन",
                "चार्टर्ड अकाउंटेंसी, लेखा एवं वित्तीय नियंत्रण",
            ],
            "lucky_color": "पत्ता हरा, गहरा नीला एवं सफेद",
            "lucky_gemstone": "पन्ना (Emerald)",
            "lucky_day": "बुधवार",
            "ruling_deity": "भगवान श्री हरि विष्णु",
            "compatible_rashis": ["वृषभ", "मकर", "कर्क", "वृश्चिक"],
        },
    },

    # -------------------------------------------------------------------------
    # 6. LIBRA (তুলা / तुला)
    # -------------------------------------------------------------------------
    6: {
        "en": {
            "name": "Libra",
            "element": "Airy",
            "modality": "Movable / Cardinal",
            "polarity": "Masculine / Positive (Odd sign)",
            "body_parts": "Kidneys, lower back, adrenal glands, buttocks, lumbar region",
            "nature": "Diplomatic, charming, balanced, justice-oriented, aesthetic, social",
            "overview": (
                "Ruled by Venus, Libra is the celestial balance scale representing harmony, justice, "
                "and partnership. Individuals with Moon in Libra are natural diplomats with graceful manners, "
                "symmetrical aesthetics, and a soothing demeanor. They thrive in harmonious partnerships and "
                "artistic environments."
            ),
            "strengths": [
                "Exemplary diplomacy, mediation, and conflict-resolution ability",
                "Flawless aesthetic taste, elegance, and social grace",
                "Strong moral commitment to fairness, justice, and equality",
                "Charming, accommodating, and peaceful relationship partner",
            ],
            "cautions_and_pitfalls": [
                "Crippling indecision and paralysis by over-evaluating options",
                "People-pleasing tendencies compromising personal integrity",
                "Superficial charm masking underlying conflict avoidance",
                "Vulnerability to kidney stones, lower back strain, and hormonal shifts",
                "Excessive spending on luxuries, fashion, and social appearances",
            ],
            "beneficial_actions_and_remedies": [
                "Practice making prompt, firm decisions without second-guessing",
                "Worship Goddess Durga or Mahalakshmi on Fridays with white lotus flowers",
                "Maintain optimal kidney hydration; drink ample pure water throughout the day",
                "Donate white silk, perfumes, dairy, or sweets to underprivileged women",
                "Set clear personal boundaries and avoid appeasing toxic individuals",
            ],
            "career_fields": [
                "Law, judiciary, arbitration & diplomatic services",
                "Interior decoration, architecture, fashion & graphic design",
                "Public relations, event curation & luxury hospitality",
                "Performing arts, music, dance & fashion styling",
                "Counseling, marriage arbitration & corporate mediation",
            ],
            "lucky_color": "Pastel Pink, Sky Blue, Cream & Opal White",
            "lucky_gemstone": "Diamond (Heera) or White Zircon",
            "lucky_day": "Friday",
            "ruling_deity": "Goddess Durga & Goddess Lakshmi",
            "compatible_rashis": ["Gemini", "Aquarius", "Leo", "Sagittarius"],
        },
        "bn": {
            "name": "তুলা",
            "element": "বায়ু তত্ত্ব (Air)",
            "modality": "চর রাশি (Movable)",
            "polarity": "পুরুষ / ধনাত্মক (বিষম রাশি)",
            "body_parts": "কিডনি, কোমরের নিম্নভাগ, অ্যাড্রিনাল গ্রন্থি ও নিতম্ব",
            "nature": "ন্যায়পরায়ণ, ভারসাম্যপূর্ণ, রুচিশীল, শান্তিপ্রিয়, কূটনৈতিক ও মার্জিত",
            "overview": (
                "শুক্র গ্রহের অধীন তুলা রাশি হলো দাঁড়িপাল্লা বা ভারসাম্যের প্রতীক। "
                "তুলা রাশির জাতক-জাতিকারা মার্জিত স্বভাব, চমৎকার সামাজিক শিষ্টাচার ও সৌন্দর্যের সমঝদার। "
                "তারা সমাজে শান্তি, ন্যায়বিচার ও সুসম্পর্ক রক্ষা করতে অগ্রণী ভূমিকা পালন করেন।"
            ),
            "strengths": [
                "অসাধারণ কূটনৈতিক দক্ষতা ও যেকোনো বিতর্ক সুন্দরভাবে মীমাংসা করার ক্ষমতা",
                "অনবদ্য নান্দনিক রুচিবোধ, সাজসজ্জা ও মার্জিত শিষ্টাচার",
                "ন্যায়বিচার, নিরপেক্ষতা এবং সাম্যের প্রতি গভীর দায়বদ্ধতা",
                "মিষ্টভাষী, সহানুভূতিশীল ও শান্তিময় জীবনসঙ্গী",
            ],
            "cautions_and_pitfalls": [
                "সিদ্ধান্তহীনতা (Indecision) এবং সবাইকে সন্তুষ্ট করতে গিয়ে নিজের ক্ষতি করা",
                "ভুল সম্পর্কে অতিরিক্ত ছাড় দেওয়া ও আত্মমর্যাদা ক্ষুণ্ণ করা",
                "সৌন্দর্য ও বাহ্যিক চাকচিক্যে অতিরিক্ত অর্থ অপচয় করার প্রবণতা",
                "কিডনি, মূত্রনালী ও কোমরের ব্যথা সংক্রান্ত সমস্যা থেকে সাবধান",
                "অপ্রীতিকর সত্য এড়িয়ে গিয়ে সংঘাতকে লুকিয়ে রাখার চেষ্টা",
            ],
            "beneficial_actions_and_remedies": [
                "দৃঢ় সিদ্ধান্ত নিতে শিখুন এবং যুক্তির পাশাপাশি অন্তর্দৃষ্টির সাহায্য নিন",
                "প্রতি শুক্রবার দেবী দুর্গা বা মা মহালক্ষ্মীর পুজো করুন",
                "সুগন্ধি (ইতর বা চন্দন) ব্যবহার করুন এবং পরিষ্কার সাদা পোশাক পরিধান করুন",
                "অভাবী কন্যাদের শিক্ষা বা বিবাহে যথাসাধ্য সহায়তা করুন",
                "কিডনি সুস্থ রাখতে প্রতিদিন পর্যাপ্ত পরিমাণ বিশুদ্ধ জল পান করুন",
            ],
            "career_fields": [
                "আইনব্যবস্থা, বিচারবিভাগ, সালিশি ও কূটনৈতিক পরিষেবা",
                "ইন্টেরিয়র ডেকোরেশন, স্থাপত্য, ফ্যাশন ও গ্রাফিক্স ডিজাইন",
                "পাবলিক রিলেশনস, ইভেন্ট কিউরেশন ও লাক্সারি হসপিটালিটি",
                "সংগীত, চারুকলা, নৃত্য ও ফ্যাশন স্টাইলিং",
                "পারিবারিক ও বৈবাহিক কাউন্সেলিং এবং জনসংযোগ",
            ],
            "lucky_color": "হালকা গোলাপি, আকাশী নীল, ক্রিম ও দুধসাদা",
            "lucky_gemstone": "হীরক (Diamond) বা সাদা জিরকন",
            "lucky_day": "শুক্রবার",
            "ruling_deity": "দেবী দুর্গা ও মা মহালক্ষ্মী",
            "compatible_rashis": ["মিথুন", "কুম্ভ", "সিংহ", "ধনু"],
        },
        "hi": {
            "name": "तुला",
            "element": "वायु तत्व",
            "modality": "चर राशि (Movable)",
            "polarity": "पुरुष / धनात्मक (विषम राशि)",
            "body_parts": "गुर्दे (किडनी), कमर का निचला हिस्सा और कटि प्रदेश",
            "nature": "न्यायप्रिय, संतुलित, कलाप्रेमी, कूटनीतिज्ञ, आकर्षक और शांतिप्रिय",
            "overview": (
                "शुक्र देव द्वारा शासित तुला राशि न्याय, संतुलन और सौंदर्य की प्रतीक है। "
                "तुला राशि के जातक सुरुचिपूर्ण, मिलनसार और निष्पक्ष स्वभाव के होते हैं। "
                "वे जीवन में संतुलन, कलात्मक परिवेश और मधुर संबंधों को सबसे अधिक महत्व देते हैं।"
            ),
            "strengths": [
                "विवादों को सुलझाने की असाधारण कूटनीतिक क्षमता और निष्पक्षता",
                "उत्कृष्ट सौंदर्य बोध, सुरुचिपूर्ण शैली और सौम्य आचरण",
                "सत्य, न्याय और समानता के प्रति अडिग निष्ठा",
                "शांतिप्रिय, सहयोगात्मक और आदर्श जीवनसाथी",
            ],
            "cautions_and_pitfalls": [
                "अनिर्णय की स्थिति और सबको खुश करने के चक्कर में अपना नुकसान करना",
                "गलत रिश्तों में सीमा से अधिक समझौता करना",
                "दिखावे और विलासिता की वस्तुओं पर व्यर्थ धन खर्च करना",
                "गुर्दे (किडनी), पीठ के निचले हिस्से और मूत्र संबंधी समस्याओं के प्रति सचेत रहें",
                "विवाद से बचने के लिए कड़वे सच का सामना करने से कतराना",
            ],
            "beneficial_actions_and_remedies": [
                "दृढ़ निर्णय लेने की आदत डालें और समय पर स्पष्ट फैसला करें",
                "शुक्रवार को मां दुर्गा या मां महालक्ष्मी की आराधना करें",
                "सुगंधित इत्र या चंदन का प्रयोग करें और श्वेत वस्त्र धारण करें",
                "निर्धन कन्याओं की शिक्षा या विवाह में यथासंभव सहयोग करें",
                "गुर्दों की सुरक्षा के लिए दिनभर में पर्याप्त मात्रा में पानी पिएं",
            ],
            "career_fields": [
                "वकालत, न्यायपालिका, कूटनीति एवं मध्यस्थता",
                "इंटीरियर डिजाइन, फैशन, वास्तुकला एवं कलात्मक क्षेत्र",
                "जनसंपर्क (पीआर), इवेंट मैनेजमेंट एवं लग्जरी हॉस्पिटैलिटी",
                "संगीत, अभिनय, मॉडलिंग एवं सौंदर्य परामर्श",
                "वैवाहिक परामर्श एवं कॉर्पोरेट सुलह",
            ],
            "lucky_color": "हल्का गुलाबी, आसमानी नीला एवं दूधिया सफेद",
            "lucky_gemstone": "हीरा (Diamond) या सफेद जरकन",
            "lucky_day": "शुक्रवार",
            "ruling_deity": "माता दुर्गा एवं महालक्ष्मी",
            "compatible_rashis": ["मिथुन", "कुंभ", "सिंह", "धनु"],
        },
    },

    # -------------------------------------------------------------------------
    # 7. SCORPIO (বৃশ্চিক / वृश्चिक) - USER'S SIGN IN SCREENSHOT
    # -------------------------------------------------------------------------
    7: {
        "en": {
            "name": "Scorpio",
            "element": "Watery",
            "modality": "Fixed / Static",
            "polarity": "Feminine / Negative (Even sign)",
            "body_parts": "Reproductive organs, pelvis, excretory system, bladder",
            "nature": "Intense, penetrating, secretive, transformative, loyal, resilient",
            "overview": (
                "Ruled by Mars and representing the deep mystical waters, Scorpio is the sign of "
                "profound regeneration and hidden power. Moon in Scorpio (debilitated in classical "
                "terms, yet deeply perceptive) bestows penetrating intuition, iron willpower, "
                "unwavering loyalty, and the ability to resurrect from life's greatest tribulations."
            ),
            "strengths": [
                "Unshakeable willpower, resilience, and transformative capacity",
                "Profound psychological penetration and lie-detection ability",
                "Fierce, lifelong loyalty to those who earn their trust",
                "Mastery over research, occult mysteries, and confidential matters",
            ],
            "cautions_and_pitfalls": [
                "Harboring deep resentment, jealousy, and revenge fantasies",
                "Extreme secrecy and paranoia pushing loving people away",
                "Emotional all-or-nothing extremes leading to self-sabotage",
                "Vulnerability to reproductive, urinary, or pelvic inflammation",
                "Difficulty forgiving past betrayals or emotional wounds",
            ],
            "beneficial_actions_and_remedies": [
                "Practice conscious forgiveness and release mental grudges daily",
                "Worship Lord Shiva (Maha Mrityunjaya Mantra) or Lord Hanuman on Tuesdays",
                "Donate blood voluntarily or donate red lentils/copper on Tuesdays",
                "Channel intensity into investigative work, occult research, or psychotherapy",
                "Maintain hygienic reproductive/pelvic health and practice grounding meditation",
            ],
            "career_fields": [
                "Investigative journalism, espionage, intelligence & detective work",
                "Surgery, pathology, oncology & psychiatric psychotherapy",
                "Cybersecurity, forensic science & data forensics",
                "Mining, geology, petroleum, metallurgy & marine engineering",
                "Astrology, occult sciences, metaphysics & deep research",
            ],
            "lucky_color": "Deep Maroon, Rust Brown, Black & Dark Red",
            "lucky_gemstone": "Red Coral (Moonga) or Carnelian",
            "lucky_day": "Tuesday",
            "ruling_deity": "Lord Shiva & Lord Hanuman",
            "compatible_rashis": ["Cancer", "Pisces", "Virgo", "Capricorn"],
        },
        "bn": {
            "name": "বৃশ্চিক",
            "element": "জল তত্ত্ব (Water)",
            "modality": "স্থির রাশি (Fixed)",
            "polarity": "স্ত্রী / ঋণাত্মক (সম রাশি)",
            "body_parts": "প্রজনন অঙ্গ, পেলভিস, মূত্রনালী ও রেচনতন্ত্র",
            "nature": "গভীর, আত্মপ্রত্যয়ী, রহস্যময়, অদম্য মনোবলের অধিকারী ও দৃঢ়চেতা",
            "overview": (
                "মঙ্গল গ্রহের শাসনাধীন বৃশ্চিক রাশি গভীর রহস্য, আত্মিক রূপান্তর ও অদম্য ইচ্ছাশক্তির প্রতীক। "
                "বৃশ্চিক রাশির জাতক-জাতিকাদের মন অত্যন্ত গভীর ও রহস্যভেদী। তারা মানুষের আসল রূপ এক পলকেই চিনে নিতে পারেন "
                "এবং জীবনের যেকোনো কঠিন বিপর্যয় থেকেও ফিনিক্স পাখির মতো নতুন শক্তিতে জেগে উঠতে পারেন।"
            ),
            "strengths": [
                "অটল ইচ্ছাশক্তি, অদম্য মানসিক সহনশীলতা ও ঘুরে দাঁড়ানোর অসাধারণ ক্ষমতা",
                "গভীর মনস্তাত্ত্বিক দূরদৃষ্টি ও মিথ্যা বা প্রতারণা সহজেই ধরে ফেলার বিশেষ ক্ষমতা",
                "বিশ্বাসভাজন প্রিয়জনদের প্রতি আজীবন অটুট ও নিঃশর্ত আনুগত্য",
                "গভীর গবেষণা, গোপন বিষয়াদি ও আধ্যাত্মিক রহস্য উন্মোচনে অনন্য দক্ষতা",
            ],
            "cautions_and_pitfalls": [
                "গভীর ক্ষোভ, ঈর্ষা বা প্রতিশোধস্পৃহা মনে পুষে রাখা থেকে সাবধান",
                "অতিরিক্ত গোপনীয়তা ও অহেতুক সন্দেহবাতিকতা যা আপনজনদের দূরে সরিয়ে দেয়",
                "সবকিছুতেই চরমপন্থা (Extreme All-or-Nothing) অবলম্বন করে নিজের ক্ষতি করা",
                "প্রজনন অঙ্গ, পেলভিক বা মূত্রনালীর প্রদাহজনিত সমস্যা থেকে সাবধান",
                "অতীতের বিশ্বাসঘাতকতা বা আঘাত সহজে ক্ষমা করতে না পারা",
            ],
            "beneficial_actions_and_remedies": [
                "প্রতিদিন ক্ষমাশীলতার অনুশীলন করুন এবং মনের দীর্ঘদিনের ক্ষোভ মুক্ত করুন",
                "প্রতি মঙ্গলবার ভগবান শিবের মহামৃত্যুঞ্জয় মন্ত্র বা হনুমান চালিসা পাঠ করুন",
                "স্বেচ্ছায় রক্তদান করুন অথবা মঙ্গলবার লাল মুসুর ডাল ও তামা অভাবীদের দান করুন",
                "মনের তীব্র একাগ্রতাকে গভীর গবেষণা, আধ্যাত্মিক চর্চা বা কঠিন কাজে লাগান",
                "প্রজনন ও মূত্রনালীর স্বাস্থ্যবিধি মেনে চলুন এবং গ্রাউন্ডিং মেডিটেশন করুন",
            ],
            "career_fields": [
                "গোয়েন্দা বিভাগ, সাইবার সিকিউরিটি, গোয়েন্দা সাংবাদিকতা ও ফরেনসিক",
                "শল্যচিকিৎসা (সার্জারি), প্যাথলজি, সাইকিয়াট্রি ও সাইকোথেরাপি",
                "খনিজ সম্পদ, ভূতত্ত্ব, পেট্রোলিয়াম ও গভীর সমুদ্র অনুসন্ধান",
                "জ্যোতির্বিদ্যা, গুপ্তবিদ্যা (Occult), অধিবিদ্যা ও গভীর বৈজ্ঞানিক গবেষণা",
                "জরুরি সংকট ব্যবস্থাপনা ও ডিফেন্স স্ট্র্যাটেজি",
            ],
            "lucky_color": "গাঢ় খয়েরি, রক্তলাল ও মেটালিক কালো",
            "lucky_gemstone": "রক্ত প্রবাল (Red Coral)",
            "lucky_day": "মঙ্গলবার",
            "ruling_deity": "দেবাদিদেব মহাদেব ও শ্রী হনুমানজি",
            "compatible_rashis": ["কর্কট", "মীন", "কন্যা", "মকর"],
        },
        "hi": {
            "name": "वृश्चिक",
            "element": "जल तत्व",
            "modality": "स्थिर राशि (Fixed)",
            "polarity": "स्त्री / ऋणात्मक (सम राशि)",
            "body_parts": "प्रजनन अंग, मूत्राशय, पेल्विस और उत्सर्जन तंत्र",
            "nature": "गंभीर, दृढ़-संकल्पी, रहस्यमयी, परिवर्तनकारी और निष्ठावान",
            "overview": (
                "मंगल देव द्वारा शासित वृश्चिक राशि गूढ़ रहस्य, गहन इच्छाशक्ति और रूपांतरण की प्रतीक है। "
                "वृश्चिक राशि के जातक तीव्र अंतर्दृष्टि, अटूट संकल्प और साहसी मनोबल वाले होते हैं। "
                "वे जीवन की सबसे बड़ी विपदाओं से भी राख से उठने वाले फीनिक्स की तरह पुनः उठ खड़े होने की क्षमता रखते हैं।"
            ),
            "strengths": [
                "अटूट इच्छाशक्ति, मानसिक दृढ़ता और जीवन को पुनः संवारने की अद्भुत क्षमता",
                "गहरी मनोवैज्ञानिक पकड़ और झूठ को तुरंत पकड़ लेने की स्वाभाविक योग्यता",
                "जिन पर भरोसा करते हैं, उनके प्रति आजीवन सच्ची वफादारी",
                "अनुसंधान, गुप्त विद्याओं और कठिन रहस्यों को सुलझाने में महारत",
            ],
            "cautions_and_pitfalls": [
                "मन में गहरा क्रोध, ईर्ष्या या बदले की भावना रखने से बचें",
                "अत्यधिक गोपनीयता और अविश्वास के कारण अपनों को दूर करना",
                "चरमपंथी सोच (सब कुछ या कुछ नहीं) के कारण आत्मघाती निर्णय लेना",
                "प्रजनन अंगों, मूत्राशय और पेल्विक क्षेत्र के संक्रमण के प्रति सतर्क रहें",
                "अतीत के विश्वासघात या भावनात्मक चोटों को क्षमा न कर पाना",
            ],
            "beneficial_actions_and_remedies": [
                "मन में क्षमा भाव रखें और पुराने गिले-शिकवे त्यागने का अभ्यास करें",
                "प्रत्येक मंगलवार को महामृत्युंजय मंत्र या हनुमान चालीसा का पाठ करें",
                "स्वैच्छिक रक्तदान करें या मंगलवार को लाल मसूर की दाल और तांबे का दान करें",
                "अपनी तीव्र ऊर्जा को गूढ़ अनुसंधान, अध्यात्म या रचनात्मक कार्यों में लगाएं",
                "शारीरिक स्वच्छता पर विशेष ध्यान दें और दैनिक ध्यान का अभ्यास करें",
            ],
            "career_fields": [
                "जासूसी विभाग, खुफिया एजेंसी, साइबर सुरक्षा एवं फॉरेंसिक विज्ञान",
                "शल्य चिकित्सा (सर्जरी), पैथोलॉजी एवं मनोचिकित्सा",
                "खनन, पेट्रोलियम, भूविज्ञान एवं समुद्री इंजीनियरिंग",
                "ज्योतिष, गूढ़ रहस्य विज्ञान, अध्यात्म एवं गहन शोध",
                "आपदा प्रबंधन एवं रक्षा रणनीति",
            ],
            "lucky_color": "गहरा महरून, रस्ट ब्राउन एवं लाल",
            "lucky_gemstone": "लाल मूंगा (Red Coral)",
            "lucky_day": "मंगलवार",
            "ruling_deity": "भगवान शिव एवं श्री हनुमान",
            "compatible_rashis": ["कर्क", "मीन", "कन्या", "मकर"],
        },
    },

    # -------------------------------------------------------------------------
    # 8. SAGITTARIUS (ধনু / धनु)
    # -------------------------------------------------------------------------
    8: {
        "en": {
            "name": "Sagittarius",
            "element": "Fiery",
            "modality": "Dual / Common",
            "polarity": "Masculine / Positive (Odd sign)",
            "body_parts": "Thighs, hips, femur, sciatic nerve, liver, arterial system",
            "nature": "Philosophical, optimistic, adventurous, visionary, candid, truth-seeking",
            "overview": (
                "Ruled by Jupiter, Sagittarius is the seeker of universal truth, wisdom, and higher "
                "learning. Moon in Sagittarius individuals possess boundless optimism, expansive vision, "
                "and an adventurous spirit. They are guided by spiritual ideals and a generous philosophy of life."
            ),
            "strengths": [
                "Boundless optimism and infectious positive enthusiasm",
                "Deep philosophical wisdom and visionary forward-thinking",
                "Generous heart and moral commitment to universal truth",
                "Love for adventure, intercultural learning, and exploration",
            ],
            "cautions_and_pitfalls": [
                "Over-promising and taking reckless gambles due to blind optimism",
                "Blunt, tactless honesty that unintentionally hurts loved ones",
                "Restlessness and abandoning routine duties for new adventures",
                "Vulnerability to liver strain, weight gain, and hip/thigh injuries",
                "Self-righteous dogmatism and preaching to others unnecessarily",
            ],
            "beneficial_actions_and_remedies": [
                "Ground expansive dreams with pragmatic milestones and realistic timelines",
                "Worship Lord Vishnu or Brihaspati on Thursdays; chant `Om Gram Greem Graum Sah Gurave Namaha`",
                "Respect spiritual gurus, teachers, and elders with genuine devotion",
                "Donate yellow split chickpeas (chana dal), turmeric, or yellow fruits on Thursdays",
                "Protect liver health by moderating heavy fats, sugars, and alcohol intake",
            ],
            "career_fields": [
                "Higher education, philosophy, university professorship & academia",
                "International law, diplomacy, foreign trade & cross-border consultancy",
                "Publishing, religious leadership & spiritual mentorship",
                "Travel, tourism, aviation & wildlife conservation",
                "Judiciary, ethics advisory & sports management",
            ],
            "lucky_color": "Golden Yellow, Saffron, Royal Blue & Purple",
            "lucky_gemstone": "Yellow Sapphire (Pukhraj)",
            "lucky_day": "Thursday",
            "ruling_deity": "Lord Vishnu & Lord Brihaspati",
            "compatible_rashis": ["Aries", "Leo", "Libra", "Aquarius"],
        },
        "bn": {
            "name": "ধনু",
            "element": "অগ্নি তত্ত্ব (Fire)",
            "modality": "দ্বিস্বভাব রাশি (Dual)",
            "polarity": "পুরুষ / ধনাত্মক (বিষম রাশি)",
            "body_parts": "উরু, নিতম্ব, ফিমার অস্থি, যকৃৎ (লিভার) ও ধমনী",
            "nature": "দার্শনিক, আশাবাদী, সত্যসন্ধানী, দূরদর্শী, মুক্তমনা ও উদার",
            "overview": (
                "দেবগুরু বৃহস্পতি দ্বারা শাসিত ধনু রাশি হলো জ্ঞান, প্রজ্ঞা ও উচ্চতর দর্শনের প্রতীক। "
                "ধনু রাশির জাতক-জাতিকারা সীমাহীন আশাবাদ ও সত্যের সন্ধানী। তারা ভ্রমণ, বিভিন্ন সংস্কৃতি সম্পর্কে জ্ঞান অর্জন "
                "এবং আধ্যাত্মিক মূল্যবোধকে জীবনে সর্বোচ্চ স্থান দিয়ে থাকেন।"
            ),
            "strengths": [
                "সীমাহীন ইতিবাচক দৃষ্টিভঙ্গি ও মানুষকে অনুপ্রাণিত করার অদ্ভুত ক্ষমতা",
                "গভীর দার্শনিক প্রজ্ঞা ও সুদূরপ্রসারী চিন্তাচেতনা",
                "সত্যের প্রতি অবিচল নিষ্ঠা ও মুক্তহস্ত উদারতা",
                "ভ্রমণপ্রিয়তা ও নতুন দিগন্ত উন্মোচনের নিরন্তর আগ্রহ",
            ],
            "cautions_and_pitfalls": [
                "অতিরিক্ত আশাবাদী হয়ে বিচার-বিবেচনা ছাড়া অন্ধ ঝুঁকি নেওয়া",
                "অবাস্তব প্রতিশ্রুতি দেওয়া যা ভবিষ্যতে রক্ষা করা সম্ভব হয় না",
                "অতিরিক্ত স্পষ্টবক্তা হতে গিয়ে অন্যের অনুভূতিতে আঘাত হানা",
                "লিভারের সমস্যা, মেদবৃদ্ধি এবং নিতম্ব বা উরুর আঘাত থেকে সাবধান",
                "আইনি জটিলতা বা অসাবধান আর্থিক বাজি ধরা থেকে বিরত থাকুন",
            ],
            "beneficial_actions_and_remedies": [
                "কথা দেওয়ার আগে নিজের বাস্তবতা ও সক্ষমতা যাচাই করুন",
                "প্রতি বৃহস্পতিবার ভগবান শ্রী হরি বিষ্ণু বা বৃহস্পতির মন্ত্র পাঠ করুন",
                "কপালে হলুদ চন্দনের তিলক লাগান এবং গুরুজনদের সেবা করুন",
                "বৃহস্পতিবার ছোলার ডাল, হলুদ ফল বা ধর্মীয় পুস্তক অভাবীদের দান করুন",
                "লিভার সুস্থ রাখতে অতিরিক্ত তেল-চর্বিযুক্ত খাবার এড়িয়ে চলুন",
            ],
            "career_fields": [
                "উচ্চশিক্ষা, বিশ্ববিদ্যালয় অধ্যাপনা ও গবেষণা",
                "আন্তর্জাতিক আইন, কূটনীতি ও বৈদেশিক বাণিজ্য",
                "প্রকাশনা, আধ্যাত্মিক দিকনির্দেশনা ও মোটিভেশনাল স্পিকিং",
                "পর্যটন, বিমান পরিবহন ও বন্যপ্রাণী সংরক্ষণ",
                "বিচার বিভাগ, নীতিশাস্ত্র ও স্পোর্টস ম্যানেজমেন্ট",
            ],
            "lucky_color": "সোনালি হলুদ, জাফরান ও গাঢ় বেগুনি",
            "lucky_gemstone": "হলুদ পোখরাজ (Yellow Sapphire)",
            "lucky_day": "বৃহস্পতিবার",
            "ruling_deity": "ভগবান শ্রী হরি বিষ্ণু ও দেবগুরু বৃহস্পতি",
            "compatible_rashis": ["মেষ", "সিংহ", "তুলা", "কুম্ভ"],
        },
        "hi": {
            "name": "धनु",
            "element": "अग्नि तत्व",
            "modality": "द्विस्वभाव राशि (Dual)",
            "polarity": "पुरुष / धनात्मक (विषम राशि)",
            "body_parts": "जांघें, कूल्हे, यकृत (लिवर) और धमनियां",
            "nature": "दार्शनिक, आशावादी, सत्यप्रिय, दूरदर्शी, स्पष्टवादी और ज्ञानपिपासु",
            "overview": (
                "देवगुरु बृहस्पति द्वारा शासित धनु राशि ज्ञान, उच्च दर्शन और सत्य की प्रतीक है। "
                "धनु राशि के जातक सकारात्मक सोच, धर्मपरायणता और साहसी स्वभाव के धनी होते हैं। "
                "वे हमेशा सत्य और उच्च ज्ञान की खोज में रत रहते हैं और समाज को दिशा देने की क्षमता रखते हैं।"
            ),
            "strengths": [
                "असीम सकारात्मक ऊर्जा और दूसरों को प्रेरित करने की क्षमता",
                "गहरा दार्शनिक ज्ञान और भविष्यगामी दूरदर्शिता",
                "उदार हृदय, परोपकार की भावना और सत्यनिष्ठा",
                "यात्रा प्रियता और नई संस्कृतियों को जानने की तीव्र ललक",
            ],
            "cautions_and_pitfalls": [
                "अति-उत्साह में आकर बिना सोचे-समझे अंधाधुंध जोखिम उठाना",
                "ऐसे बड़े वादे कर बैठना जिन्हें बाद में पूरा करना असंभव हो",
                "अत्यधिक बेबाक बोलने के चक्कर में दूसरों की भावनाओं को ठेस पहुंचाना",
                "लिवर (यकृत) की समस्या, मोटापा और जांघों में चोट लगने से बचें",
                "सट्टेबाजी, जुए या कानूनी लापरवाही से हमेशा दूर रहें",
            ],
            "beneficial_actions_and_remedies": [
                "कोई भी वादा करने से पहले अपनी वास्तविक क्षमता का आकलन करें",
                "प्रत्येक गुरुवार को भगवान विष्णु की पूजा करें और पीले पुष्प अर्पित करें",
                "मस्तक पर पीले चंदन का तिलक लगाएं और अपने गुरुजनों का आशीर्वाद लें",
                "गुरुवार को चने की दाल, पीले फल या धार्मिक पुस्तकों का दान करें",
                "लिवर को स्वस्थ रखने के लिए अत्यधिक वसायुक्त और तैलीय भोजन से परहेज करें",
            ],
            "career_fields": [
                "उच्च शिक्षा, विश्वविद्यालय अध्यापन एवं शोध कार्य",
                "अंतर्राष्ट्रीय कानून, विदेश सेवा एवं कूटनीति",
                "प्रकाशन, धार्मिक उपदेश एवं आध्यात्मिक परामर्श",
                "पर्यटन, विमानन (एविएशन) एवं वन्यजीव संरक्षण",
                "न्यायपालिका एवं खेल प्रबंधन",
            ],
            "lucky_color": "पीला, केसरिया, गहरा नीला एवं बैंगनी",
            "lucky_gemstone": "पीला पुखराज (Yellow Sapphire)",
            "lucky_day": "गुरुवार",
            "ruling_deity": "भगवान श्री विष्णु एवं देवगुरु बृहस्पति",
            "compatible_rashis": ["मेष", "सिंह", "तुला", "कुंभ"],
        },
    },

    # -------------------------------------------------------------------------
    # 9. CAPRICORN (মকর / मकर)
    # -------------------------------------------------------------------------
    9: {
        "en": {
            "name": "Capricorn",
            "element": "Earthy",
            "modality": "Movable / Cardinal",
            "polarity": "Feminine / Negative (Even sign)",
            "body_parts": "Knees, bones, skeletal joints, teeth, skin, patella",
            "nature": "Pragmatic, disciplined, ambitious, patient, structured, persistent",
            "overview": (
                "Ruled by Saturn, Capricorn represents discipline, structure, and perseverance. "
                "Moon in Capricorn bestows a serious, dignified bearing, unshakeable stamina, and "
                "an ambition to climb the highest summits of accomplishment through patient effort. "
                "They are master organizers and builders of lasting legacies."
            ),
            "strengths": [
                "Iron discipline, steadfast patience, and tireless perseverance",
                "Mastery of long-term planning, organization, and execution",
                "Deep sense of duty, integrity, and accountability",
                "Calm maturity under crisis; emotional stability over time",
            ],
            "cautions_and_pitfalls": [
                "Pessimistic melancholia and excessive fixation on worst-case scenarios",
                "Workaholism neglecting emotional well-being and family bonds",
                "Emotional coldness or aloofness that repels warm friendships",
                "Vulnerability to knee pain, arthritis, dental issues, and dry skin",
                "Rigid austerity preventing personal enjoyment of hard-earned wealth",
            ],
            "beneficial_actions_and_remedies": [
                "Cultivate warm emotional openness with family and trusted peers",
                "Worship Lord Shiva or Lord Shani Dev on Saturdays; light sesame oil lamps",
                "Serve elder citizens, laborers, and physically challenged individuals with respect",
                "Donate black sesame seeds, mustard oil, dark blankets, or iron items on Saturdays",
                "Practice regular joint mobilization, knee stretching, and calcium nutrition",
            ],
            "career_fields": [
                "Corporate governance, industrial management & enterprise leadership",
                "Civil engineering, heavy infrastructure, architecture & construction",
                "Government administration, public policy & legal stewardship",
                "Real estate development, geology, mining & agriculture",
                "Finance, banking treasury & risk assessment",
            ],
            "lucky_color": "Charcoal Grey, Navy Blue, Forest Green & Black",
            "lucky_gemstone": "Blue Sapphire (Neelam) or Amethyst",
            "lucky_day": "Saturday",
            "ruling_deity": "Lord Shiva & Lord Shani Dev",
            "compatible_rashis": ["Taurus", "Virgo", "Scorpio", "Pisces"],
        },
        "bn": {
            "name": "মকর",
            "element": "পৃথ্বী তত্ত্ব (Earth)",
            "modality": "চর রাশি (Movable)",
            "polarity": "স্ত্রী / ঋণাত্মক (সম রাশি)",
            "body_parts": "হাঁটু, অস্থিসন্ধি, হাড়, দাঁত ও ত্বক",
            "nature": "পরিশ্রমী, বাস্তববাদী, সুশৃঙ্খল, ধৈর্যশীল, নীতিবান ও দায়িত্বশীল",
            "overview": (
                "কর্মফলদাতা শনিদেব দ্বারা শাসিত মকর রাশি হলো কঠোর পরিশ্রম, শৃঙ্খলা ও অবিচল লক্ষ্যের প্রতীক। "
                "মকর রাশির জাতক-জাতিকারা গম্ভীর স্বভাব ও অটল সংকল্পের অধিকারী। তারা ধীরে ধীরে কিন্তু দৃঢ় পদক্ষেপে "
                "সাফল্যের সর্বোচ্চ শিখরে আরোহণ করেন এবং দীর্ঘস্থায়ী কীর্তি গড়ে তোলেন।"
            ),
            "strengths": [
                "লৌহকঠিন শৃঙ্খলা, অপরিসীম ধৈর্য এবং অক্লান্ত পরিশ্রম করার ক্ষমতা",
                "দীর্ঘমেয়াদী পরিকল্পনা ও সংগঠন পরিচালনার অসাধারণ পারদর্শিতা",
                "উচ্চ দায়িত্ববোধ, কর্তব্যনিষ্ঠা ও প্রগাঢ় সততা",
                "যেকোনো সংকটে শান্ত থেকে সমাধান করার পরিপক্কতা",
            ],
            "cautions_and_pitfalls": [
                "কাজে অতিরিক্ত ডুবে থেকে পরিবার ও নিজের মানসিক স্বাস্থ্যের ক্ষতি করা",
                "অতিমাত্রায় সন্দেহপ্রবণ ও কঠোর আচরণ যা ভালোবাসার মানুষদের ব্যথিত করে",
                "হাঁটু, অস্থিসন্ধি (বাত) এবং ত্বকের সমস্যা থেকে সাবধান",
                "ভবিষ্যতের ভয়ে বর্তমানের আনন্দকে উপভোগ করতে না পারা",
                "অন্যের উপর সহজে বিশ্বাস করতে না পেরে একাকীত্বে ভোগা",
            ],
            "beneficial_actions_and_remedies": [
                "কাজের পাশাপাশি পরিবার ও নিজের আনন্দের জন্য সময় বরাদ্দ করুন",
                "প্রতি শনিবার শনি চালিসা পাঠ বা হনুমানজির পুজো করুন",
                "শনিবার সর্ষের তেল, কালো তিল, ছাতা বা জুতো অভাবী মানুষদের দান করুন",
                "কঠোর মনোভাব পরিহার করে অন্যদের প্রতি ক্ষমাশীল ও সহানুভূতিশীল হোন",
                "হাঁটু ও হাড়ের সুস্থতায় ক্যালসিয়ামযুক্ত খাবার ও নিয়মিত হাঁটার অভ্যাস করুন",
            ],
            "career_fields": [
                "শিল্প প্রতিষ্ঠান পরিচালনা, কর্পোরেট সিইও ও উচ্চতর ব্যবস্থাপনা",
                "সিভিল ইঞ্জিনিয়ারিং, ব্রিজ-রাস্তা নির্মাণ ও ভারী পরিকাঠামো শিল্প",
                "সরকারি আমলাতন্ত্র, আইন প্রয়োগকারী সংস্থা ও জননীতি প্রণয়ন",
                "রিয়েল এস্টেট, খনি শিল্প, ধাতুবিদ্যা ও কৃষি ব্যবস্থাপনা",
                "ব্যাংকিং, ফিন্যান্সিয়াল রিস্ক অ্যাসেসমেন্ট ও অডিট",
            ],
            "lucky_color": "গাঢ় ধূসর, নেভি ব্লু ও কালো",
            "lucky_gemstone": "নীলা (Blue Sapphire) বা জামুনিয়া",
            "lucky_day": "শনিবার",
            "ruling_deity": "ভগবান দেবাদিদেব মহাদেব ও শনিদেব",
            "compatible_rashis": ["বৃষ", "কন্যা", "বৃশ্চিক", "মীন"],
        },
        "hi": {
            "name": "मकर",
            "element": "पृथ्वी तत्व",
            "modality": "चर राशि (Movable)",
            "polarity": "स्त्री / ऋणात्मक (सम राशि)",
            "body_parts": "घुटने, अस्थियां, जोड़, दांत और त्वचा",
            "nature": "व्यावहारिक, अनुशासित, महत्वाकांक्षी, गंभीर, दृढ़ और धैर्यवान",
            "overview": (
                "कर्मफलदाता शनि देव द्वारा शासित मकर राशि अनुशासन, परिश्रम और धैर्य की प्रतीक है। "
                "मकर राशि के जातक दृढ़ संकल्पी, दूरदर्शी और कठोर परिश्रमी होते हैं। "
                "वे अपने धैर्य और निरंतर प्रयासों के बल पर जीवन में सर्वोच्च सफलता हासिल करते हैं।"
            ),
            "strengths": [
                "फौलादी अनुशासन, अटूट धैर्य और अथक परिश्रम करने का माद्दा",
                "दीर्घकालिक योजना निर्माण और संगठन प्रबंधन में महारत",
                "कर्तव्यपरायणता, ईमानदारी और उच्च जवाबदेही",
                "संकट की घड़ी में भी शांत और परिपक्व निर्णय लेने की क्षमता",
            ],
            "cautions_and_pitfalls": [
                "काम के अत्यधिक बोझ तले दबकर परिवार और व्यक्तिगत स्वास्थ्य की अनदेखी करना",
                "अत्यधिक कठोर, निराशावादी या स्वार्थी दृष्टिकोण अपनाने से बचें",
                "घुटनों में दर्द, जोड़ों के विकार और त्वचा संबंधी समस्याओं के प्रति सतर्क रहें",
                "भविष्य के डर में आज के सुंदर पलों का आनंद न ले पाना",
                "दूसरों पर भरोसा न कर पाने के कारण एकाकीपन का शिकार होना",
            ],
            "beneficial_actions_and_remedies": [
                "काम के साथ-साथ परिवार और मनोरंजन के लिए भी समय निकालें",
                "प्रत्येक शनिवार को शनि चालीसा का पाठ करें और पीपल के नीचे सरसों के तेल का दीपक जलाएं",
                "शनिवार को सरसों का तेल, काले तिल, छाता या जूते निर्धनों को दान करें",
                "सहकर्मियों और अधीनस्थों के प्रति विनम्र और दयालु दृष्टिकोण रखें",
                "हड्डियों और घुटनों की मजबूती के लिए कैल्शियम युक्त आहार और व्यायाम करें",
            ],
            "career_fields": [
                "औद्योगिक प्रबंधन, कॉर्पोरेट नेतृत्व एवं वरिष्ठ प्रशासनिक पद",
                "सिविल इंजीनियरिंग, भवन निर्माण एवं भारी बुनियादी ढांचा",
                "सरकारी सेवा, कानून एवं लोकनीति निर्माण",
                "रियल एस्टेट, खनन, भूविज्ञान एवं कृषि व्यवसाय",
                "वित्तीय जोखिम प्रबंधन, बैंकिंग एवं ट्रेजरी",
            ],
            "lucky_color": "गहरा नीला, स्लेटी (ग्रे) एवं काला",
            "lucky_gemstone": "नीलम (Blue Sapphire) या जमुनिया",
            "lucky_day": "शनिवार",
            "ruling_deity": "भगवान शिव एवं श्री शनिदेव",
            "compatible_rashis": ["वृषभ", "कन्या", "वृश्चिक", "मीन"],
        },
    },

    # -------------------------------------------------------------------------
    # 10. AQUARIUS (কুম্ভ / कुंभ)
    # -------------------------------------------------------------------------
    10: {
        "en": {
            "name": "Aquarius",
            "element": "Airy",
            "modality": "Fixed / Static",
            "polarity": "Masculine / Positive (Odd sign)",
            "body_parts": "Ankles, shins, calves, circulatory system, oxygenation",
            "nature": "Humanitarian, visionary, inventive, independent, unconventional, progressive",
            "overview": (
                "Ruled by Saturn (and associated with modern Uranus), Aquarius represents the water-bearer "
                "pouring the waters of collective wisdom upon humanity. Moon in Aquarius individuals possess "
                "an original intellect, egalitarian vision, and deep concern for social progress. "
                "They are forward-thinking innovators who champion freedom and community welfare."
            ),
            "strengths": [
                "Trailblazing originality, innovative genius, and scientific foresight",
                "Deep humanitarian altruism and commitment to social equality",
                "Free-thinking objectivity unswayed by emotional biases",
                "Inclusive, egalitarian friendship network embracing all walks of life",
            ],
            "cautions_and_pitfalls": [
                "Emotional detachment and aloofness creating walls in close intimacy",
                "Rebelliousness for its own sake and stubborn intellectual pride",
                "Living too far in theoretical futures while ignoring current realities",
                "Vulnerability to poor lower-leg circulation, varicosities, and ankle sprains",
                "Erratic unpredictability baffling partners and colleagues",
            ],
            "beneficial_actions_and_remedies": [
                "Practice warm emotional vulnerability in private relationships",
                "Worship Lord Shiva or Lord Hanuman on Saturdays with blue flowers",
                "Engage actively in voluntary community service or animal welfare",
                "Donate dark blankets, winter coats, or footwear to the homeless",
                "Keep legs active with routine elevation, brisk walking, and calf stretches",
            ],
            "career_fields": [
                "Information technology, artificial intelligence, data science & robotics",
                "Aviation, aerospace engineering & renewable green energy",
                "Social reform, humanitarian NGOs, human rights law & community advocacy",
                "Astrology, astronomy, scientific research & futurism",
                "Broadcast media, digital communities & innovative inventions",
            ],
            "lucky_color": "Electric Blue, Cyan, Ultramarine & Dark Violet",
            "lucky_gemstone": "Blue Sapphire (Neelam) or Blue Topaz",
            "lucky_day": "Saturday",
            "ruling_deity": "Lord Shiva & Lord Kaal Bhairav",
            "compatible_rashis": ["Gemini", "Libra", "Aries", "Sagittarius"],
        },
        "bn": {
            "name": "কুম্ভ",
            "element": "বায়ু তত্ত্ব (Air)",
            "modality": "স্থির রাশি (Fixed)",
            "polarity": "পুরুষ / ধনাত্মক (বিষম রাশি)",
            "body_parts": "গোড়ালি, পায়ের নলা, রক্ত সঞ্চালন প্রক্রিয়া ও স্নায়ুতন্ত্র",
            "nature": "মানবতাবাদী, উদ্ভাবনী, মুক্তমনা, প্রগতিশীল, দূরদর্শী ও সমাজসংস্কারক",
            "overview": (
                "শনিদেবের শাসনাধীন কুম্ভ রাশি হলো বিশ্বকল্যাণ ও সার্বিক প্রজ্ঞার কলসের প্রতীক। "
                "কুম্ভ রাশির জাতক-জাতিকারা স্বাধীনচেতা, দূরদর্শী ও গভীর সমাজসচেতন ব্যক্তিত্বের অধিকারী। "
                "তারা গতানুগতিকতার বাইরে গিয়ে নতুন উদ্ভাবন ও মানবকল্যাণে অবদান রাখতে ভালোবাসেন।"
            ),
            "strengths": [
                "মৌলিক উদ্ভাবনী প্রতিভা ও যেকোনো বিষয়ে যুগান্তকারী দূরদর্শিতা",
                "গভীর মানবতাবাদ ও সামাজিক সাম্যের প্রতি নিঃস্বার্থ দায়বদ্ধতা",
                "পক্ষপাতহীন বস্তুনিষ্ঠ চিন্তা ও নিরপেক্ষ বিচারশক্তি",
                "সকল স্তরের মানুষের সাথে নির্দ্বিধায় বন্ধুত্ব গড়ার মানসিকতা",
            ],
            "cautions_and_pitfalls": [
                "আবেগহীনতা ও অতিরিক্ত দূরত্ব বজায় রেখে মানুষকে পর করে দেওয়া",
                "বিদ্রোহী স্বভাবের বশে যুক্তিসঙ্গত সামাজিক নিয়ম লঙ্ঘন করা",
                "নিজের মতামতের বাইরে অন্যের মতামতকে গুরুত্বহীন ভাবা",
                "রক্ত সঞ্চালনের সমস্যা, পায়ের গোড়ালি ও ভ্যারিকোজ ভেইনের সমস্যা থেকে সাবধান",
                "অতিরিক্ত আকাশকুসুম কল্পনা করে বাস্তব দায়িত্ব এড়িয়ে চলা",
            ],
            "beneficial_actions_and_remedies": [
                "কাছের মানুষদের সাথে মন খুলে অনুভূতি ভাগ করে নিন এবং দূরত্ব পরিহার করুন",
                "প্রতি শনিবার ভগবান ভৈরব বা শনিদেবের উপাসনা করুন",
                "অসহায়, প্রতিবন্ধী বা বয়স্ক মানুষদের সেবা ও সহায়তা করুন",
                "শনিবার কালো তিল, নীল বা কালো কম্বল অভাবীদের দান করুন",
                "পায়ের গোড়ালি ও রক্তসঞ্চালন ঠিক রাখতে নিয়মিত শরীরচর্চা করুন",
            ],
            "career_fields": [
                "ইনফরমেশন টেকনোলজি, কৃত্রিম বুদ্ধিমত্তা (AI) ও রোবোটিক্স",
                "মহাকাশ গবেষণা, এভিয়েশন ও পরিবেশবান্ধব নবায়নযোগ্য শক্তি",
                "সমাজকল্যাণ, মানবাধিকার রক্ষা ও অলাভজনক সংস্থা পরিচালনা",
                "জ্যোতির্বিদ্যা, জ্যোতিষশাস্ত্র ও বৈজ্ঞানিক উদ্ভাবন",
                "ইলেকট্রনিক্স ও আধুনিক ডিজিটাল প্রযুক্তি",
            ],
            "lucky_color": "ইলেকট্রিক ব্লু, আসমানী ও গাঢ় নীল",
            "lucky_gemstone": "নীলা (Blue Sapphire)",
            "lucky_day": "শনিবার",
            "ruling_deity": "দেবাদিদেব মহাদেব ও কালভৈরব",
            "compatible_rashis": ["মিথুন", "তুলা", "মেষ", "ধনু"],
        },
        "hi": {
            "name": "कुंभ",
            "element": "वायु तत्व",
            "modality": "स्थिर राशि (Fixed)",
            "polarity": "पुरुष / धनात्मक (विषम राशि)",
            "body_parts": "टखने, पिंडलियां, पैर और रक्त परिसंचरण तंत्र",
            "nature": "मानवतावादी, दूरदर्शी, स्वतंत्र, नवाचारी, वैज्ञानिक और उदार",
            "overview": (
                "शनि देव द्वारा शासित कुंभ राशि मानवता, स्वतंत्र विचार और प्रगति की प्रतीक है। "
                "कुंभ राशि के जातक लीक से हटकर सोचने वाले, वैज्ञानिक दृष्टिकोण रखने वाले और समाज सुधारक होते हैं। "
                "वे व्यक्तिगत स्वार्थ से ऊपर उठकर जनहित और सामूहिक उन्नति के लिए कार्य करते हैं।"
            ),
            "strengths": [
                "मौलिक और क्रांतिकारी सोच तथा दूरदर्शी वैज्ञानिक दृष्टिकोण",
                "मानव कल्याण और सामाजिक समानता के प्रति अटूट समर्पण",
                "पूर्वाग्रह मुक्त निष्पक्ष विश्लेषण और स्वतंत्र विचार",
                "सच्ची मित्रता और सभी वर्गों के लोगों को साथ लेकर चलने का भाव",
            ],
            "cautions_and_pitfalls": [
                "भावनात्मक रूप से अलग-थलग हो जाना और अपनों से दूरी बना लेना",
                "अनावश्यक विद्रोही रुख अपनाकर सामाजिक नियमों का उल्लंघन करना",
                "केवल अपनी सोच को सही मानकर दूसरों के दृष्टिकोण को नकारना",
                "रक्त परिसंचरण (सर्कुलेशन) की समस्या, टखनों और पैरों में दर्द से बचें",
                "हवाई कल्पनाओं में खोकर व्यावहारिक जिम्मेदारियों से भागना",
            ],
            "beneficial_actions_and_remedies": [
                "अपनों के साथ खुलकर अपनी भावनाएं साझा करें और आत्मीय संवाद बनाए रखें",
                "शनिवार को भगवान शिव, कालभैरव या शनिदेव की आराधना करें",
                "असहाय, वृद्ध और दिव्यांगजनों की निस्वार्थ भाव से सहायता करें",
                "शनिवार को काले तिल, नीले या काले कंबल का दान करें",
                "पैरों और टखनों की मजबूती के लिए नियमित व्यायाम और स्ट्रेचिंग करें",
            ],
            "career_fields": [
                "सूचना प्रौद्योगिकी, आर्टिफिशियल इंटेलिजेंस (AI) एवं डेटा साइंस",
                "विमानन, अंतरिक्ष विज्ञान एवं नवीकरणीय ऊर्जा",
                "समाज सेवा, मानवाधिकार एवं गैर-सरकारी संगठन (NGO)",
                "ज्योतिष, खगोल विज्ञान एवं वैज्ञानिक अनुसंधान",
                "डिजिटल मीडिया एवं आधुनिक इलेक्ट्रॉनिक्स",
            ],
            "lucky_color": "आसमानी, इलेक्ट्रिक नीला एवं गहरा जामुनी",
            "lucky_gemstone": "नीलम (Blue Sapphire) या नीला टोपाज",
            "lucky_day": "शनिवार",
            "ruling_deity": "भगवान शिव एवं श्री कालभैरव",
            "compatible_rashis": ["मिथुन", "तुला", "मेष", "धनु"],
        },
    },

    # -------------------------------------------------------------------------
    # 11. PISCES (মীন / मीन)
    # -------------------------------------------------------------------------
    11: {
        "en": {
            "name": "Pisces",
            "element": "Watery",
            "modality": "Dual / Common",
            "polarity": "Feminine / Negative (Even sign)",
            "body_parts": "Feet, toes, lymphatic system, pineal gland, immune system",
            "nature": "Compassionate, mystical, artistic, intuitive, imaginative, transcendent",
            "overview": (
                "Ruled by Jupiter, Pisces is the cosmic ocean where all boundaries dissolve into "
                "universal consciousness. Moon in Pisces endows boundless compassion, poetic imagination, "
                "dreamy eyes, and psychic empathy. They are natural healers and artists attuned to the "
                "invisible spiritual dimensions of existence."
            ),
            "strengths": [
                "Unbounded compassion, unconditional love, and spiritual empathy",
                "Profound artistic genius, poetic imagination, and musical gifts",
                "Potent psychic intuition, prophetic dreams, and spiritual receptivity",
                "Natural healing presence that calms troubled and suffering souls",
            ],
            "cautions_and_pitfalls": [
                "Escapism from harsh realities into daydreaming, avoidance, or addiction",
                "Vulnerability to exploitation and boundary erosion by toxic opportunists",
                "Martyrdom complex taking on others' suffering to the point of self-ruin",
                "Vulnerability to foot injuries, lymphatic sluggishness, and sleep disorders",
                "Vagueness, procrastination, and lack of practical grounding",
            ],
            "beneficial_actions_and_remedies": [
                "Establish firm personal boundaries; learn to say 'No' lovingly but firmly",
                "Worship Lord Vishnu or Lord Dattatreya on Thursdays; chant `Om Namo Bhagavate Vasudevaya`",
                "Feed fish in clean ponds/rivers with flour balls on Thursdays",
                "Donate yellow garments, saffron, or devotional books to hermits or temples",
                "Anchor dreams into reality through daily meditation and structured artistic output",
            ],
            "career_fields": [
                "Creative arts, cinema, poetry, music composition & creative writing",
                "Spiritual counseling, yoga therapy, energy healing & meditation teaching",
                "Marine biology, oceanography, shipping & maritime management",
                "Hospice care, charity foundations, psychiatric social work & rehabilitation",
                "Photography, filmmaking & esoteric metaphysical research",
            ],
            "lucky_color": "Aquamarine, Seafoam Green, Golden Yellow & Pearl",
            "lucky_gemstone": "Yellow Sapphire (Pukhraj) or Aquamarine",
            "lucky_day": "Thursday",
            "ruling_deity": "Lord Vishnu & Lord Shiva",
            "compatible_rashis": ["Cancer", "Scorpio", "Taurus", "Capricorn"],
        },
        "bn": {
            "name": "মীন",
            "element": "জল তত্ত্ব (Water)",
            "modality": "দ্বিস্বভাব রাশি (Dual)",
            "polarity": "স্ত্রী / ঋণাত্মক (সম রাশি)",
            "body_parts": "পায়ের পাতা, আঙুল, লিম্ফ্যাটিক সিস্টেম ও রোগ প্রতিরোধ ব্যবস্থা",
            "nature": "দয়ালু, আধ্যাত্মিক, কল্পনাপ্রবণ, শিল্পীসুলভ, সংবেদনশীল ও রহস্যসন্ধানী",
            "overview": (
                "দেবগুরু বৃহস্পতি দ্বারা শাসিত মীন রাশি হলো অনন্ত আধ্যাত্মিক মহাসাগরের প্রতীক। "
                "মীন রাশির জাতক-জাতিকারা পরম স্নেহশীল, দয়ালু ও স্বপ্নচারী মনের অধিকারী। "
                "তারা শিল্পের গভীর সমঝদার এবং মানুষের কষ্ট দূর করতে সর্বদা আন্তরিকভাবে এগিয়ে আসেন।"
            ),
            "strengths": [
                "অসীম সহানুভূতি, নিঃস্বার্থ ভালোবাসা ও গভীর আধ্যাত্মিক অনুভূতি",
                "অসাধারণ শৈল্পিক প্রতিভা, কাব্যিক কল্পনা ও সংগীতের সহজাত প্রেরণা",
                "তীব্র অতিন্দ্রীয় অন্তর্দৃষ্টি ও মানুষের মনের গূঢ় ভাব বোঝার ক্ষমতা",
                "পীড়িত ও ব্যথিত মানুষদের মানসিক শান্তি ও সান্ত্বনা দেওয়ার মহৎ গুণ",
            ],
            "cautions_and_pitfalls": [
                "বাস্তবতা এড়িয়ে অলীক কল্পনার জগতে পালিয়ে থাকার প্রবণতা (Escapism)",
                "অতিরিক্ত পরোপকারী হতে গিয়ে ধূর্ত মানুষদের প্রতারণার শিকার হওয়া",
                "মাদক, নেশা বা ক্ষতিকর অভ্যাসে সহজেই জড়িয়ে পড়ার ঝুঁকি",
                "পায়ের পাতা, লিম্ফ্যাটিক সিস্টেম এবং অনিদ্রাজনিত সমস্যা থেকে সাবধান",
                "স্পষ্ট সীমানা (Boundaries) নির্ধারণ করতে না পেরে মানসিক বিভ্রান্তি",
            ],
            "beneficial_actions_and_remedies": [
                "দয়াশীল হওয়ার পাশাপাশি সুস্থ ব্যক্তিত্বের সীমানা (Healthy Boundaries) তৈরি করুন",
                "প্রতি বৃহস্পতিবার ভগবান শ্রী সত্যনারায়ণ বা বিষ্ণু সহস্রনাম পাঠ করুন",
                "পুকুর বা নদীতে মাছকে আটার গুলি বা খাবার দিন",
                "হলুদ রঙের পোশাক, বেসন বা ধর্মীয় সামগ্রী বৃহস্পতিবার অভাবীদের দান করুন",
                "মনকে বিভ্রান্তি থেকে মুক্ত রাখতে নিয়মিত মেডিটেশন ও ধ্যান করুন",
            ],
            "career_fields": [
                "চারুকলা, চলচ্চিত্র, সংগীত পরিচালনা, কবিতা ও সাহিত্যচর্চা",
                "আধ্যাত্মিক পরামর্শদান, যোগথেরাপি, নিরাময়বিদ্যা ও মেডিটেশন",
                "সামুদ্রিক জীববিজ্ঞান, মৎস্যবিজ্ঞান ও নৌবাণিজ্য",
                "হাসপাতাল সেবা, সমাজসেবা ট্রাস্ট ও পুনর্বাসন কেন্দ্র পরিচালনা",
                "ফটোগ্রাফি, ভিজ্যুয়াল আর্ট ও আধ্যাত্মিক গবেষণা",
            ],
            "lucky_color": "সমুদ্র-সবুজ, অ্যাকোয়ামেরিন, হালকা হলুদ ও মুক্তা সাদা",
            "lucky_gemstone": "হলুদ পোখরাজ (Yellow Sapphire)",
            "lucky_day": "বৃহস্পতিবার",
            "ruling_deity": "ভগবান শ্রী হরি বিষ্ণু",
            "compatible_rashis": ["কর্কট", "বৃশ্চিক", "বৃষ", "মকর"],
        },
        "hi": {
            "name": "मीन",
            "element": "जल तत्व",
            "modality": "द्विस्वभाव राशि (Dual)",
            "polarity": "स्त्री / ऋणात्मक (सम राशि)",
            "body_parts": "पैर के पंजे, तलवे, लसीका तंत्र और रोग प्रतिरोधक प्रणाली",
            "nature": "दयालु, आध्यात्मिक, कल्पनाशील, कलाप्रेमी, परोपकारी और संवेदनशील",
            "overview": (
                "देवगुरु बृहस्पति द्वारा शासित मीन राशि मोक्ष, करुणा और आध्यात्मिक सागर की प्रतीक है। "
                "मीन राशि के जातक अत्यंत दयालु, संवेदनशील और उच्च कल्पना शक्ति के धनी होते हैं। "
                "वे दुखी और जरूरतमंद लोगों के प्रति स्वाभाविक सहानुभूति रखते हैं और एक जादुई हीलिंग ऊर्जा संजोए रहते हैं।"
            ),
            "strengths": [
                "असीम करुणा, निस्वार्थ प्रेम और गहरी आध्यात्मिक चेतना",
                "उत्कृष्ट कलात्मक प्रतिभा, काव्यात्मक कल्पना और संगीत का वरदान",
                "तीव्र अंतर्ज्ञान, पूर्वभास और सूक्ष्म जगत से जुड़ाव",
                "सहानुभूतिपूर्ण और दुखों को हरने वाली सुखद उपस्थिति",
            ],
            "cautions_and_pitfalls": [
                "कठिन परिस्थितियों का सामना करने के बजाय ख्याली दुनिया में भागना",
                "अति-उदारता के कारण चालाक लोगों द्वारा ठगे जाने का जोखिम",
                "किसी भी प्रकार के व्यसन, नशे या गलत आदतों के प्रति सजग रहें",
                "पैरों के तलवों में दर्द, अनिद्रा और रोग प्रतिरोधक क्षमता की कमजोरी",
                "स्पष्ट सीमाएं न बना पाने के कारण मानसिक भ्रम और पछतावा",
            ],
            "beneficial_actions_and_remedies": [
                "उदारता के साथ-साथ व्यावहारिक सीमाएं (Healthy Boundaries) तय करना सीखें",
                "गुरुवार को भगवान सत्यनारायण या गुरुदेव की पूजा करें",
                "नदी या तालाब में मछलियों को आटे की गोलियां खिलाएं",
                "गुरुवार को पीले वस्त्र, बेसन की मिठाई या धार्मिक पुस्तकें दान करें",
                "नकारात्मक विचारों को दूर करने के लिए दैनिक ध्यान और एकाग्रता का अभ्यास करें",
            ],
            "career_fields": [
                "ललित कला, सिनेमा, संगीत रचना, कविता एवं रचनात्मक लेखन",
                "आध्यात्मिक परामर्श, योग थेरेपी, ध्यान एवं प्राकृतिक चिकित्सा",
                "समुद्री जीव विज्ञान, जल प्रबंधन एवं नौवहन",
                "अस्पताल प्रबंधन, अनाथालय, वृद्धाश्रम एवं समाज कल्याण",
                "फोटोग्राफी, फिल्म निर्माण एवं गूढ़ तत्वज्ञान",
            ],
            "lucky_color": "हल्का पीला, समुद्री हरा एवं एक्वामरीन",
            "lucky_gemstone": "पीला पुखराज (Yellow Sapphire)",
            "lucky_day": "गुरुवार",
            "ruling_deity": "भगवान श्री सत्यनारायण",
            "compatible_rashis": ["कर्क", "वृश्चिक", "वृषभ", "मकर"],
        },
    },
}


def get_rashi_translations(rashi_index: int, lang: str = "en") -> dict:
    """Returns localized traits for requested rashi index and language,
    plus full all_translations dictionary for all 3 languages.
    """
    safe_idx = rashi_index % 12
    rashi_dict = RASHI_TRANSLATIONS.get(safe_idx, RASHI_TRANSLATIONS[0])
    selected = rashi_dict.get(lang, rashi_dict["en"])
    return {
        "selected": selected,
        "all": rashi_dict,
    }
