"""Seed authentic sacred courses matching DivinLink Gurukul categories.

Categories:
- vedic_astrology
- numerology
- tarot
- vastu
- palmistry
- kp_astrology
- lal_kitab

Run:
    uv run python -m scripts.seed_courses
"""

import asyncio
from datetime import datetime, timezone
from app.db.mongodb import close_mongo_connection, connect_to_mongo
from app.models.course import Course, CourseSection, CourseLesson


COURSES_DATA = [
    {
        "title": "সম্পূর্ণ বৈদিক জ্যোতিষ ও কুণ্ডলী বিচার মাস্টারক্লাস",
        "slug": "complete-vedic-astrology-masterclass",
        "subtitle": "লগ্ন, ১২টি ভাব, গ্রহের কারকত্ব এবং দশা-অন্তর্দশার নিখুঁত বিচার পদ্ধতি",
        "description": "মহর্ষি পরাশর প্রণীত প্রাচীন বৈদিক জ্যোতিষের সম্পূর্ণ পাঠক্রম। লগ্ন কুষ্ঠি নির্ণয় থেকে শুরু করে গ্রহের বল, শনি সাড়েসাতি, মাঙ্গলিক বিচার ও নিখুঁত ভবিষ্যৎ গণনা শিখুন সরাসরি অভিজ্ঞ জ্যোতিষাচার্যের তত্ত্বাবধানে।",
        "category": "vedic_astrology",
        "level": "all_levels",
        "language": "bn",
        "instructor_name": "পণ্ডিত আচার্য রাহুল শর্মা",
        "instructor_title": "প্রধান বৈদিক জ্যোতিষাচার্য ও স্বর্ণপদকপ্রাপ্ত গবেষক",
        "instructor_avatar": "https://images.unsplash.com/photo-1544717305-2782549b5136?q=80&w=300&auto=format&fit=crop",
        "instructor_bio": "২৫+ বছরের জ্যোতিষ শাস্ত্রের অভিজ্ঞতা ও কাশী হিন্দু বিশ্ববিদ্যালয়ের বিশিষ্ট প্রাক্তনী।",
        "thumbnail_url": "https://images.unsplash.com/photo-1532012197267-da84d127e765?q=80&w=800&auto=format&fit=crop",
        "price": 999.0,
        "mrp": 2999.0,
        "discount_percent": 67,
        "currency": "INR",
        "duration_hours": 12.5,
        "total_lessons": 18,
        "total_students": 248,
        "average_rating": 4.9,
        "rating_count": 89,
        "what_you_will_learn": [
            "১২টি রাশি ও ২৭টি নক্ষত্রের গভীর চারিত্রিক বিশ্লেষণ",
            "লগ্ন কুষ্ঠির ১২টি ভাবের কারকত্ব ও শুভাশুভ ফল বিচার",
            "বিংশোত্তরী মহাদশা ও অন্তর্দশার সময় নির্ণয়",
            "মাঙ্গলিক ও কালসর্প দোষের শাস্ত্রীয় প্রতিকার",
        ],
        "prerequisites": ["জ্যোতিষ শেখার আন্তরিক নিষ্ঠা ও প্রাথমিক আগ্রহ"],
        "tags": ["vedic_astrology", "kundli", "parashar", "astrology", "horoscope"],
        "is_published": True,
        "is_featured": True,
        "certificate_enabled": True,
        "sections": [
            {
                "title": "অধ্যায় ১: বৈদিক জ্যোতিষের ভিত্তি ও লগ্ন বিচার",
                "order": 1,
                "lessons": [
                    {"title": "জ্যোতিষ শাস্ত্রের পরিচিতি ও উৎপত্তি", "duration_minutes": 35, "is_free_preview": True},
                    {"title": "১২টি রাশি ও তাদের অধিপতি গ্রহ", "duration_minutes": 45, "is_free_preview": True},
                    {"title": "লগ্ন নির্ণয় ও ১২টি ভাবের কারকত্ব", "duration_minutes": 55, "is_free_preview": False},
                ],
            },
            {
                "title": "অধ্যায় ২: গ্রহের বল ও দশা গণনা",
                "order": 2,
                "lessons": [
                    {"title": "উচ্চ, নীচ ও স্বক্ষেত্র গ্রহের ফল", "duration_minutes": 50, "is_free_preview": False},
                    {"title": "বিংশোত্তরী মহাদশা ও গোচর বিচার", "duration_minutes": 60, "is_free_preview": False},
                ],
            },
        ],
    },
    {
        "title": "রাইডার ওয়েট ট্যারো রিডিং ও ভবিষ্যৎ সংকেত পাঠ",
        "slug": "rider-waite-tarot-reading-mastery",
        "subtitle": "৭৮টি কার্ডের আধ্যাত্মিক অর্থ, স্প্রেড পদ্ধতি ও সাইকিক রিডিং কলা",
        "description": "ট্যারো কার্ডের মাধ্যমে অভ্যন্তরীণ অবচেতন মন ও ভবিষ্যৎ শক্তির সংকেত জানুন। মেজর ও মাইনর আর্কানার প্রতিটি কার্ডের প্রতীকী অর্থ, ৩-কার্ড স্প্রেড, কেল্টিক ক্রস এবং ক্যারিয়ার ও সম্পর্কের সঠিক পরামর্শ দেওয়ার দক্ষতা অর্জন করুন।",
        "category": "tarot",
        "level": "beginner",
        "language": "bn",
        "instructor_name": "অদিত্যা রায় (ট্যারো বিশারদ)",
        "instructor_title": "আন্তর্জাতিক সার্টিফায়েড ট্যারো রিডার ও সাইকিক কোচ",
        "instructor_avatar": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?q=80&w=300&auto=format&fit=crop",
        "instructor_bio": "১২+ বছর ধরে হাজার হাজার মানুষকে ট্যারোর মাধ্যমে সঠিক দিশা প্রদর্শন করেছেন।",
        "thumbnail_url": "https://images.unsplash.com/photo-1633493752763-71a25a9adfc5?q=80&w=800&auto=format&fit=crop",
        "price": 1299.0,
        "mrp": 3499.0,
        "discount_percent": 63,
        "currency": "INR",
        "duration_hours": 9.0,
        "total_lessons": 14,
        "total_students": 182,
        "average_rating": 4.8,
        "rating_count": 64,
        "what_you_will_learn": [
            "২২টি মেজর আর্কানা কার্ডের গভীর অর্থ ও মনস্তাত্ত্বিক ব্যাখ্যা",
            "৫৬টি মাইনর আর্কানা (ওয়ান্ডস, কাপ্স, সোর্ডস, পেন্টাকলস) এর বিশ্লেষণ",
            "দৈনিক রিডিং, প্রেম ও আর্থিক সিদ্ধান্তের জন্য জনপ্রিয় স্প্রেডস",
            "রিভার্সাল কার্ডের নিখুঁত অর্থ ও এনার্জি ক্লিনজিং",
        ],
        "prerequisites": ["রাইডার-ওয়েট ট্যারো ডেক (ঐচ্ছিক)"],
        "tags": ["tarot", "cards", "rider_waite", "divination", "psychic"],
        "is_published": True,
        "is_featured": True,
        "certificate_enabled": True,
        "sections": [
            {
                "title": "অধ্যায় ১: ট্যারো কার্ডের পরিচিতি ও প্রস্তুতি",
                "order": 1,
                "lessons": [
                    {"title": "ট্যারোর ইতিহাস ও এনার্জি সংযোগ", "duration_minutes": 30, "is_free_preview": True},
                    {"title": "মেজর আর্কানা ১-১১ এর আধ্যাত্মিক পথ", "duration_minutes": 50, "is_free_preview": True},
                ],
            },
        ],
    },
    {
        "title": "কালডিয়ান ও পাইথাগোরিয়ান সংখ্যাতত্ত্ব (Numerology)",
        "slug": "chaldean-pythagorean-numerology-secrets",
        "subtitle": "মূলাঙ্ক, ভাগ্যাঙ্ক, নামের বানান সংশোধন ও লকি নম্বর নির্বাচন",
        "description": "সংখ্যার গোপন শক্তির সাহায্যে জীবনের সৌভাগ্য আকর্ষণ করুন। আপনার জন্মতারিখ বিশ্লেষণ করে মূলাঙ্ক ও ভাগ্যাঙ্ক নির্ণয়, নামের বানানের কম্পন পরিবর্তন এবং ব্যবসা ও ক্যারিয়ারের উপযুক্ত সময় নির্বাচন শিখুন।",
        "category": "numerology",
        "level": "intermediate",
        "language": "bn",
        "instructor_name": "ড. দেবব্রত মুখোপাধ্যায়",
        "instructor_title": "সংখ্যাতত্ত্ববিদ ও বাস্তু পরামর্শদাতা",
        "instructor_avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?q=80&w=300&auto=format&fit=crop",
        "instructor_bio": "১৮ বছরের অভিজ্ঞতা সম্পন্ন আন্তর্জাতিক খ্যাতিসম্পন্ন সংখ্যাতত্ত্ববিদ।",
        "thumbnail_url": "https://images.unsplash.com/photo-1509228468518-180dd4864904?q=80&w=800&auto=format&fit=crop",
        "price": 799.0,
        "mrp": 2499.0,
        "discount_percent": 68,
        "currency": "INR",
        "duration_hours": 8.0,
        "total_lessons": 12,
        "total_students": 195,
        "average_rating": 4.9,
        "rating_count": 72,
        "what_you_will_learn": [
            "১ থেকে ৯ সংখ্যার গ্রহগত প্রভাব ও স্বভাব বিশ্লেষণ",
            "কালডিয়ান চার্ট অনুযায়ী শুভ নামের বানান তৈরি",
            "মোবাইল নম্বর, বাড়ি ও গাড়ি নম্বর বিশ্লেষণ",
            "ব্যক্তিগত বর্ষ (Personal Year) অনুযায়ী সঠিক সিদ্ধান্ত গ্রহণ",
        ],
        "prerequisites": ["সাধারণ গাণিতিক যোগ বিয়োগের জ্ঞান"],
        "tags": ["numerology", "numbers", "chaldean", "lucky_number"],
        "is_published": True,
        "is_featured": False,
        "certificate_enabled": True,
        "sections": [
            {
                "title": "অধ্যায় ১: মূল সংখ্যা ও গ্রহ সংযোগ",
                "order": 1,
                "lessons": [
                    {"title": "১-৯ সংখ্যার বৈশিষ্ট্য ও প্রভাব", "duration_minutes": 40, "is_free_preview": True},
                    {"title": "মূলাঙ্ক ও ভাগ্যাঙ্কের গণনা পদ্ধতি", "duration_minutes": 45, "is_free_preview": False},
                ],
            },
        ],
    },
    {
        "title": "মহাবাস্তু ও বৈদিক দিকশোধন বিজ্ঞান",
        "slug": "mahavastu-and-vedic-space-energy-science",
        "subtitle": "ভাঙচুর ছাড়াই ১৬টি জোনের ভারসাম্য রক্ষা ও ধন-সমৃদ্ধি বৃদ্ধি",
        "description": "আপনার বাসস্থান ও কর্মক্ষেত্রের শক্তি সঞ্চালন উন্নত করে সমৃদ্ধি ও মানসিক শান্তি আনুন। বাস্তুপুরুষ মন্ডল, ১৬টি দিক, পঞ্চতত্ত্বের ভারসাম্য এবং বিনা ভাঙচুরে রঙ, ধাতু ও পিরামিড প্রতিকারের বৈজ্ঞানিক প্রয়োগ শিখুন।",
        "category": "vastu",
        "level": "all_levels",
        "language": "bn",
        "instructor_name": "বাস্তুাচার্য সমীরণ রায়",
        "instructor_title": "সার্টিফায়েড মহাবাস্তু এক্সপার্ট ও ইনটেরিয়র কনসালট্যান্ট",
        "instructor_avatar": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?q=80&w=300&auto=format&fit=crop",
        "instructor_bio": "বাণিজ্যিক ও আবাসিক বাস্তুর ১০০+ সফল প্রকল্পের রূপকার।",
        "thumbnail_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?q=80&w=800&auto=format&fit=crop",
        "price": 1499.0,
        "mrp": 3999.0,
        "discount_percent": 63,
        "currency": "INR",
        "duration_hours": 10.0,
        "total_lessons": 15,
        "total_students": 164,
        "average_rating": 4.9,
        "rating_count": 51,
        "what_you_will_learn": [
            "১৬টি মহাবাস্তু দিক ও বাস্তুপুরুষ মণ্ডলের রহস্য",
            "প্রধান ফটক, রান্নাঘর ও শোবার ঘরের সঠিক অবস্থান",
            "টয়লেট ও জলের ট্যাঙ্কের বাস্তু দোষ কাটানোর উপায়",
            "বিনা ভাঙচুরে রঙ, স্ট্রিপ ও স্ফটিক দ্বারা প্রতিকার",
        ],
        "prerequisites": ["বাস্তু সম্পর্কে প্রাথমিক আগ্রহ ও ড্রয়িং ম্যাপ বোঝার ইচ্ছা"],
        "tags": ["vastu", "mahavastu", "home_energy", "architecture"],
        "is_published": True,
        "is_featured": True,
        "certificate_enabled": True,
        "sections": [
            {
                "title": "অধ্যায় ১: বাস্তুর পঞ্চতত্ত্বের মূল নীতি",
                "order": 1,
                "lessons": [
                    {"title": "জল, বায়ু, অগ্নি, পৃথিবী ও আকাশ তত্ত্ব", "duration_minutes": 45, "is_free_preview": True},
                    {"title": "কম্পাস ও শক্তি জোনের সঠিক পরিমাপ", "duration_minutes": 50, "is_free_preview": False},
                ],
            },
        ],
    },
    {
        "title": "সামুদ্রিক শাস্ত্র ও হস্তরেখা বিচার বিজ্ঞান (Palmistry)",
        "slug": "samudrika-shastra-hand-reading-secrets",
        "subtitle": "হাতের রেখা, পর্বত, চিহ্ন এবং আয়ু-ক্যারিয়ার-বিবাহের নিখুঁত সংকেত",
        "description": "হাতের তালুর রেখা ও পর্বতের সাহায্যে মানুষের চরিত্র, স্বাস্থ্য, আর্থিক উন্নতি ও জীবনের মোড় বিশ্লেষণ করুন। হৃদয় রেখা, মস্তিষ্ক রেখা, ভাগ্য রেখা ও হাতের পর্বতের শুভাশুভ চিহ্নের বিস্তারিত বিশ্লেষণ শিখুন।",
        "category": "palmistry",
        "level": "beginner",
        "language": "bn",
        "instructor_name": "পণ্ডিত নারায়ণ চক্রবর্তী",
        "instructor_title": "সামুদ্রিক শাস্ত্রবিদ ও হস্তরেখা বিশেষজ্ঞ",
        "instructor_avatar": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?q=80&w=300&auto=format&fit=crop",
        "instructor_bio": "৩০ বছরের অভিজ্ঞতাসম্পন্ন প্রখ্যাত হস্তরেখা বিশারদ।",
        "thumbnail_url": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=800&auto=format&fit=crop",
        "price": 899.0,
        "mrp": 2799.0,
        "discount_percent": 68,
        "currency": "INR",
        "duration_hours": 7.5,
        "total_lessons": 11,
        "total_students": 142,
        "average_rating": 4.8,
        "rating_count": 48,
        "what_you_will_learn": [
            "প্রধান রেখাসমূহ: আয়ুরেখা, শিররেখা, হৃদয়রেখা ও ভাগ্যরেখা",
            "৭টি পর্বতের (বৃহস্পতি, শনি, রবি ইত্যাদি) শুভাশুভ প্রভাব",
            "বিবাহ রেখা ও সন্তানের সংকেত বিচার",
            "হাতে পদ্ম, ত্রিশূল, মাছের চিহ্নের অর্থ ও প্রভাব",
        ],
        "prerequisites": ["হস্তরেখা বিচার শেখার আগ্রহ"],
        "tags": ["palmistry", "hand_reading", "samudrika", "destiny"],
        "is_published": True,
        "is_featured": False,
        "certificate_enabled": True,
        "sections": [
            {
                "title": "অধ্যায় ১: হাতের গঠন ও প্রধান রেখাসমূহ",
                "order": 1,
                "lessons": [
                    {"title": "হাতের প্রকারভেদ ও ত্বকের গঠন", "duration_minutes": 35, "is_free_preview": True},
                    {"title": "আয়ুরেখা ও জীবন শক্তির বিচার", "duration_minutes": 45, "is_free_preview": False},
                ],
            },
        ],
    },
    {
        "title": "কেপি জ্যোতিষ (KP Astrology) ও সাব-লর্ড গণনা",
        "slug": "kp-astrology-sub-lord-prediction-mastery",
        "subtitle": "কৃষ্ণমূর্তি পদ্ধতির গাণিতিক নির্ভুলতা ও সুনির্দিষ্ট সময়ের ফল বিচার",
        "description": "ঐতিহাসিক কৃষ্ণমূর্তি পদ্ধতি (KP System) দ্বারা ২৪৯টি সাব-ডিভিশন, নক্ষত্র অধিপতি ও সাব-লর্ডের মাধ্যমে 'হ্যাঁ' বা 'না' প্রশ্নের তাৎক্ষণিক নিখুঁত উত্তর ও যেকোনো ঘটনার সঠিক ক্ষণ নির্ণয়ের উচ্চতর পাঠক্রম।",
        "category": "kp_astrology",
        "level": "mastery",
        "language": "bn",
        "instructor_name": "ড. সুরেশ বন্দ্যোপাধ্যায়",
        "instructor_title": "কেপি জ্যোতিষ গবেষক ও সিনিয়র গাণিতিক বিশ্লেষক",
        "instructor_avatar": "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?q=80&w=300&auto=format&fit=crop",
        "instructor_bio": "কেপি অ্যাস্ট্রোলজির গাণিতিক গণনায় ২০+ বছরের আন্তর্জাতিক শিক্ষকতা।",
        "thumbnail_url": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=800&auto=format&fit=crop",
        "price": 1999.0,
        "mrp": 4999.0,
        "discount_percent": 60,
        "currency": "INR",
        "duration_hours": 14.0,
        "total_lessons": 20,
        "total_students": 118,
        "average_rating": 5.0,
        "rating_count": 42,
        "what_you_will_learn": [
            "কেপি পদ্ধতির ২৪৯টি সাব-ডিভিশন ও নক্ষত্র বিভাজন",
            "সাব-লর্ড তত্ত্ব ও ঘটনার সময় সুনির্দিষ্ট নির্ণয়",
            "চাকরি, পদোন্নতি, বিবাহ ও সন্তানলাভের কেপি সূত্র",
            "কেপি প্রশ্ন কুষ্ঠি (Horary Astrology) বিচার পদ্ধতি",
        ],
        "prerequisites": ["বৈদিক জ্যোতিষের প্রাথমিক জ্ঞান থাকা আবশ্যক"],
        "tags": ["kp_astrology", "krishnamurti", "sub_lord", "horary"],
        "is_published": True,
        "is_featured": True,
        "certificate_enabled": True,
        "sections": [
            {
                "title": "অধ্যায় ১: কেপি পদ্ধতির সূচনা ও সাব-লর্ড",
                "order": 1,
                "lessons": [
                    {"title": "কেপি শাস্ত্রের ভিত্তি ও পরাশর পদ্ধতির সাথে পার্থক্য", "duration_minutes": 45, "is_free_preview": True},
                    {"title": "প্ল্যানেট, স্টার ও সাব-লর্ডের ভূমিকা", "duration_minutes": 55, "is_free_preview": False},
                ],
            },
        ],
    },
]


async def main():
    print("Connecting to MongoDB Atlas...")
    await connect_to_mongo()

    try:
        total_created = 0
        total_updated = 0

        for cdata in COURSES_DATA:
            sections_data = cdata.pop("sections", [])
            slug = cdata["slug"]

            existing = await Course.find_one(Course.slug == slug)
            if existing:
                for k, v in cdata.items():
                    setattr(existing, k, v)
                existing.updated_at = datetime.now(timezone.utc)
                await existing.save()
                course_id = existing.id
                total_updated += 1
                print(f"Updated existing course: {cdata['title']} ({slug})")
            else:
                course = Course(**cdata)
                await course.insert()
                course_id = course.id
                total_created += 1
                print(f"Created new course: {cdata['title']} ({slug})")

            # Create sections and lessons if not already present
            existing_sections = await CourseSection.find(CourseSection.course_id == course_id).to_list()
            if not existing_sections:
                for sdata in sections_data:
                    lessons_data = sdata.pop("lessons", [])
                    section = CourseSection(
                        course_id=course_id,
                        title=sdata["title"],
                        order=sdata["order"],
                    )
                    await section.insert()

                    for l_idx, ldata in enumerate(lessons_data, 1):
                        lesson = CourseLesson(
                            course_id=course_id,
                            section_id=section.id,
                            title=ldata["title"],
                            order=l_idx,
                            duration_minutes=ldata.get("duration_minutes", 10),
                            is_free_preview=ldata.get("is_free_preview", False),
                        )
                        await lesson.insert()
                print(f"  Inserted sections & lessons for {slug}")

        print(f"\nSeeding complete! Created: {total_created}, Updated: {total_updated}")
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())
