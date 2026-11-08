"""1-Year Resolution High-Precision Age Timeline (Ayur Nirnay & Event Chronology).

Maps the classical 7-year Cheiro cycle and Vedic Samudrika Shastra proportional divisions
along the Life Line (0-84+), Head Line (0-70), Fate Line (18-65+), and Heart Line (0-75).

Provides year-by-year predictive intelligence with normalized landmark coordinates for
interactive UI highlighting.
"""

from __future__ import annotations

from typing import Any


def get_palm_timeline_for_age(
    age: int,
    gender: str = "male",
    measurements: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Return high-resolution 1-year timeline forecast and spatial palm coordinate."""
    clamped_age = max(1, min(95, int(age)))

    # Determine epoch, governing mount, active line, and normalized spatial coordinates
    if clamped_age <= 14:
        epoch_key = "CHILDHOOD_ROOTS"
        epoch_name_en = "Formative Childhood & Parental Grace"
        epoch_name_bn = "বাল্যকাল ও পিতৃ-মাতৃ স্নেহবলয়"
        epoch_name_hi = "बाल्यकाल व माता-पिता का संरक्षण"
        governing_mount = "Rahu & Ketu Axis"
        active_line = "Life Line (Earth Line Origin)"
        norm_x, norm_y = 0.22, 0.38
        focus_en = "Physical vitality, early schooling, family security"
        focus_bn = "শারীরিক সুস্থতা, প্রাথমিক শিক্ষা ও পারিবারিক নিরাপত্তা"
        focus_hi = "शारीरिक स्वास्थ्य, प्रारंभिक शिक्षा व पारिवारिक सुरक्षा"
        prediction_en = (
            f"At age {clamped_age}, your life line reflects foundational nurturing and ancestral protection. "
            "Natural curiosity flourishes, laying the emotional bedrock for future academic resilience."
        )
        prediction_bn = (
            f"{clamped_age} বছর বয়সে আপনার জীবনরেখার শীর্ষবিন্দু নির্দেশ করে স্নেহপূর্ণ পারিবারিক সুরক্ষা ও শারীরিক তেজ। "
            "এই সময়ে অর্জিত মূল্যবোধ আপনার ভবিষ্যৎ চরিত্র ও মেধার মজবুত ভিত্তি স্থাপন করছে।"
        )
        prediction_hi = (
            f"आयु {clamped_age} वर्ष में आपकी जीवन रेखा मातृ-पितृ संरक्षण एवं मानसिक चेतना के विकास को दर्शाती है। "
            "इस समय की गई शिक्षा भविष्य की सफलता का आधार बनेगी।"
        )
    elif clamped_age <= 21:
        epoch_key = "ACADEMIC_FOUNDATION"
        epoch_name_en = "Intellectual Awakening & Higher Education"
        epoch_name_bn = "মেধার স্ফুরণ ও উচ্চশিক্ষা সন্ধান"
        epoch_name_hi = "बुद्धि का जागरण व उच्च शिक्षा"
        governing_mount = "Jupiter (Guru Parvat)"
        active_line = "Head Line (Air Line Ascent)"
        norm_x, norm_y = 0.32, 0.42
        focus_en = "Academic excellence, vocational choice, identity formation"
        focus_bn = "একাডেমিক সাফল্য, পেশা নির্বাচন ও আত্মপরিচয় গঠন"
        focus_hi = "शैक्षणिक सफलता, करियर चयन व आत्म-पहचान"
        prediction_en = (
            f"At age {clamped_age}, the separation of your Head and Life lines marks rising intellectual autonomy. "
            "A prime window for mastering advanced technical or creative disciplines and establishing career direction."
        )
        prediction_bn = (
            f"{clamped_age} বছর বয়সে জীবনরেখা ও শিরোরেখার স্বাধীন গতি আপনার বুদ্ধিবৃত্তিক স্বাতন্ত্র্যের সূচনা করে। "
            "উচ্চশিক্ষা, নতুন দক্ষতা অর্জন এবং ভবিষ্যৎ কর্মজীবনের গতিপথ নির্ধারণের এটি একটি স্বর্ণালী সময়।"
        )
        prediction_hi = (
            f"आयु {clamped_age} वर्ष में मस्तिष्क रेखा का विकास स्वतंत्र विचार और निर्णय क्षमता का संकेत देता है। "
            "उच्च शिक्षा एवं करियर का सही मार्ग चुनने का यह उत्तम समय है।"
        )
    elif clamped_age <= 28:
        epoch_key = "CAREER_LAUNCH"
        epoch_name_en = "Early Enterprise & Financial Independence"
        epoch_name_bn = "প্রথম কর্ম প্রতিষ্ঠা ও আত্মনির্ভরতা"
        epoch_name_hi = "प्रथम आजीविका व आत्मनिर्भरता"
        governing_mount = "Mercury & Sun Axis"
        active_line = "Fate Line (Fire Line Ascent)"
        norm_x, norm_y = 0.48, 0.65
        focus_en = "Professional onboarding, self-reliance, relationship formation"
        focus_bn = "পেশাগত সাফল্য, আত্মনির্ভরশীলতা ও সম্পর্কের দৃঢ়তা"
        focus_hi = "व्यावसायिक उन्नति, स्वावलंबन व संबंध"
        prediction_en = (
            f"At age {clamped_age}, your upward Fate line accelerates toward the central palm. Independent "
            "undertakings yield visible recognition, building lasting financial confidence."
        )
        prediction_bn = (
            f"{clamped_age} বছর বয়সে ভাগ্যরেখার ঊর্ধ্বমুখী যাত্রা স্বাধীন উপার্জনের সুযোগ বৃদ্ধি করে। আপনার কাজের স্বীকৃতি "
            "মিলবে এবং আত্মবিশ্বাস উত্তরোত্তর বৃদ্ধি পাবে।"
        )
        prediction_hi = (
            f"आयु {clamped_age} वर्ष में भाग्य रेखा का उभार स्वतंत्र कार्य और आर्थिक उन्नति का स्पष्ट संकेत देता है। "
            "परिश्रम का उचित फल और सामाजिक प्रतिष्ठा प्राप्त होगी।"
        )
    elif clamped_age <= 35:
        epoch_key = "THE_GOLDEN_CONVERGENCE"
        epoch_name_en = "The Golden Crossroads (Head-Fate Intersection)"
        epoch_name_bn = "সুবর্ণ সন্ধিক্ষণ: মেধা ও ভাগ্যের মহামিলন (৩৫ বর্ষ)"
        epoch_name_hi = "स्वर्णिम संधि: मस्तिष्क व भाग्य का मिलन"
        governing_mount = "Mount of Saturn (Shani Parvat)"
        active_line = "Fate Line meets Head Line"
        norm_x, norm_y = 0.52, 0.48
        focus_en = "Major partnership/marriage, executive decisions, property foundation"
        focus_bn = "বিবাহ বা স্থায়ী বন্ধন, নির্বাহী সিদ্ধান্ত ও স্থায়ী সম্পত্তি যোগ"
        focus_hi = "विवाह या स्थायी संबंध, बड़े निर्णय व संपत्ति लाभ"
        prediction_en = (
            f"At age {clamped_age}, the sacred junction of the Head and Fate lines signifies pivotal destiny calibration. "
            "Your intellectual choices directly command commercial and domestic flourishing."
        )
        prediction_bn = (
            f"{clamped_age} বছর বয়সে শিরোরেখা ও ভাগ্যরেখার মহামিলন আপনার জীবনের অন্যতম প্রধান মোড় ঘোরানোর সময়। "
            "গুরুত্বপূর্ণ পারিবারিক ও আর্থিক সিদ্ধান্ত আপনার পরবর্তী দুই দশকের প্রাচুর্যের ভিত গড়ে তুলবে।"
        )
        prediction_hi = (
            f"आयु {clamped_age} वर्ष में मस्तिष्क और भाग्य रेखा का संगम जीवन की सबसे महत्वपूर्ण दिशा तय करता है। "
            "कार्यक्षेत्र में उच्च पद और पारिवारिक जीवन में स्थिरता प्राप्त होगी।"
        )
    elif clamped_age <= 45:
        epoch_key = "PEAK_AUTHORITY"
        epoch_name_en = "Peak Authority, Renown & Wealth Acceleration"
        epoch_name_bn = "শীর্ষ কর্তৃত্ব, ধনবৃদ্ধি ও সামাজিক প্রতিপত্তি"
        epoch_name_hi = "शीर्ष नेतृत्व, यश व धन संचय"
        governing_mount = "Mount of Sun (Surya Parvat)"
        active_line = "Sun Line (Surya Rekha) & Upper Fate Line"
        norm_x, norm_y = 0.65, 0.35
        focus_en = "Executive authority, wealth accumulation, societal prestige"
        focus_bn = "শীর্ষ পদমর্যাদা, সম্পদ বৃদ্ধি ও জনসম্মান"
        focus_hi = "उच्च पद, धन लाभ व सामाजिक मान-सम्मान"
        prediction_en = (
            f"At age {clamped_age}, the emergence of the Sun line brings solar radiance to your public reputation. "
            "Leadership authority solidifies, accompanied by high financial stability."
        )
        prediction_bn = (
            f"{clamped_age} বছর বয়সে সূর্যরেখার প্রভাব আপনার প্রতিষ্ঠা ও সামাজিক যশকে শীর্ষে নিয়ে যাবে। "
            "আর্থিক সচ্ছলতা ও নেতৃত্ব দেওয়ার ক্ষমতা বহুগুণ বৃদ্ধি পাবে।"
        )
        prediction_hi = (
            f"आयु {clamped_age} वर्ष में सूर्य रेखा का प्रभाव आपके मान-सम्मान को नई ऊंचाइयों पर ले जाता है। "
            "आर्थिक मजबूती और नेतृत्व क्षमता का पूर्ण विकास होगा।"
        )
    elif clamped_age <= 55:
        epoch_key = "HARVEST_AND_STABILITY"
        epoch_name_en = "Harvest of Lifelong Enterprise (Heart-Fate Apex)"
        epoch_name_bn = "পরিপক্ক ফল ও আধ্যাত্মিক সন্তুষ্টি (৫০-৫৫ বর্ষ)"
        epoch_name_hi = "परिपक्वता व कर्मफल संचय"
        governing_mount = "Mount of Jupiter & Venus"
        active_line = "Heart Line meets Upper Palm"
        norm_x, norm_y = 0.55, 0.25
        focus_en = "Family legacy, mentorship, philanthropic fulfillment"
        focus_bn = "পারিবারিক কল্যাণ, উত্তরসূরিদের দিকনির্দেশনা ও পরোপকার"
        focus_hi = "पारिवारिक सुख, मार्गदर्शन व परोपकार"
        prediction_en = (
            f"At age {clamped_age}, the harmony between Heart and Saturn lines reflects graceful fulfillment. "
            "Material security supports generous mentorship and deep philosophical peace."
        )
        prediction_bn = (
            f"{clamped_age} বছর বয়সে হৃদয়রেখা ও শনি পর্বতের সান্নিধ্য মনের গভীর শান্তি ও পরিতৃপ্তি এনে দেয়। "
            "জীবনের বড় দায়িত্বগুলো সম্পন্ন করে আপনি সমাজের জন্য অনুকরণীয় পথপ্রদর্শক হিসেবে প্রতিষ্ঠিত হবেন।"
        )
        prediction_hi = (
            f"आयु {clamped_age} वर्ष में हृदय रेखा व शनि पर्वत का सामंजस्य मानसिक शांति और संतोष प्रदान करता है। "
            "पारिवारिक जिम्मेदारियां पूरी होकर समाज में आदरणीय स्थान मिलेगा।"
        )
    else:
        epoch_key = "VEDIC_LONGEVITY_MOKSHA"
        epoch_name_en = "Vedic Longevity, Serenity & Moksha (Wisdom Horizon)"
        epoch_name_bn = "দীর্ঘায়ু, আত্মদর্শন ও পরম শান্তি (মোক্ষ যোগ)"
        epoch_name_hi = "दीर्घायु, आत्म-साक्षात्कार व मोक्ष योग"
        governing_mount = "Manibandha & Mount of Ketu"
        active_line = "Life Line descent into Wrist Bracelets"
        norm_x, norm_y = 0.35, 0.88
        focus_en = "Spiritual liberation, vital resilience, ancestral wisdom"
        focus_bn = "আধ্যাত্মিক মোক্ষ, সুস্থ দীর্ঘায়ু ও প্রজ্ঞার আলো"
        focus_hi = "आध्यात्मिक शांति, उत्तम स्वास्थ्य व दीर्घायु"
        prediction_en = (
            f"At age {clamped_age}, the continuous curve into the wrist bracelets marks venerable longevity and "
            "spiritual freedom (Moksha). Revered family elder status with clear mind and peaceful contentment."
        )
        prediction_bn = (
            f"{clamped_age} বছর বয়সে মণিবন্ধ পর্যন্ত জীবনরেখার সুবিন্যস্ত বিস্তার দীর্ঘায়ু ও শারীরিক সহনশীলতা প্রকাশ করে। "
            "পরিবারে শ্রদ্ধেয় মুরব্বি হিসেবে আধ্যাত্মিক আনন্দ ও পরম শান্তিতে দিন অতিবাহিত হবে।"
        )
        prediction_hi = (
            f"आयु {clamped_age} वर्ष में मणिबंध तक जीवन रेखा का प्रवाह उत्तम दीर्घायु और शांति का प्रमाण है। "
            "परिवार और समाज में सम्मानित स्थान तथा आध्यात्मिक शांति प्राप्त होगी।"
        )

    return {
        "age": clamped_age,
        "epoch_key": epoch_key,
        "epoch_name_en": epoch_name_en,
        "epoch_name_bn": epoch_name_bn,
        "epoch_name_hi": epoch_name_hi,
        "governing_mount": governing_mount,
        "active_line": active_line,
        "focus_en": focus_en,
        "focus_bn": focus_bn,
        "focus_hi": focus_hi,
        "prediction_en": prediction_en,
        "prediction_bn": prediction_bn,
        "prediction_hi": prediction_hi,
        "norm_coord": [norm_x, norm_y],
        "vitality_index": int(max(70, min(99, 100 - clamped_age * 0.28))),
    }

