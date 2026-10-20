"""Authentic Samudrik Shastra (হস্তরেখা বিচার / Palmistry) rule seeds.

Every threshold is grounded in classical Vedic chiromancy and hand geometric metrics:
- Hand elemental types (Earth, Air, Fire, Water)
- Major lines: Heart (হৃদয়), Head (মস্তিষ্ক), Life (জীবন), Fate (ভাগ্য), Sun (রবি)
- Planetary mounts: Jupiter, Saturn, Sun, Mercury, Venus, Moon
- Finger biometrics: 2D:4D ratios, pinky reach, thumb angle
"""

from app.models.palm_reading import PalmFeature

RULES: list[dict] = [
    # ------------------------------------------------------------- 1. HAND TYPE
    {
        "feature": PalmFeature.HAND_TYPE,
        "option": "earth_hand",
        "label": "পৃথ্বী হস্ত (Earth Hand - Square Palm, Short Fingers)",
        "conditions": [
            {"metric": "palm_aspect_ratio", "min": 0.85},
            {"metric": "finger_to_palm_ratio", "max": 0.78},
        ],
        "meaning": (
            "আপনার হাতটি পৃথ্বী তত্ত্বের (Earth Hand)। সমুদ্রিক শাস্ত্র অনুযায়ী আপনি অত্যন্ত বাস্তববাদী, "
            "কর্মঠ ও নির্ভরযোগ্য ব্যক্তিত্ব। আবেগ বা ভাবাবেগের চেয়ে যুক্তি ও বাস্তব পরিস্থিতিকে আপনি বেশি গুরুত্ব দেন। "
            "প্রকৃতির সাথে গভীর সংযোগ এবং ধৈর্য আপনার জীবনের মূল স্তম্ভ। আপনি যেকোনো কঠিন দায়িত্ব সুচারুভাবে "
            "সম্পন্ন করতে পারেন। জীবনের মধ্যভাগে আর্থিক স্থায়িত্ব লাভ সুনিশ্চিত।"
        ),
        "area": "personality",
        "priority": 10,
        "is_default": False,
    },
    {
        "feature": PalmFeature.HAND_TYPE,
        "option": "air_hand",
        "label": "বায়ু হস্ত (Air Hand - Square Palm, Long Fingers)",
        "conditions": [
            {"metric": "palm_aspect_ratio", "min": 0.85},
            {"metric": "finger_to_palm_ratio", "min": 0.78},
        ],
        "meaning": (
            "আপনার হাতটি বায়ু তত্ত্বের (Air Hand)। আপনি একজন গভীর চিন্তাশীল, অনুসন্ধিৎসু ও প্রখর যোগাযোগ ক্ষমতার "
            "অধিকারী মানুষ। নিত্যনতুন আইডিয়া, জ্ঞানার্জন এবং বিশ্লেষণাত্মক কাজে আপনার অসাধারণ পারদর্শিতা রয়েছে। "
            "আপনি যেকোনো সামাজিক পরিবেশে সাবলীলভাবে মানিয়ে নিতে পারেন। শিক্ষকতা, লেখালেখি, প্রযুক্তি বা "
            "গবেষণামূলক ক্ষেত্রে আপনার যশ ও প্রতিষ্ঠা পাওয়ার যোগ প্রবল।"
        ),
        "area": "personality",
        "priority": 10,
        "is_default": False,
    },
    {
        "feature": PalmFeature.HAND_TYPE,
        "option": "fire_hand",
        "label": "অগ্নি হস্ত (Fire Hand - Long Palm, Short Fingers)",
        "conditions": [
            {"metric": "palm_aspect_ratio", "max": 0.85},
            {"metric": "finger_to_palm_ratio", "max": 0.78},
        ],
        "meaning": (
            "আপনার হাতটি অগ্নি তত্ত্বের (Fire Hand)। আপনার মধ্যে রয়েছে এক প্রচণ্ড জীবনীশক্তি, তেজ ও নেতৃত্বদানের সহজাত ক্ষমতা। "
            "আপনি উদ্যমী, স্পষ্টভাষী এবং ঝুঁকি নিতে ভয় পান না। যেকোনো নতুন প্রকল্প দ্রুত শুরু করার অনুপ্রেরণা আপনার ভেতরে সবসময় "
            "কাজ করে। ব্যবসা, প্রশাসন ও নেতৃত্বস্থানে আপনার সাফল্য সুনিশ্চিত। তবে অতিরিক্ত তাড়াহুড়া পরিহার করলে আপনার উন্নতি আরও ত্বরান্বিত হবে।"
        ),
        "area": "personality",
        "priority": 10,
        "is_default": False,
    },
    {
        "feature": PalmFeature.HAND_TYPE,
        "option": "water_hand",
        "label": "জল হস্ত (Water Hand - Long Palm, Long Slender Fingers)",
        "conditions": [
            {"metric": "palm_aspect_ratio", "max": 0.85},
            {"metric": "finger_to_palm_ratio", "min": 0.78},
        ],
        "meaning": (
            "আপনার হাতটি জল তত্ত্বের (Water Hand)। সমুদ্রিক শাস্ত্রে এটিকে সংবেদনশীল ও শিল্পমনা ব্যক্তিত্বের প্রতীক মনে করা হয়। "
            "আপনার মনস্তাত্ত্বিক অনুভূতি ও অন্তর্দৃষ্টি (Intuition) অত্যন্ত প্রখর। আপনি সহজে মানুষের আবেগ অনুভব করতে পারেন। "
            "শিল্প, সাহিত্য, সঙ্গীত, মনস্তত্ত্ব ও আধ্যাত্মিক সাধনায় আপনার গভীর অনুরাগ ও সিদ্ধি লাভের যোগ রয়েছে। শান্ত পরিবেশ আপনার আত্মিক শান্তির জন্য অপরিহার্য।"
        ),
        "area": "personality",
        "priority": 10,
        "is_default": False,
    },
    {
        "feature": PalmFeature.HAND_TYPE,
        "option": "balanced_hand",
        "label": "সুষম পঞ্চভূত হস্ত (Harmonious Elemental Hand)",
        "conditions": [],
        "meaning": (
            "আপনার হাতের গঠন অত্যন্ত সুষম ও সামঞ্জস্যপূর্ণ (Balanced Elemental Hand)। পঞ্চভূতের গুণাবলী আপনার মধ্যে পরিমিতভাবে অবস্থান করছে, "
            "যা আপনাকে যেকোনো পরিস্থিতিতে ভারসাম্য বজায় রেখে বিচক্ষণ সিদ্ধান্ত নিতে সক্ষম করে।"
        ),
        "area": "personality",
        "priority": 0,
        "is_default": True,
    },

    # ------------------------------------------------------------- 2. HEART LINE
    {
        "feature": PalmFeature.HEART_LINE,
        "option": "curved_to_jupiter",
        "label": "বৃহস্পতি পর্বতাভিমুখী হৃদয় রেখা (Curved to Jupiter - Noble Affection)",
        "conditions": [
            {"metric": "heart_line_curvature", "min": 0.35},
            {"metric": "heart_line_length", "min": 0.55},
        ],
        "meaning": (
            "আপনার হৃদয় রেখাটি বৃহস্পতি পর্বতের দিকে সুন্দরভাবে উত্থিত ও বাঁকানো। এটি পরম বিশুদ্ধ ভালোবাসা, বিশ্বস্ততা ও পারিবারিক মূল্যবোধের "
            "এক চমৎকার শুভ লক্ষণ। সম্পর্কে আপনি অত্যন্ত নিষ্ঠাবান ও উদার মনের মানুষ। সঙ্গীর প্রতি আপনার শ্রদ্ধা ও গভীর মমতা থাকে। "
            "দাম্পত্য ও সামাজিক জীবনে আপনি সম্মান ও অকৃত্রিম ভালোবাসা অর্জন করবেন।"
        ),
        "area": "love",
        "priority": 10,
        "is_default": False,
    },
    {
        "feature": PalmFeature.HEART_LINE,
        "option": "straight_across",
        "label": "সুদৃঢ় ও বাস্তববাদী হৃদয় রেখা (Straight & Stable Heart Line)",
        "conditions": [
            {"metric": "heart_line_curvature", "max": 0.35},
            {"metric": "heart_line_depth", "min": 0.50},
        ],
        "meaning": (
            "আপনার হৃদয় রেখাটি সোজা ও সুদৃঢ়। আপনি ভালোবাসার ক্ষেত্রে অত্যন্ত বাস্তববাদী ও স্থিরচিত্ত। আবেগের বন্যায় ভেসে না গিয়ে সম্পর্কের "
            "দায়িত্বগুলো আপনি নিষ্ঠার সাথে পালন করেন। বাহ্যিক আড়ম্বরের চেয়ে আত্মিক সততাকে আপনি বেশি মূল্যায়ন করেন। আপনার এই মানসিক ভারসাম্য "
            "যেকোনো পারিবারিক অস্থিরতায় শান্তির পরিবেশ বজায় রাখতে সাহায্য করে।"
        ),
        "area": "love",
        "priority": 10,
        "is_default": False,
    },
    {
        "feature": PalmFeature.HEART_LINE,
        "option": "long_reaching_edge",
        "label": "গভীর ও দীর্ঘ স্নেহশীল হৃদয় রেখা (Deep & Expansive Heart Line)",
        "conditions": [
            {"metric": "heart_line_length", "min": 0.70},
        ],
        "meaning": (
            "আপনার হৃদয় রেখা অত্যন্ত দীর্ঘ ও সুস্পষ্ট। আপনি তীব্র অনুভূতিপ্রবণ এবং প্রিয়জনদের জন্য সর্বস্ব ত্যাগ করতে প্রস্তুত থাকেন। "
            "আপনার স্নেহশীল হৃদয় চারপাশের মানুষের জন্য এক নিরাপদ আশ্রয়স্থল। তবে আবেগে অন্ধ না হয়ে কিছুটা সতর্ক থাকলে জীবনে মানসিক আঘাতের সম্ভাবনা কমে যাবে।"
        ),
        "area": "love",
        "priority": 8,
        "is_default": False,
    },
    {
        "feature": PalmFeature.HEART_LINE,
        "option": "balanced_heart",
        "label": "স্থিতিশীল হৃদয় রেখা (Balanced Heart Line)",
        "conditions": [],
        "meaning": (
            "আপনার হৃদয় রেখাটি শান্ত ও স্থিতিশীল। এটি আবেগীয় পরিপক্কতা এবং সুষম মানবিক সম্পর্কের ইঙ্গিত দেয়। "
            "আপনি পারস্পরিক সম্মান বজায় রেখে ব্যক্তিগত ও সামাজিক সম্পর্কগুলো সুন্দরভাবে পরিচালনা করেন।"
        ),
        "area": "love",
        "priority": 0,
        "is_default": True,
    },

    # ------------------------------------------------------------- 3. HEAD LINE
    {
        "feature": PalmFeature.HEAD_LINE,
        "option": "long_straight_head",
        "label": "সমুন্নত ও প্রত্যক্ষ বুদ্ধি রেখা (Logical & Analytical Head Line)",
        "conditions": [
            {"metric": "head_line_slope", "max": 0.28},
            {"metric": "head_line_length", "min": 0.55},
        ],
        "meaning": (
            "আপনার মস্তিষ্ক রেখাটি সোজা ও সুদীর্ঘ। সমুদ্রিক শাস্ত্রে এটিকে প্রখর যুক্তি, বিশ্লেষণ ক্ষমতা ও একাগ্রতার প্রতীক বলা হয়। "
            "বিজ্ঞান, গণিত, আইন, ফিন্যান্স বা প্রশাসনিক জটিল নীতি নির্ধারণে আপনার সিদ্ধান্ত গ্রহণে অসাধারণ দক্ষতা রয়েছে। "
            "কোনো আবেগপূর্ণ বিভ্রান্তি আপনার লক্ষ্য থেকে আপনাকে বিচ্যুত করতে পারে না।"
        ),
        "area": "career",
        "priority": 10,
        "is_default": False,
    },
    {
        "feature": PalmFeature.HEAD_LINE,
        "option": "curved_to_moon",
        "label": "চন্দ্রাভিমুখী সৃষ্টিশীল মস্তিষ্ক রেখা (Creative & Intuitive Head Line)",
        "conditions": [
            {"metric": "head_line_slope", "min": 0.28},
            {"metric": "head_line_length", "min": 0.55},
        ],
        "meaning": (
            "আপনার মস্তিষ্ক রেখাটি নিচের দিকে মৃদু বাঁক নিয়ে চন্দ্র পর্বতের দিকে প্রসারিত হয়েছে। এটি অগাধ সৃষ্টিশীলতা, শিল্পচেতনা "
            "ও স্বতঃস্ফূর্ত উদ্ভাবনী প্রতিভার শুভ লক্ষণ। আপনার কল্পনাশক্তি অত্যন্ত সমৃদ্ধ। গল্প, ডিজাইন, আর্কিটেকচার, কনসালটেন্সি "
            "বা নতুন ব্যবসায়িক আইডিয়া তৈরিতে আপনার মন সবসময় সতেজ থাকে। আপনার অন্তর্দৃষ্টিই আপনার সফলতার চাবিকাঠি।"
        ),
        "area": "career",
        "priority": 10,
        "is_default": False,
    },
    {
        "feature": PalmFeature.HEAD_LINE,
        "option": "sharp_focused_head",
        "label": "তীক্ষ্ণ ও সুসংহত বুদ্ধি রেখা (Sharp Focused Intellect)",
        "conditions": [
            {"metric": "head_line_depth", "min": 0.55},
        ],
        "meaning": (
            "আপনার মস্তিষ্ক রেখাটি বেশ সুস্পষ্ট ও গভীর। আপনি যেকোনো সমস্যার মূল কারণ নিমেষেই ধরতে পারেন এবং তাত্ক্ষণিক কার্যকর সমাধান বের করতে পারেন। "
            "আপনার কর্মক্ষমতা ও মানসিক স্থৈর্য সাধারণের চেয়ে অনেক বেশি মজবুত।"
        ),
        "area": "career",
        "priority": 8,
        "is_default": False,
    },
    {
        "feature": PalmFeature.HEAD_LINE,
        "option": "balanced_head",
        "label": "সুচিন্তিত মস্তিষ্ক রেখা (Balanced Mind & Intellect)",
        "conditions": [],
        "meaning": (
            "আপনার মস্তিষ্ক রেখাটি যুক্তি ও কল্পনার মধ্যে এক চমৎকার মেলবন্ধন প্রকাশ করে। "
            "আপনি পরিস্থিতির প্রয়োজন অনুযায়ী কখনও কঠোর বাস্তববাদী আবার কখনও উদার দৃষ্টিভঙ্গি অবলম্বন করতে পারেন।"
        ),
        "area": "career",
        "priority": 0,
        "is_default": True,
    },

    # ------------------------------------------------------------- 4. LIFE LINE
    {
        "feature": PalmFeature.LIFE_LINE,
        "option": "wide_curving_life",
        "label": "প্রশস্ত ও প্রাণবন্ত জীবন রেখা (Expansive Vitality & High Prana)",
        "conditions": [
            {"metric": "life_line_arc", "min": 0.42},
            {"metric": "life_line_length", "min": 0.60},
        ],
        "meaning": (
            "আপনার জীবন রেখাটি শুক্র পর্বতকে বেষ্টন করে এক মনোরম ও প্রশস্ত বৃত্ত তৈরি করেছে। এটি সুস্বাস্থ্য, অফুরন্ত জীবনীশক্তি (Pranic Energy) "
            "এবং দীর্ঘায়ুর এক শ্রেষ্ঠ আশীর্বাদ। আপনার রোগ প্রতিরোধ ক্ষমতা অত্যন্ত ভালো। ভ্রমণের প্রতি আপনার তীব্র আকর্ষণ রয়েছে এবং আপনি জীবনকে পূর্ণ উদ্যমে উপভোগ করতে জানেন।"
        ),
        "area": "health",
        "priority": 10,
        "is_default": False,
    },
    {
        "feature": PalmFeature.LIFE_LINE,
        "option": "close_to_thumb_life",
        "label": "সংযত ও গৃহপ্রিয় জীবন রেখা (Reserved & Disciplined Energy)",
        "conditions": [
            {"metric": "life_line_arc", "max": 0.42},
            {"metric": "life_line_length", "min": 0.50},
        ],
        "meaning": (
            "আপনার জীবন রেখাটি বুড়ো আঙুলের বেশ কাছাকাছি অবস্থান করছে। আপনি শান্ত, গৃহকোণপ্রিয় এবং সংযমী জীবন পছন্দ করেন। অযথা শক্তি অপচয় না করে "
            "আপনি নিজের সম্পদ ও পারিবারিক বন্ধনকে সুরক্ষিত রাখতে ভালোবাসেন। নিয়মমাফিক জীবনযাপন ও সুষম খাদ্যাভ্যাস বজায় রাখলে আপনার শারীরিক তেজ অটুট থাকবে।"
        ),
        "area": "health",
        "priority": 10,
        "is_default": False,
    },
    {
        "feature": PalmFeature.LIFE_LINE,
        "option": "deep_resilient_life",
        "label": "গভীর ও অপরাজেয় জীবনী রেখা (Deep Resilient Life Force)",
        "conditions": [
            {"metric": "life_line_depth", "min": 0.60},
        ],
        "meaning": (
            "আপনার জীবন রেখাটি কোনো বাধা ছাড়াই গভীর ও উজ্জ্বল। প্রাচীন শাস্ত্রে একে 'অজেয় জীবনীশক্তি' বলা হয়েছে। জীবনের যেকোনো ঝড়-ঝাপটা বা "
            "শারীরিক ক্লান্তি থেকে দ্রুত স্বাভাবিক ছন্দে ফিরে আসার এক সহজাত ক্ষমতা আপনার মধ্যে রয়েছে।"
        ),
        "area": "health",
        "priority": 8,
        "is_default": False,
    },
    {
        "feature": PalmFeature.LIFE_LINE,
        "option": "steady_vitality",
        "label": "সুস্থিত জীবন রেখা (Steady Life Stream)",
        "conditions": [],
        "meaning": (
            "আপনার জীবন রেখাটি স্থিতিশীল ও মসৃণ। এটি একটি নিরাপদ, শান্ত ও সামঞ্জস্যপূর্ণ জীবনপ্রবাহের নির্দেশক। "
            "নিয়মিত ধ্যান ও যোগব্যায়াম আপনার এই ইতিবাচক স্বাস্থ্য প্রবাহকে আরও বর্ধিত করবে।"
        ),
        "area": "health",
        "priority": 0,
        "is_default": True,
    },

    # ------------------------------------------------------------- 5. FATE LINE
    {
        "feature": PalmFeature.FATE_LINE,
        "option": "strong_direct_fate",
        "label": "বলিষ্ঠ ঊর্ধ্বগামী ভাগ্য রেখা (Strong Clear Fate Line / শনি রেখা)",
        "conditions": [
            {"metric": "fate_line_prominence", "min": 0.55},
            {"metric": "fate_line_length", "min": 0.40},
        ],
        "meaning": (
            "আপনার হাতে মণিবন্ধ থেকে শনি পর্বত পর্যন্ত এক স্পষ্ট ভাগ্য রেখা প্রস্ফুটিত। সমুদ্রিক শাস্ত্রে এটি 'স্বয়ংসিদ্ধ ভাগ্য' বা নিজের পরিশ্রমে "
            "সাম্রাজ্য গড়ার নির্দেশক। জীবনের লক্ষ্য অল্প বয়স থেকেই আপনার নিকট সুস্পষ্ট এবং ক্রমাগত অধ্যবসায়ের ফলে সমাজে পদমর্যাদা ও অর্থনৈতিক প্রাচুর্য অর্জন করবেন।"
        ),
        "area": "wealth",
        "priority": 10,
        "is_default": False,
    },
    {
        "feature": PalmFeature.FATE_LINE,
        "option": "from_moon_mount",
        "label": "চন্দ্রোত্থিত ভাগ্য রেখা (Destiny Supported by Public & Travel)",
        "conditions": [
            {"metric": "fate_line_from_moon", "min": 0.50},
        ],
        "meaning": (
            "আপনার ভাগ্য রেখাটি চন্দ্রের পর্বত থেকে শুরু হয়ে ঊর্ধ্বে ধাবিত হয়েছে। এর অর্থ আপনার ভাগ্যোন্নতিতে বহির্বিশ্ব, গুণগ্রাহী শুভানুধ্যায়ী ও জনসাধারণের "
            "শুভ প্রভাব গুরুত্বপূর্ণ ভূমিকা রাখবে। ব্যবসা, জনসংযোগ, শিল্পকলা বা আন্তর্জাতিক যোগাযোগে বিপুল খ্যাতি ও আর্থিক সমৃদ্ধির যোগ রয়েছে।"
        ),
        "area": "wealth",
        "priority": 9,
        "is_default": False,
    },
    {
        "feature": PalmFeature.FATE_LINE,
        "option": "gradual_fate_rise",
        "label": "বিকাশমান ভাগ্য রেখা (Gradual Career Growth)",
        "conditions": [
            {"metric": "fate_line_prominence", "min": 0.35},
        ],
        "meaning": (
            "আপনার ভাগ্য রেখাটি জীবনের অভিজ্ঞতা ও পরিপক্কতার সাথে সাথে আরও উজ্জ্বল রূপ নেয়। বয়স বৃদ্ধির সাথে সাথে আপনার অর্থনৈতিক স্বাধীনতা "
            "ও কর্মক্ষেত্রের কর্তৃত্ব বৃদ্ধি পাবে।"
        ),
        "area": "wealth",
        "priority": 5,
        "is_default": False,
    },
    {
        "feature": PalmFeature.FATE_LINE,
        "option": "self_made_destiny",
        "label": "স্বনির্ভর ভাগ্য (Self-Made Destiny)",
        "conditions": [],
        "meaning": (
            "আপনার হস্তরেখায় কোনো কৃত্রিম নির্ভরতা ছাড়াই আত্মশক্তির জয়গান প্রতিফলিত। নির্দিষ্ট কোনো পূর্বনির্ধারিত ছকে না হেঁটে আপনি নিজের মেধা, "
            "সাহস ও স্বাধীন কর্মে নিজের ভাগ্য নিজে গড়ে তোলার পূর্ণ সামর্থ্য রাখেন।"
        ),
        "area": "wealth",
        "priority": 0,
        "is_default": True,
    },

    # ------------------------------------------------------------- 6. SUN LINE
    {
        "feature": PalmFeature.SUN_LINE,
        "option": "prominent_sun_line",
        "label": "উজ্জ্বল রবি রেখা (Radiant Sun Line / যশ ও খ্যাতি যোগ)",
        "conditions": [
            {"metric": "sun_line_prominence", "min": 0.45},
        ],
        "meaning": (
            "আপনার হাতে রবি বা সূর্য রেখাটি অত্যন্ত স্পষ্ট ও শুভপ্রদ। এটি সমাজে সুনাম, যশ ও বিশেষ স্বীকৃতির এক অনন্য প্রতীক। "
            "কর্মক্ষেত্রে আপনার অবদানের প্রশংসা ছড়িয়ে পড়বে এবং আপনি অন্যদের চেয়ে এক স্বতন্ত্র মর্যাদা উপভোগ করবেন। রবির শুভ কৃপায় আপনার তেজ ও খ্যাতি দীর্ঘস্থায়ী হবে।"
        ),
        "area": "career",
        "priority": 10,
        "is_default": False,
    },
    {
        "feature": PalmFeature.SUN_LINE,
        "option": "moderate_sun_line",
        "label": "স্নিগ্ধ রবি প্রভাব (Gentle Solar Grace)",
        "conditions": [],
        "meaning": (
            "আপনার রবি পর্বতে এক স্নিগ্ধ শক্তির আভা রয়েছে। আপনি আত্মপ্রচারের চেয়ে নিঃশব্দে নিজের কাজ করে যেতে বেশি পছন্দ করেন। "
            "সঠিক সময়ে আপনার সততা ও দীর্ঘদিনের সাধনার উপযুক্ত প্রতিদান ও সম্মান আপনি অবশ্যই পাবেন।"
        ),
        "area": "career",
        "priority": 0,
        "is_default": True,
    },

    # ------------------------------------------------------------- 7. MOUNTS
    {
        "feature": PalmFeature.MOUNTS,
        "option": "prominent_jupiter_venus",
        "label": "বৃহস্পতি ও শুক্র পর্বতের ঐশ্বর্য (Majestic Jupiter & Venus Mounts)",
        "conditions": [
            {"metric": "mount_jupiter_prominence", "min": 0.50},
            {"metric": "mount_venus_prominence", "min": 0.50},
        ],
        "meaning": (
            "আপনার হস্ততলে বৃহস্পতির পর্বত (তর্জনীর নিচে) এবং শুক্রের পর্বত (অঙ্গুষ্ঠের মূলে) অত্যন্ত মাংসল ও সমুন্নত। বৃহস্পতি আপনাকে আত্মমর্যাদা, "
            "জ্ঞান ও নেতৃত্বের মহিমা দান করেছে; অন্যদিকে শুক্র আপনাকে সৌন্দর্যবোধ, আকর্ষণীয় ব্যক্তিত্ব ও পার্থিব সুখ-স্বাচ্ছন্দ্যের সৌভাগ্য প্রদান করেছে। আপনার জীবন বৈভব ও সম্মানে ভরপুর থাকবে।"
        ),
        "area": "personality",
        "priority": 10,
        "is_default": False,
    },
    {
        "feature": PalmFeature.MOUNTS,
        "option": "prominent_mercury_moon",
        "label": "বুধ ও চন্দ্র পর্বতের শুভ সংযোগ (Intuitive Mercury & Luna Mounts)",
        "conditions": [
            {"metric": "mount_mercury_prominence", "min": 0.48},
            {"metric": "mount_moon_prominence", "min": 0.48},
        ],
        "meaning": (
            "আপনার হাতে বুধ এবং চন্দ্রের পর্বত যুগল অত্যন্ত শক্তিশালী। বুধের কৃপায় আপনি বাকপটু, তীক্ষ্ণ বুদ্ধিসম্পন্ন এবং ব্যবসায় বিচক্ষণ। "
            "চন্দ্রের প্রভাবে আপনার চিন্তাধারা উদার ও কল্পনাপ্রবণ। যোগাযোগ, বাণিজ্য, আন্তর্জাতিক সংযোগ বা সৃষ্টিশীল উদ্যোগে আপনার ঈর্ষণীয় সাফল্য অর্জিত হবে।"
        ),
        "area": "personality",
        "priority": 9,
        "is_default": False,
    },
    {
        "feature": PalmFeature.MOUNTS,
        "option": "harmonious_mounts",
        "label": "সুষম গ্রহ পর্বত বিন্যাস (Harmonious Planetary Mounts)",
        "conditions": [],
        "meaning": (
            "আপনার হাতের সমস্ত গ্রহ পর্বতগুলি সুন্দর সমতায় বিরাজমান। কোনো একটি গ্রহের অতি-প্রভাব বা খর্বতা নেই, যা আপনাকে জীবনের সমস্ত পরিস্থিতিতে "
            "শান্ত, ধৈর্যশীল ও ইতিবাচক ভারসাম্য বজায় রাখতে সাহায্য করে।"
        ),
        "area": "personality",
        "priority": 0,
        "is_default": True,
    },

    # ------------------------------------------------------------- 8. FINGERS
    {
        "feature": PalmFeature.FINGERS,
        "option": "ring_longer_than_index",
        "label": "অনামিকার প্রাধান্য (Longer Ring Finger / 2D:4D Charisma)",
        "conditions": [
            {"metric": "ratio_2d_4d", "max": 0.98},
        ],
        "meaning": (
            "আপনার অনামিকা বা রবির আঙুল তর্জনীর চেয়ে দীর্ঘ। বৈদিক ও আধুনিক বায়োমেট্রিক উভয় শাস্ত্রেই এটিকে সহজাত ক্যারিশমা, ঝুঁকি নেওয়ার ক্ষমতা "
            "এবং চৌকস ব্যক্তিত্বের পরিচায়ক মনে করা হয়। আপনি যেকোনো চ্যালেঞ্জে দ্রুত পদক্ষেপ নেন এবং প্রতিকূল পরিস্থিতিকে সফলতার সোপানে রূপান্তর করতে পারেন।"
        ),
        "area": "personality",
        "priority": 10,
        "is_default": False,
    },
    {
        "feature": PalmFeature.FINGERS,
        "option": "index_longer_than_ring",
        "label": "তর্জনীর নেতৃত্ব প্রভাব (Longer Index Finger / Strategic Leadership)",
        "conditions": [
            {"metric": "ratio_2d_4d", "min": 1.02},
        ],
        "meaning": (
            "আপনার তর্জনী বা বৃহস্পতির আঙুল অনামিকার চেয়ে অপেক্ষাকৃত দীর্ঘ। এটি জন্মগত নেতৃত্বগুণ, উচ্চাকাঙ্ক্ষা ও পথপ্রদর্শকের প্রতীক। "
            "আপনি দায়িত্ব নিতে ভালোবাসেন এবং দল বা সংস্থাকে পরম আত্মবিশ্বাসের সাথে লক্ষ্যের দিকে এগিয়ে নিয়ে যেতে পারেন।"
        ),
        "area": "personality",
        "priority": 10,
        "is_default": False,
    },
    {
        "feature": PalmFeature.FINGERS,
        "option": "long_expressive_pinky",
        "label": "বাণীসিদ্ধ কনিষ্ঠা অঙ্গুলি (Eloquence & Business Acumen)",
        "conditions": [
            {"metric": "pinky_reach", "min": 0.98},
        ],
        "meaning": (
            "আপনার কনিষ্ঠা বা বুধের আঙুলটি অনামিকার প্রথম পর্ব পর্যন্ত অনায়াসে পৌঁছেছে। প্রাচীন শাস্ত্রে এটিকে 'বাণীসিদ্ধি ও অর্থযোগ' বলা হয়েছে। "
            "আপনার কথা বলার ভঙ্গি মানুষকে গভীরভাবে আকৃষ্ট করে এবং আর্থিক হিসাব-নিকাশে আপনি অত্যন্ত সতর্ক ও দূরদর্শী।"
        ),
        "area": "wealth",
        "priority": 9,
        "is_default": False,
    },
    {
        "feature": PalmFeature.FINGERS,
        "option": "balanced_fingers",
        "label": "সুষম অঙ্গুলি অনুপাত (Equally Balanced Fingers)",
        "conditions": [],
        "meaning": (
            "আপনার আঙুল ও পর্বের বিন্যাস অত্যন্ত সুষম। এটি ধৈর্য, আত্মনিয়ন্ত্রণ এবং জীবনের প্রতিটি ক্ষেত্রে ভারসাম্যপূর্ণ ও সুবিবেচক আচরণের শুভ নিদর্শন।"
        ),
        "area": "personality",
        "priority": 0,
        "is_default": True,
    },
]
