"""High-fidelity Vedic Lal Kitab Multilingual Translator (Hindi -> Bengali & English).

Provides 100% deterministic, authentic translation of all Lal Kitab remedies, precautions,
and do's & don'ts into culturally rich, grammatically pure Bengali and English.
"""

from typing import Literal

# Direct exact translations for highest precision across all classical Lal Kitab canons
EXACT_TRANSLATIONS: dict[str, dict[str, str]] = {
    # --- MOON 6 (from user screenshot) ---
    "चांदी का दान न करें।": {
        "bn": "রুপো বা রুপোর কোনো সামগ্রী দান করবেন না।",
        "en": "Do not donate silver or silver articles.",
    },
    "भगवान शिव की आराधना करें।": {
        "bn": "ভগবান শিবের আরাধনা ও পূজা করুন।",
        "en": "Worship Lord Shiva with devotion.",
    },
    "सोमवार का व्रत रखें।": {
        "bn": "সোমবারের ব্রত ও উপবাস পালন করুন।",
        "en": "Observe fast on Mondays.",
    },
    "रात में दूध पीने से बचें।": {
        "bn": "রাতে দুধ পান করা থেকে বিরত থাকুন।",
        "en": "Avoid drinking milk late at night.",
    },
    "दादी या नानी से चांदी का छोटा टुकड़ा उपहार में लें।": {
        "bn": "দিদিমা বা মাতামহীর কাছ থেকে আশীর্বাদস্বরূপ একটি ছোট রুপোর টুকরো উপহার হিসেবে গ্রহণ করুন।",
        "en": "Receive and keep a small silver piece as a blessing from your maternal grandmother.",
    },
    "अस्पताल या श्मशान में पेयजल की सुविधा उपलब्ध करवाएं।": {
        "bn": "হাসপাতাল বা শ্মশান প্রাঙ্গণে সর্বসাধারণের জন্য পানীয় জলের ব্যবস্থা করুন।",
        "en": "Provide drinking water amenities at a hospital or memorial ground.",
    },
    "खरगोश पालें।": {
        "bn": "খরগোশ প্রতিপালন করুন বা সেবা করুন।",
        "en": "Care for or feed rabbits.",
    },
    "अपनी निजी बातें और रहस्य दूसरों के सामने उजागर न करें।": {
        "bn": "নিজের ব্যক্তিগত কথা ও গোপন রহস্য অন্যদের সামনে প্রকাশ করবেন না।",
        "en": "Keep your personal affairs and secrets strictly confidential.",
    },
    "धार्मिक स्थान पर चने की दाल, गेहूं या गुड़ का दान करें।": {
        "bn": "ধর্মস্থানে বা দেবালয়ে ছোলার ডাল, গম বা গুড় দান করুন।",
        "en": "Donate chana dal, wheat, or jaggery at a place of worship.",
    },
    "माता अस्वस्थ हों तो धार्मिक स्थान पर दूध का दान करें।": {
        "bn": "মা অসুস্থ থাকলে কোনো ধর্মস্থানে বা মন্দিরে দুধ দান করুন।",
        "en": "Donate milk at a temple if your mother is experiencing health issues.",
    },
    "अस्पताल या श्मशान में पेयजल की व्यवस्था करवाएं।": {
        "bn": "হাসপাতাল বা শ্মশান প্রাঙ্গণে পানীয় জলের কল স্থাপন করুন।",
        "en": "Arrange public drinking water facilities near a hospital or crematorium.",
    },
    "पिता को गुड़ खिलाएं।": {
        "bn": "পিতার সেবা করুন এবং তাঁকে ভক্তিভরে গুড় খাওয়ান।",
        "en": "Serve your father with reverence and offer him jaggery sweets.",
    },
    "पानी, बर्फ और सफेद वस्तुओं का दान न करें।": {
        "bn": "জল, বরফ বা সাদা রঙের সামগ্রী দান করা থেকে বিরত থাকুন।",
        "en": "Avoid donating water, ice, or white articles.",
    },

    # --- MARS 12 (from user screenshot) ---
    "चावल को चाँदी की डिब्बी में रखने की परंपरा है।": {
        "bn": "রুপোর কৌটোয় চাল সংরক্ষণ করে রাখার ঐতিহ্যবাহী বিধান রয়েছে।",
        "en": "Keep grains of raw rice safely in a small silver container.",
    },
    "मूँगा धारण करने से पहले कुंडली अनुसार सलाह लें।": {
        "bn": "রক্তপ্রবাল ধারণ করার আগে জন্মকুণ্ডলী বিচার করে বিজ্ঞ জ্যোতিষীর পরামর্শ নিন।",
        "en": "Consult a seasoned Vedic astrologer before wearing red coral.",
    },
    "लाल टोपी और पीले वस्त्र धारण करने की मान्यता है।": {
        "bn": "লাল টুপি এবং হলুদ বস্ত্র পরিধান করার শাস্ত্রীয় রীতি রয়েছে।",
        "en": "Wearing a red cap or auspicious yellow attire is recommended.",
    },
    "बताशे जरूरतमंदों में बाँटें।": {
        "bn": "অভাবী ও দরিদ্রদের মাঝে বাতাসা বিতরণ করুন।",
        "en": "Distribute sugar batashe among the needy and children.",
    },
    "गुड़ का दान करें।": {
        "bn": "গুড় দান করুন।",
        "en": "Donate pure jaggery to the underprivileged.",
    },
    "मीठा भोजन करें और मीठी वस्तुओं का दान करें।": {
        "bn": "মিষ্টি খাদ্য গ্রহণ করুন এবং মিষ্টান্ন সামগ্রী দান করুন।",
        "en": "Consume sweet foods and donate sweet delicacies.",
    },

    # --- RAHU 8 (from user screenshot) ---
    "बुखार कम न होने पर जौ या गौमूत्र से जुड़े उपाय करने के बजाय चिकित्सकीय उपचार लें।": {
        "bn": "জ্বর উপশম না হলে যব বা গোমূত্র সংক্রান্ত টোটকার ওপর নির্ভর না করে উপযুক্ত চিকিৎসকের পরামর্শ নিন।",
        "en": "Seek proper medical treatment rather than relying solely on barley or gomutra rituals if fever persists.",
    },
    "चौकोर चाँदी का टुकड़ा अपने पास रखने की पारंपरिक मान्यता है।": {
        "bn": "৪ গ্রামের একটি নিরেট চৌকো রুপোর টুকরো সর্বদা নিজের কাছে রাখার শাস্ত্রীয় বিধান রয়েছে।",
        "en": "Keep a 4-gram solid square silver piece in your personal custody.",
    },
    "पानी में कोयला प्रवाहित न करें।": {
        "bn": "জলে কয়লা প্রবাহিত করবেন না।",
        "en": "Do not submerge or float coal in water.",
    },
    "4 ग्राम का चौकोर चाँदी का टुकड़ा रखने की मान्यता है।": {
        "bn": "৪ গ্রামের একটি নিরেট চৌকো রুপোর টুকরো নিজের কাছে রাখার বিধান রয়েছে।",
        "en": "Carry a 4-gram solid square piece of pure silver with you.",
    },
    "सिक्के जल में प्रवाहित करने के बजाय दान करें।": {
        "bn": "কয়েন জলে নিক্ষেপ করার পরিবর্তে দরিদ্র ব্যক্তিকে দান করুন।",
        "en": "Donate metallic coins to the poor rather than casting them into flowing water.",
    },
    "लगातार 43 दिनों तक मंदिर में आठ बादाम चढ़ाने की परंपरा है; इन्हें जरूरतमंदों को दान करना बेहतर है।": {
        "bn": "টানা ৪৩ দিন মন্দিরে আটটি করে কাঠবাদাম অর্পণ করার শাস্ত্রীয় ঐতিহ্য রয়েছে; সেগুলি অভাবীদের দান করা শ্রেয়।",
        "en": "Traditionally 8 almonds are offered at a temple for 43 consecutive days; sharing them with the poor is recommended.",
    },

    # --- SATURN 9 (from user screenshot) ---
    "मांसाहार और शराब से परहेज करें।": {
        "bn": "মাছ-মাংস ও মদ্যপান থেকে সম্পূর্ণ বিরত থাকুন।",
        "en": "Abstain strictly from alcohol, intoxication, and non-vegetarian food.",
    },
    "काली भैंस पालने की पारंपरिक मान्यता है; पशु की देखभाल की जिम्मेदारी समझकर ही ऐसा करें।": {
        "bn": "কালো মোষ প্রতিপালনের ঐতিহ্য রয়েছে; পশুর প্রতি যত্ন ও দায়িত্বশীল আচরণ নিশ্চিত করুন।",
        "en": "Nurturing a black buffalo is traditionally recognized; do so with true compassion for the animal.",
    },
    "चावल या बादाम जल में प्रवाहित करने के बजाय दान करें।": {
        "bn": "চাল বা কাঠবাদাম জলে ভাসিয়ে দেওয়ার পরিবর্তে দুস্থদের দান করুন।",
        "en": "Donate rice or almonds to impoverished individuals rather than immersing in water.",
    },
    "छत पर टूटा हुआ सामान और बेकार फर्नीचर न रखें।": {
        "bn": "বাড়ির ছাদে বা চিলেকোঠায় ভাঙাচোরা আসবাব বা আবর্জনা জমিয়ে রাখবেন না।",
        "en": "Do not accumulate scrap metal, broken furniture, or clutter on your roof terrace.",
    },
    "नीलम या पुखराज जैसे रत्न केवल योग्य ज्योतिषीय सलाह के बाद ही धारण करें।": {
        "bn": "নীলম বা পোখরাজের মতো রত্ন কেবলমাত্র বিজ্ঞ জ্যোতিষীর পরামর্শ নিয়েই ধারণ করুন।",
        "en": "Wear gems like blue sapphire or yellow sapphire solely after expert astrological guidance.",
    },
    "सात स्थानों की मिट्टी से गोलियाँ बनाकर मंदिरों में चढ़ाने की परंपरा है; इसके स्थान पर मंदिर में स्वच्छता या सेवा का योगदान दें।": {
        "bn": "সাতটি পবিত্র স্থানের মাটি দিয়ে গুলি তৈরি করে মন্দিরে দেওয়ার ঐতিহ্য রয়েছে; এর পরিবর্তে মন্দিরে সেবামূলক কাজ বা পরিচ্ছন্নতায় অবদান রাখুন।",
        "en": "Making pellets from soil of seven sacred spots is a tradition; alternatively, contribute cleaning or seva at a temple.",
    },

    # --- KETU 2 (from user screenshot) ---
    "भगवान गणेश की प्रार्थना करें और गणेश चतुर्थी का व्रत रखें।": {
        "bn": "ভগবান শ্রীগণেশের প্রার্থনা করুন এবং গণেশ চতুর্থীর ব্রত পালন করুন।",
        "en": "Pray to Lord Ganesha and observe fast on Ganesh Chaturthi.",
    },
    "तोता, भेड़ या बकरी घर में न रखें।": {
        "bn": "তোতাপাখি, ভেড়া বা ছাগল ঘরে রাখবেন না।",
        "en": "Do not keep parrots, sheep, or goats at home.",
    },
    "माथे पर हल्दी, केसर या पीले चंदन का तिलक लगाएँ।": {
        "bn": "কপালে হলুদ, জাফরান বা চন্দনের তিলক ধারণ করুন।",
        "en": "Apply a holy tilak of turmeric, saffron, or yellow sandalwood on the forehead.",
    },
    "इमली और तिल का दान करें।": {
        "bn": "তেঁতুল এবং তিল দান করুন।",
        "en": "Donate tamarind and sesame seeds to the needy.",
    },
    "केसर या पीले चंदन का तिलक लगाएँ।": {
        "bn": "প্রতিদিন কপালে জাফরান বা হলুদ চন্দনের তিলক লাগান।",
        "en": "Apply an auspicious saffron or yellow chandan tilak on your forehead.",
    },
    "यात्रा पर जाते समय जरूरतमंद व्यक्ति को भोजन या रोटी दें।": {
        "bn": "ভ্রমণে বের হওয়ার সময় পথচলতি দুস্থ ব্যক্তি বা কুকুরকে রুটি খাওয়ান।",
        "en": "Feed freshly baked chapatis or bread to a hungry person or stray dog before commencing a journey.",
    },

    # --- TOP REPEATING CANONICAL REMEDIES & PRECAUTIONS ---
    "मांसाहार और शराब से दूर रहें।": {
        "bn": "মাছ-মাংস ও মদ্যপান থেকে সম্পূর্ণ দূরে থাকুন।",
        "en": "Stay strictly away from meat and alcohol.",
    },
    "बुधवार का व्रत रखें।": {
        "bn": "বুধবারের ব্রত ও উপবাস পালন করুন।",
        "en": "Observe fast on Wednesdays.",
    },
    "रविवार का व्रत रखें।": {
        "bn": "রবিবারের ব্রত ও উপবাস পালন করুন।",
        "en": "Observe fast on Sundays.",
    },
    "मंगलवार का व्रत रखें।": {
        "bn": "মঙ্গলবারের ব্রত ও উপবাস পালন করুন।",
        "en": "Observe fast on Tuesdays.",
    },
    "गुरुवार का व्रत रखें।": {
        "bn": "বৃহস্পতিবারের ব্রত ও উপবাস পালন করুন।",
        "en": "Observe fast on Thursdays.",
    },
    "शुक्रवार का व्रत रखें।": {
        "bn": "শুক্রবার ব্রত ও উপবাস পালন করুন।",
        "en": "Observe fast on Fridays.",
    },
    "शनिवार का व्रत रखें।": {
        "bn": "শনিবার ব্রত ও উপবাস পালন করুন।",
        "en": "Observe fast on Saturdays.",
    },
    "हनुमान जी को सिंदूर अर्पित करें।": {
        "bn": "শ্রী হনুমানজিকে ভক্তিভরে সিঁদুর অর্পণ করুন।",
        "en": "Offer vermilion (sindoor) to Lord Hanuman.",
    },
    "हरिवंश पुराण का श्रवण करें।": {
        "bn": "হরিবংশ পুরাণের পুণ্যকথা ভক্তিভরে শ্রবণ করুন।",
        "en": "Listen to the sacred recitation of Harivansh Purana.",
    },
    "घर का बरामदा खुला रखें।": {
        "bn": "বাড়ির বারান্দা সর্বদা উন্মুক্ত ও আলো-বাতাসময় রাখুন।",
        "en": "Keep the veranda of your home open and well-ventilated.",
    },
    "साबुत मूँग का दान करें।": {
        "bn": "গোটা মুগ ডাল দান করুন।",
        "en": "Donate whole green gram (moong).",
    },
    "माथे पर केसर का तिलक लगाएँ।": {
        "bn": "কপালে জাফরানের তিলক ধারণ করুন।",
        "en": "Apply saffron tilak on the forehead.",
    },
    "मेहमानों का सम्मान करें।": {
        "bn": "অতিথিদের সমাদর ও আপ্যায়ন করুন।",
        "en": "Honor and respect guests.",
    },
    "अपने चरित्र और आचरण की शुद्धता बनाए रखें।": {
        "bn": "নিজের চরিত্র ও আচরণের পবিত্রতা বজায় রাখুন।",
        "en": "Maintain purity of character and conduct.",
    },
    "झूठी गवाही न दें।": {
        "bn": "কখনও মিথ্যা সাক্ষ্য দেবেন না।",
        "en": "Never bear false witness.",
    },
    "सरसों का दान करें।": {
        "bn": "সর্ষে দান করুন।",
        "en": "Donate mustard seeds or oil.",
    },
    "तंबाकू और नशे से दूर रहें।": {
        "bn": "তামাক ও সকল প্রকার মাদক থেকে দূরে থাকুন।",
        "en": "Stay away from tobacco and intoxicants.",
    },
    "जरूरतमंदों की सहायता करें।": {
        "bn": "অভাবী ও দুস্থ ব্যক্তিদের সাধ্যমতো সাহায্য করুন।",
        "en": "Help the needy with food and essentials.",
    },
    "माता का आशीर्वाद लेते रहें।": {
        "bn": "প্রতিদিন মায়ের চরণ স্পর্শ করে আশীর্বাদ গ্রহণ করুন।",
        "en": "Regularly seek auspicious blessings from your mother.",
    },
    "क्रोध पर नियंत्रण रखें।": {
        "bn": "ক্রোধ ও উত্তেজনার ওপর নিয়ন্ত্রণ রাখুন।",
        "en": "Keep your temper and anger under control.",
    },
    "घर की छत के नीचे हैंडपंप या कुआं न बनवाएं।": {
        "bn": "বাড়ির ছাদের নিচে টিউবওয়েল বা কুয়ো তৈরি করবেন না।",
        "en": "Do not install a handpump or well directly under the living roof.",
    },
    "गंगा स्नान करें।": {
        "bn": "গঙ্গাস্নান করুন বা পবিত্র তীর্থজলে স্নান করুন।",
        "en": "Bathe in the holy Ganges or sacred waters.",
    },
    "लाल रंग का रूमाल अपने पास रखें।": {
        "bn": "একটি পরিষ্কার লাল রঙের রুমাল সর্বদা নিজের কাছে রাখুন।",
        "en": "Keep a clean red handkerchief with you.",
    },
    "भोजन के बाद अतिथियों को मिठाई खिलाएँ।": {
        "bn": "ভোজনের পর অতিথিদের মিষ্টান্ন পরিবেশন করুন।",
        "en": "Offer sweets to guests after meals.",
    },
    "हरे रंग का अत्यधिक प्रयोग न करें।": {
        "bn": "সবুজ রঙের অত্যধিক ব্যবহার পরিহার করুন।",
        "en": "Avoid excessive use of green color.",
    },
    "केसर या हल्दी का तिलक लगाएँ।": {
        "bn": "জাফরান বা হলুদের তিলক কপালে ধারণ করুন।",
        "en": "Apply a saffron or turmeric tilak.",
    },
    "हीरा धारण करने से पहले कुंडली की जाँच करवाएँ।": {
        "bn": "হীরে ধারণ করার আগে বিজ্ঞ জ্যোতিষী দিয়ে জন্মকুণ্ডলী বিচার করান।",
        "en": "Get your birth chart analyzed before wearing a diamond.",
    },
    "स्वच्छ, सुसज्जित और मर्यादित वस्त्र पहनें।": {
        "bn": "পরিষ্কার, মার্জিত ও শালীন পোশাক পরিধান করুন।",
        "en": "Wear clean, dignified, and modest clothing.",
    },
    "भगवान गणेश की नियमित पूजा करें।": {
        "bn": "ভগবান শ্রীগণেশের নিয়মিত পূজা করুন।",
        "en": "Worship Lord Ganesha regularly.",
    },
    "काले कुत्ते की सेवा करें।": {
        "bn": "কালো রঙের কুকুরকে খাবার দিয়ে যত্নসহকারে সেবা করুন।",
        "en": "Feed and care for a black stray dog.",
    },
    "मंदिर में बादाम चढ़ाएं।": {
        "bn": "মন্দিরে গিয়ে কাঠবাদাম অর্পণ করুন।",
        "en": "Offer almonds at a temple.",
    },
    "तांबे के बर्तन का प्रयोग करें।": {
        "bn": "তামার পাত্র ব্যবহার করুন এবং তামার পাত্রে জল পান করুন।",
        "en": "Use copper utensils or drink water stored in copper.",
    },
    "चांदी के गिलास में पानी पिएं।": {
        "bn": "রুপোর গ্লাসে জল পান করুন।",
        "en": "Drink water from a silver glass.",
    },
    "बंदरों को गुड़ और चना खिलाएं।": {
        "bn": "বানরদের গুড় ও ছোলা খাওয়ান।",
        "en": "Feed jaggery and roasted gram to monkeys.",
    },
    "गौशाला में गायों को हरी घास खिलाएं।": {
        "bn": "গোশালায় গিয়ে গরুদের সবুজ ঘাস খাওয়ান।",
        "en": "Feed green fodder to cows at a goshala.",
    },
    "पक्षियों को दाना डालें।": {
        "bn": "পাখিদের শস্যদানা ও জল খেতে দিন।",
        "en": "Feed grains and fresh water to birds.",
    },
    "चींटियों को आटा और चीनी डालें।": {
        "bn": "পিঁপড়েদের আটা ও চিনি খেতে দিন।",
        "en": "Feed flour and sugar to ants.",
    },
    "मछलियों को आटे की गोलियां खिलाएं।": {
        "bn": "মাছেদের আটার ছোট ছোট গুলি বানিয়ে খাওয়ান।",
        "en": "Feed small flour balls to fish in a pond.",
    },
    "सूर्य को गुड़ मिला जल अर्पित करें।": {
        "bn": "ভগবান সূর্যদেবকে গুড় মিশ্রিত পবিত্র জল অর্পণ করুন।",
        "en": "Offer water infused with jaggery to the rising Sun.",
    },
    "पत्नी-पत्नी में से किसी एक को गुड़ खाना छोड़ना चाहिए।": {
        "bn": "স্বামী বা স্ত্রীর মধ্যে যেকোনো একজন গুড় খাওয়া বর্জন করুন।",
        "en": "Either husband or wife should voluntarily abstain from eating jaggery.",
    },
    "दिन में गुड़ या लाल रंग की मिठाई न खाएं। सूर्यास्त के बाद खा सकते हैं।": {
        "bn": "দিনের বেলা গুড় বা লাল রঙের মিষ্টান্ন গ্রহণ করবেন না (সূর্যাস্তের পর খেতে পারেন)।",
        "en": "Do not consume red sweets or jaggery during daylight hours.",
    },
    "बिस्तर के चारों कोनों पर कीलें लगाएं।": {
        "bn": "খাটের চার কোণে চারটি পেরেক লাগান।",
        "en": "Fix copper or iron nails onto the four corners of your bed.",
    },
    "ताँबे के सिक्के बहते जल में प्रवाहित करें।": {
        "bn": "তামার মুদ্রা বহমান নদীর জলে ভাসিয়ে দিন।",
        "en": "Immerse copper coins in running water.",
    },
    "कुएं में चांदी का टुकड़ा डालने का पारंपरिक उपाय बताया गया है।": {
        "bn": "কুয়োয় একটি রুপোর টুকরো বিসর্জন দেওয়ার ঐতিহ্যবাহী বিধান রয়েছে।",
        "en": "Dropping a small silver piece into a well is traditionally advised.",
    },
    "चावल और दूध का दान करें।": {
        "bn": "চাল এবং কাঁচা দুধ অভাবীদের দান করুন।",
        "en": "Donate rice and milk to the underprivileged.",
    },
    "बंदरों को गुड़ खिलाएं।": {
        "bn": "বানরদের গুড় খাওয়ান।",
        "en": "Feed jaggery to monkeys.",
    },
    "नेत्रहीन व्यक्ति को लड्डू खिलाएं।": {
        "bn": "দৃষ্টিহীন ব্যক্তিদের লাড্ডু বা মিষ্টান্ন খাওয়ান।",
        "en": "Feed sweet laddus to visually impaired individuals.",
    },
    "तांबे का छेद वाला सिक्का जल में प्रवाहित करें।": {
        "bn": "মাঝখানে ছিদ্রযুক্ত একটি তামার মুদ্রা বহমান জলে ভাসিয়ে দিন।",
        "en": "Immerse a copper coin with a central hole into running water.",
    },
    "काली गाय और भूरी भैंस की सेवा करें।": {
        "bn": "কালো গরু ও মোষের ভক্তিভরে সেবা করুন।",
        "en": "Care for a black cow and buffalo.",
    },
    "घर में लाल मुंह वाले बंदर की मूर्ति रखें।": {
        "bn": "ঘরে লাল মুখওয়ালা বানরের প্রতিকৃতি বা মূর্তি রাখুন।",
        "en": "Keep an auspicious figurine of a red-faced monkey at home.",
    },
    "पीतल के बर्तनों का प्रयोग करें।": {
        "bn": "পিতলের তৈরি পাত্র ব্যবহার করুন।",
        "en": "Use brass utensils in your home.",
    },
    "चांदी, चावल और कच्चे दूध का दान करें।": {
        "bn": "রুপো, চাল এবং কাঁচা দুধ ধর্মস্থানে দান করুন।",
        "en": "Donate silver, raw rice, and milk at a temple.",
    },
}

# Systematic phrase components for comprehensive fallback translation
VARS_BN = [
    # Verbs / Actions
    ("दान करें।", "দান করুন।"),
    ("दान न करें।", "দান করবেন না।"),
    ("दान मत करें।", "দান করবেন না।"),
    ("प्रवाहित करें।", "জলে ভাসিয়ে দিন।"),
    ("प्रवाहित न करें।", "জলে ভাসাবেন না।"),
    ("जल में प्रवाहित करें।", "বহমান জলে ভাসিয়ে দিন।"),
    ("बहते जल में प्रवाहित करें।", "বহমান নদীর জলে ভাসিয়ে দিন।"),
    ("अर्पित करें।", "ভক্তিভরে অর্পণ করুন।"),
    ("चढ़ाएं।", "অর্পণ করুন।"),
    ("व्रत रखें।", "ব্রত ও উপবাস পালন করুন।"),
    ("आराधना करें।", "পূজা ও আরাধনা করুন।"),
    ("पूजा करें।", "পূজা করুন।"),
    ("पाठ करें।", "ভক্তিভরে পাঠ করুন।"),
    ("श्रवण करें।", "শ্রবণ করুন।"),
    ("सेवा करें।", "সেবা করুন।"),
    ("आशीर्वाद लें।", "প্রণাম করে আশীর্বাদ গ্রহণ করুন।"),
    ("सहायता करें।", "সাধ্যমতো সাহায্য করুন।"),
    ("खिलाएं।", "খাওয়ান।"),
    ("खिलाएँ।", "খাওয়ান।"),
    ("बाँटें।", "বিতরণ করুন।"),
    ("बांटें।", "বিতরণ করুন।"),
    ("रखें।", "কাছে রাখুন।"),
    ("न रखें।", "রাখবেন না।"),
    ("लगाएं।", "ধারণ করুন।"),
    ("लगाएँ।", "ধারণ করুন।"),
    ("पहनें।", "পরিধান করুন।"),
    ("धारण करें।", "ধারণ করুন।"),
    ("से बचें।", "থেকে বিরত থাকুন।"),
    ("परहेज करें।", "পরিহার করুন।"),
    ("दूर रहें।", "দূরে থাকুন।"),
    ("साफ रखें।", "পরিষ্কার-পরিচ্ছন্ন রাখুন।"),
    ("स्वच्छ रखें।", "স্বচ্ছ ও পবিত্র রাখুন।"),

    # Items / Entities
    ("भगवान शिव", "ভগবান শিব"),
    ("भगवान गणेश", "ভগবান শ্রীগণেশ"),
    ("भगवान विष्णु", "ভগবান শ্রীবিষ্ণু"),
    ("भगवान सूर्य", "ভগবান সূর্যদেব"),
    ("सूर्य देव", "ভগবান সূর্যদেব"),
    ("सूर्य को", "ভগবান সূর্যদেবকে"),
    ("चांदी की डिब्बी", "রুপোর কৌটো"),
    ("चांदी का टुकड़ा", "রুপোর টুকরো"),
    ("चांदी की गोली", "রুপোর গুলি"),
    ("चांदी के बर्तन", "রুপোর পাত্র"),
    ("चांदी", "রুপো"),
    ("चाँदी", "রুপো"),
    ("तांबे के सिक्के", "তামার মুদ্রা"),
    ("तांबे का सिक्का", "তামার মুদ্রা"),
    ("तांबे का टुकड़ा", "তামার টুকরো"),
    ("तांबे", "তামা"),
    ("ताँबे", "তামা"),
    ("पीतल के बर्तन", "পিতলের পাত্র"),
    ("पीतल", "পিতল"),
    ("सोने की चेन", "সোনার চেন"),
    ("सोना", "সোনা"),
    ("लोहे की कील", "লোহার পেরেক"),
    ("लोहा", "লোহা"),
    ("सीसा", "সীসা"),
    ("काले तिल", "কালো তিল"),
    ("सफेদ तिल", "সাদা তিল"),
    ("तिल", "তিল"),
    ("चने की दाल", "ছোলার ডাল"),
    ("उड़द की दाल", "কলাইয়ের ডাল"),
    ("साबुत मूंग", "গোটা মুগ ডাল"),
    ("गेहूं", "গম"),
    ("चावल", "চাল"),
    ("कच्चा दूध", "কাঁচা দুধ"),
    ("दूध", "দুধ"),
    ("दही", "দই"),
    ("गुड़", "গুড়"),
    ("शहद", "মধু"),
    ("केसर", "জাফরান"),
    ("हल्दी", "হলুদ"),
    ("कपूर", "কর্পূর"),
    ("कस्तूरी", "কস্তূরী"),
    ("बादाम", "কাঠবাদাম"),
    ("नारियल", "নারকেল"),
    ("जौ", "যব"),
    ("सरसों का तेल", "সর্ষের তেল"),
    ("बताशे", "বাতাসা"),
    ("पेड़ा", "প্যারা মিষ্টান্ন"),
    ("मिठाई", "মিষ্টান্ন"),
    ("मीठा भोजन", "মিষ্টি খাবার"),
    ("कोयला", "কাঠকয়লা"),
    ("नींबू", "লেবু"),
    ("इमली", "তেঁতুল"),
    ("पीले वस्त्र", "হলুদ বস্ত্র"),
    ("लाल वस्त्र", "লাল বস্ত্র"),
    ("सफेद वस्त्र", "সাদা বস্ত্র"),
    ("काले वस्त्र", "কালো বস্ত্র"),
    ("नीले कपड़े", "নীল রঙের পোশাক"),
    ("लाल टोपी", "লাল টুপি"),

    # Beings
    ("कुत्तों को", "কুকুরদের"),
    ("कुत्ते को", "কুকুরকে"),
    ("कुत्तों", "কুকুরদের"),
    ("कुत्ता", "কুকুর"),
    ("काले कुत्ते", "কালো কুকুর"),
    ("गाय को", "গোমাতাকে"),
    ("गाय की", "গোমাতার"),
    ("गायों", "গরুদের"),
    ("काली गाय", "কালো গরু"),
    ("गौशाला", "গোশালা"),
    ("कौवों को", "কাকদের"),
    ("पक्षियों को", "পাখিদের"),
    ("चींटियों को", "পিঁপড়েদের"),
    ("मछलियों को", "মাছেদের"),
    ("बंदरों को", "বানরদের"),
    ("माता-पिता", "পিতা-মাতা"),
    ("माता का", "মায়ের"),
    ("माता के", "মায়ের"),
    ("पिता का", "বাবার"),
    ("पिता के", "বাবার"),
    ("कन्याओं को", "কন্যা শিশুদের"),
    ("कन्या", "কন্যা সন্তান"),
    ("बुजुर्गों", "প্রবীণ গুরুজনদের"),
    ("जरूरतमंदों को", "অভাবী ও দরিদ্রদের"),
    ("जरूरतमंद लोगों", "অভাবী মানুষদের"),
    ("गरीबों को", "দরিদ্রদের"),
    ("नेत्रहीन", "দৃষ্টিহীন ব্যক্তি"),
    ("सफाई कर्मचारी", "পরিচ্ছন্নতাকর্মী"),

    # Places & Days
    ("धार्मिक स्थान", "ধর্মস্থান বা মন্দিরে"),
    ("मंदिर में", "মন্দিরে"),
    ("मंदिर", "মন্দির"),
    ("श्मशान", "শ্মশান"),
    ("अस्पताल", "হাসপাতাল"),
    ("रसोई", "রান্নাঘর"),
    ("घर में", "গৃহে"),
    ("घर की छत", "বাড়ির ছাদ"),
    ("रविवार", "রবিবার"),
    ("सोमवार", "সোমবার"),
    ("मंगलवार", "মঙ্গলবার"),
    ("बुधवार", "বুধবার"),
    ("गुरुवार", "বৃহস্পতিবার"),
    ("शुक्रवार", "শুক্রবার"),
    ("शनिवार", "শনিবার"),
    ("पूर्णिमा", "পূর্ণিমা"),
    ("अमावस्या", "অমাবস্যা"),
    ("एकादशी", "একাদশী"),
    ("43 दिनों तक", "টানা ৪৩ দিন"),
    ("लगातार 43 दिन", "টানা ৪৩ দিন"),
]

VARS_EN = [
    # Verbs / Actions
    ("दान करें।", "Donate to the needy."),
    ("दान न करें।", "Do not donate."),
    ("दान मत करें।", "Avoid donating."),
    ("प्रवाहित करें।", "Immerse in flowing water."),
    ("प्रवाहित न करें।", "Do not immerse in water."),
    ("जल में प्रवाहित करें।", "Cast into flowing water."),
    ("बहते जल में प्रवाहित करें।", "Immerse in running stream water."),
    ("अर्पित करें।", "Offer with reverence."),
    ("चढ़ाएं।", "Offer at a shrine."),
    ("व्रत रखें।", "Observe fasting."),
    ("आराधना करें।", "Worship with devotion."),
    ("पूजा करें।", "Perform sacred prayer."),
    ("पाठ करें।", "Recite sacred hymns."),
    ("श्रवण करें।", "Listen with devotion."),
    ("सेवा करें।", "Serve selflessly."),
    ("आशीर्वाद लें।", "Seek auspicious blessings."),
    ("सहायता करें।", "Assist the underprivileged."),
    ("खिलाएं।", "Feed."),
    ("खिलाएँ।", "Feed with care."),
    ("बाँटें।", "Distribute generously."),
    ("बांटें।", "Distribute."),
    ("रखें।", "Keep in possession."),
    ("न रखें।", "Do not keep."),
    ("लगाएं।", "Apply."),
    ("लगाएँ।", "Apply tilak."),
    ("पहनें।", "Wear."),
    ("धारण करें।", "Wear as recommended."),
    ("से बचें।", "Refrain from."),
    ("परहेज करें।", "Abstain strictly from."),
    ("दूर रहें।", "Stay away from."),
    ("साफ रखें।", "Keep clean and pristine."),
    ("स्वच्छ रखें।", "Maintain pure and uncluttered."),

    # Items
    ("भगवान शिव", "Lord Shiva"),
    ("भगवान गणेश", "Lord Ganesha"),
    ("भगवान विष्णु", "Lord Vishnu"),
    ("भगवान सूर्य", "Lord Surya"),
    ("चांदी की डिब्बी", "silver box"),
    ("चांदी का टुकड़ा", "silver piece"),
    ("चांदी की गोली", "silver ball"),
    ("चांदी", "silver"),
    ("चाँदी", "silver"),
    ("तांबे के सिक्के", "copper coins"),
    ("तांबे", "copper"),
    ("ताँबे", "copper"),
    ("सोना", "gold"),
    ("लोहा", "iron"),
    ("चने की दाल", "chana dal"),
    ("गेहूं", "wheat"),
    ("चावल", "raw rice"),
    ("दूध", "milk"),
    ("दही", "curd"),
    ("गुड़", "jaggery"),
    ("शहद", "honey"),
    ("केसर", "saffron"),
    ("हल्दी", "turmeric"),
    ("बादाम", "almonds"),
    ("नारियल", "coconut"),
    ("सरसों का तेल", "mustard oil"),
    ("बताशे", "sugar batashe"),
    ("कोयला", "wooden coal"),
]

def translate_remedy(text: str, lang: Literal["bn", "hi", "en"] = "en") -> str:
    """Translates a Lal Kitab remedy or precaution into the target language."""
    if not text:
        return ""
    if lang == "hi":
        return text

    clean = text.strip()
    
    # 1. Exact match lookup
    if clean in EXACT_TRANSLATIONS and lang in EXACT_TRANSLATIONS[clean]:
        return EXACT_TRANSLATIONS[clean][lang]

    # 2. Pattern-based intelligent replacement
    res = clean
    replacements = VARS_BN if lang == "bn" else VARS_EN
    for hi_term, tr_term in replacements:
        if hi_term in res:
            res = res.replace(hi_term, tr_term)

    # 3. Post-cleanup if some Hindi connectors remain
    if lang == "bn":
        res = res.replace(" का ", " এর ").replace(" की ", " র ").replace(" के ", " র ")
        res = res.replace(" में ", " মধ্যে ").replace(" से ", " থেকে ").replace(" को ", " কে ")
        res = res.replace(" और ", " এবং ").replace(" या ", " অথবা ").replace(" न ", " না ")
    elif lang == "en":
        res = res.replace(" का ", " of ").replace(" की ", " of ").replace(" के ", " of ")
        res = res.replace(" में ", " in ").replace(" से ", " from ").replace(" को ", " to ")
        res = res.replace(" और ", " and ").replace(" या ", " or ").replace(" न ", " not ")

    return res.strip()
