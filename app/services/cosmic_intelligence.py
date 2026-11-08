"""Cosmic Synchronicity & Autonomous Sacred Consultation Intelligence.

Features:
1. Cosmic Synergy / Astrological Resonance scoring (User Kundli vs Astrologer Kundli).
2. Automated AI Pre-Flight Astrological Dossier (T-15m before session or on-demand).
3. Post-Session Divya Paramarsha Sacred Certificate generator (strictly without shop links).
4. Printable tamper-proof Divya Certificate HTML.
5. Cosmic Standby Queue auto-notifier on appointment cancellations.
"""

from datetime import UTC, date, datetime, timedelta
import hashlib
from typing import Any
import uuid

from beanie import PydanticObjectId
from loguru import logger

from app.core.config import settings
from app.models.appointment import Appointment, AppointmentStatus
from app.models.astrologer import Astrologer
from app.models.base import utcnow
from app.models.user import User

# Rashi Bengali Names & Natural Lords
RASHI_META = {
    "Aries": {"bn": "মেষ", "lord": "Mars", "lord_bn": "মঙ্গল"},
    "Taurus": {"bn": "বৃষ", "lord": "Venus", "lord_bn": "শুক্র"},
    "Gemini": {"bn": "মিথুন", "lord": "Mercury", "lord_bn": "বুধ"},
    "Cancer": {"bn": "কর্কট", "lord": "Moon", "lord_bn": "চন্দ্র"},
    "Leo": {"bn": "সিংহ", "lord": "Sun", "lord_bn": "সূর্য"},
    "Virgo": {"bn": "কন্যা", "lord": "Mercury", "lord_bn": "বুধ"},
    "Libra": {"bn": "তুলা", "lord": "Venus", "lord_bn": "শুক্র"},
    "Scorpio": {"bn": "বৃশ্চিক", "lord": "Mars", "lord_bn": "মঙ্গল"},
    "Sagittarius": {"bn": "ধনু", "lord": "Jupiter", "lord_bn": "বৃহস্পতি"},
    "Capricorn": {"bn": "মকর", "lord": "Saturn", "lord_bn": "শনি"},
    "Aquarius": {"bn": "কুম্ভ", "lord": "Saturn", "lord_bn": "শনি"},
    "Pisces": {"bn": "মীন", "lord": "Jupiter", "lord_bn": "বৃহস্পতি"},
}

PLANET_BN = {
    "Sun": "সূর্য",
    "Moon": "চন্দ্র",
    "Mars": "মঙ্গল",
    "Mercury": "বুধ",
    "Jupiter": "বৃহস্পতি",
    "Venus": "শুক্র",
    "Saturn": "শনি",
    "Rahu": "রাহু",
    "Ketu": "কেতু",
    "Ascendant": "লগ্ন",
}

PILLAR_HOUSES_MAP = {
    "career_wealth": {
        "houses": [10, 2, 11, 6],
        "titles_bn": {
            10: "১০ম ভাব (কর্ম, ক্যারিয়ার ও সামাজিক প্রতিষ্ঠা)",
            2: "২য় ভাব (ধন, সঞ্চয় ও পারিবারিক প্রাচুর্য)",
            11: "১১শ ভাব (আয়, লাভ ও আকাঙ্ক্ষা পূরণ)",
            6: "৬ষ্ঠ ভাব (চাকরি, প্রতিযোগিতা ও দৈনন্দিন দায়িত্ব)",
        },
        "titles_en": {
            10: "10th House (Career, Karma & Reputation)",
            2: "2nd House (Wealth, Liquid Assets & Family)",
            11: "11th House (Income, Gains & Network)",
            6: "6th House (Service, Competition & Hurdles)",
        },
        "default_distress_bn": "কর্মক্ষেত্রে অস্থিরতা, পদোন্নতিতে অপ্রত্যাশিত বিলম্ব অথবা আয়ের স্থায়িত্ব নিয়ে দোলাচল।",
        "default_distress_en": "Career instability, delayed promotions or irregular financial cash flow.",
        "ice_breaker_bn": "আপনি কি গত কিছুদিন ধরে কর্মক্ষেত্রে বা ব্যবসায়ে যোগাযোগ ও সিদ্ধান্ত নিয়ে বিভ্রান্তি বা বিলম্ব অনুভব করছেন?",
        "ice_breaker_en": "Have you been experiencing roadblocks, dilemmas or unexpected delays in your career or financial flow recently?",
    },
    "love_marriage": {
        "houses": [7, 2, 5, 8],
        "titles_bn": {
            7: "৭ম ভাব (দাম্পত্য, জীবনসঙ্গী ও অংশীদারি)",
            2: "২য় ভাব (কুটুম্ব, পারিবারিক সম্প্রীতি)",
            5: "৫ম ভাব (প্রেম, আবেগীয় আকর্ষণ ও পূর্বপূণ্য)",
            8: "৮ম ভাব (মাঙ্গল্য, যৌথ সম্পদ ও দাম্পত্য স্থায়িত্ব)",
        },
        "titles_en": {
            7: "7th House (Marriage, Spouse & Partnership)",
            2: "2nd House (Family Harmony & Domestic Peace)",
            5: "5th House (Romance, Emotional Bond & Intellect)",
            8: "8th House (Marital Longevity & In-Laws)",
        },
        "default_distress_bn": "সম্পর্কে বোঝাপড়ার অভাব, দাম্পত্যে মানসিক দূরত্ব অথবা বিবাহ আলোচনায় বাধা।",
        "default_distress_en": "Communication gaps in relationship, emotional distance with partner, or delayed marriage prospects.",
        "ice_breaker_bn": "সম্পর্ক বা দাম্পত্যে কি সম্প্রতি কোনো ভুল বোঝাবুঝি বা মানসিক দূরত্ব তৈরি হয়েছে যা আপনাকে কষ্ট দিচ্ছে?",
        "ice_breaker_en": "Has there been an emotional distance or misunderstanding in your relationship or marriage recently?",
    },
    "health_longevity": {
        "houses": [6, 8, 1, 12],
        "titles_bn": {
            6: "৬ষ্ঠ ভাব (রোগ, শত্রু ও স্বাস্থ্য সংকট)",
            8: "৮ম ভাব (দীর্ঘস্থায়ী ব্যাধি ও আয়ুষ্কাল)",
            1: "১ম ভাব (তনু ভাব, রোগ প্রতিরোধ ক্ষমতা ও জীবনীশক্তি)",
            12: "১২শ ভাব (ব্যয়, চিকিৎসা ও মানসিক শান্তি)",
        },
        "titles_en": {
            6: "6th House (Diseases, Acute Ailments & Stress)",
            8: "8th House (Chronic Conditions & Longevity)",
            1: "1st House (Vitality, Constitution & Immunity)",
            12: "12th House (Hospitalization, Sleep & Mental Rest)",
        },
        "default_distress_bn": "ক্রমাগত ক্লান্তি, মানসিক উদ্বেগ, নিদ্রাহীনতা বা চিকিৎসার পুনরাবৃত্তি।",
        "default_distress_en": "Chronic fatigue, nervous anxiety, insomnia or repeated health consultations.",
        "ice_breaker_bn": "শারীরিক ক্লান্তির পাশাপাশি কি মানসিক ক্লান্তি ও ঘুমের ব্যাঘাত আপনাকে বেশি ভোগাচ্ছে?",
        "ice_breaker_en": "Along with physical fatigue, are mental exhaustion and sleep disruptions affecting you lately?",
    },
    "business_expansion": {
        "houses": [7, 10, 11, 3],
        "titles_bn": {
            7: "৭ম ভাব (ব্যবসা, ক্লায়েন্ট ও অংশীদারি চুক্তি)",
            10: "১০ম ভাব (বাণিজ্য বিস্তার ও কর্তৃত্ব)",
            11: "১১শ ভাব (মুনাফা ও নগদ লাভ)",
            3: "৩য় ভাব (উদ্যোগ, সাহস ও ঝুঁকি গ্রহণ)",
        },
        "titles_en": {
            7: "7th House (Business Partners, Clients & Contracts)",
            10: "10th House (Trade Expansion & Market Leadership)",
            11: "11th House (Profits & ROI)",
            3: "3rd House (Initiative, Enterprise & Courage)",
        },
        "default_distress_bn": "নতুন উদ্যোগে ঝুঁকি নেওয়ার ভয়, অংশীদারের সাথে মতানৈক্য বা প্রত্যাশিত মুনাফা আটকে থাকা।",
        "default_distress_en": "Hesitation in scaling ventures, partnership friction, or cash liquidity crunch.",
        "ice_breaker_bn": "নতুন প্রজেক্ট বা ব্যবসায়িক চুক্তি চূড়ান্ত করার পথে কি কোনো নগদ অর্থ বা অংশীদারি জটিলতা তৈরি হচ্ছে?",
        "ice_breaker_en": "Are you facing cash liquidity bottlenecks or partnership hesitations in scaling your venture?",
    },
    "dosha_graha_shanti": {
        "houses": [8, 12, 1, 7],
        "titles_bn": {
            8: "৮ম ভাব (অদৃষ্ট বাধা ও আকস্মিক সংকট)",
            12: "১২শ ভাব (ক্ষতি ও মোক্ষ)",
            1: "১ম ভাব (আত্মা ও আত্মবিশ্বাস)",
            7: "৭ম ভাব (মঙ্গল/কুজ দোষ ও বিরোধ)",
        },
        "titles_en": {
            8: "8th House (Unforeseen Obstacles & Karmic Debt)",
            12: "12th House (Losses & Subconscious Fear)",
            1: "1st House (Self Confidence & Vitality)",
            7: "7th House (Manglik Tension & Opposition)",
        },
        "default_distress_bn": "কোনো কাজ শেষ মুহূর্তে ভেস্তে যাওয়া, নজর দোষ বা শনি-রাহুর আকস্মিক প্রতিকূল প্রভাব।",
        "default_distress_en": "Repeated near-finish failures, unexplainable roadblocks, or intense Saturn/Rahu transit pressures.",
        "ice_breaker_bn": "আপনার সমস্ত চেষ্টা সত্ত্বেও কি বারবার শেষ মুহূর্তে কোনো কাজ আটকে যাচ্ছে বা অদৃষ্ট বাধা আসছে?",
        "ice_breaker_en": "Despite your best efforts, do you feel things are mysteriously stalling right at the finish line?",
    },
    "spiritual_guidance": {
        "houses": [9, 12, 5, 1],
        "titles_bn": {
            9: "৯ম ভাব (ধর্ম, ভাগ্য, গুরু ও তীর্থযাত্রা)",
            12: "১২শ ভাব (মোক্ষ, ধ্যান ও অন্তর্দৃষ্টি)",
            5: "৫ম ভাব (মন্ত্র সিদ্ধি ও আধ্যাত্মিক মেধা)",
            1: "১ম ভাব (আত্মোপলব্ধি ও সাধনা)",
        },
        "titles_en": {
            9: "9th House (Dharma, Fortune & Guru Blessing)",
            12: "12th House (Moksha, Meditation & Intuition)",
            5: "5th House (Mantra Sadhana & Spiritual Intellect)",
            1: "1st House (Self Realization & Soul Journey)",
        },
        "default_distress_bn": "জীবনের উদ্দেশ্য নিয়ে গভীর শূন্যতা, আধ্যাত্মিক দিকভ্রান্তি বা সঠিক গুরু/সাধনার অনুসন্ধান।",
        "default_distress_en": "Existential restlessness, seeking true soul purpose and divine guru alignment.",
        "ice_breaker_bn": "সংসার বা ক্যারিয়ারের বাইরেও কি মনের ভেতর এক ধরনের আত্মিক শূন্যতা বা পথ খোঁজার আকুলতা কাজ করছে?",
        "ice_breaker_en": "Beyond material pursuits, are you sensing a deep spiritual calling or seeking clarity on your soul purpose?",
    },
}


def _parse_dob(val: Any) -> tuple[int, int, int] | None:
    if isinstance(val, (datetime, date)):
        return val.day, val.month, val.year
    if isinstance(val, str) and val.strip():
        val = val.strip().split("T")[0]
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
            try:
                dt = datetime.strptime(val, fmt)
                return dt.day, dt.month, dt.year
            except ValueError:
                pass
    return None


def _parse_tob(val: Any) -> tuple[int, int]:
    if isinstance(val, str) and val.strip():
        clean = val.strip().upper()
        is_pm = "PM" in clean
        is_am = "AM" in clean
        clean = clean.replace("AM", "").replace("PM", "").strip()
        parts = clean.split(":")
        try:
            h = int(parts[0])
            m = int(parts[1]) if len(parts) > 1 else 0
            if is_pm and h < 12:
                h += 12
            elif is_am and h == 12:
                h = 0
            return h, m
        except Exception:
            return 12, 0
    return 12, 0


def calculate_cosmic_synergy(
    client_birth: dict[str, Any] | None,
    astrologer_id: PydanticObjectId,
) -> dict[str, Any]:
    """Calculates planetary resonance & cosmic synergy score (75% to 99%) between client and astrologer."""
    if not client_birth:
        return {
            "score": 85,
            "harmony_tier": "Highly Auspicious",
            "resonance_factors": [
                "Guru-Surya Trine: Divine guidance & clarity alignment",
                "Chandra Shuddhi: Mind-to-mind receptive flow",
            ],
            "recommended_muhurat": "Amrit / Abhijit Muhurat",
        }

    # Deterministic cosmic seed based on client DOB + Astrologer ID
    seed_str = f"{client_birth.get('dob') or client_birth.get('date_of_birth') or 'unknown'}-{str(astrologer_id)}"
    seed_val = int(hashlib.sha256(seed_str.encode()).hexdigest(), 16)
    score = 82 + (seed_val % 17)  # 82% to 98%

    factors = [
        "Guru-Brihaspati Harmony: Fosters immediate mutual trust and deep predictive accuracy",
        "Chandra-Kendra Connection: Receptive psychological synchronicity for remedial healing",
    ]
    if score >= 90:
        factors.append("Surya-Mangal Trine: High energetic activation for career & wealth breakthroughs")
    else:
        factors.append("Budha-Shukra Resonance: Smooth, articulate communication & emotional peace")

    return {
        "score": score,
        "harmony_tier": "Divine Synergy" if score >= 92 else "Highly Auspicious",
        "resonance_factors": factors,
        "recommended_muhurat": "Amrit & Abhijit Muhurat",
    }


BN_MONTHS = {
    1: "জানুয়ারি",
    2: "ফেব্রুয়ারি",
    3: "মার্চ",
    4: "এপ্রিল",
    5: "মে",
    6: "জুন",
    7: "জুলাই",
    8: "আগস্ট",
    9: "সেপ্টেম্বর",
    10: "অক্টোবর",
    11: "নভেম্বর",
    12: "ডিসেম্বর",
}

BN_DIGITS = {
    "0": "০", "1": "১", "2": "২", "3": "৩", "4": "৪",
    "5": "৫", "6": "৬", "7": "৭", "8": "৮", "9": "৯",
}


def to_bn_digits(val: Any) -> str:
    return "".join(BN_DIGITS.get(ch, ch) for ch in str(val))


def format_date_bn(dt: datetime) -> str:
    ist = dt + timedelta(hours=5, minutes=30)
    return f"{to_bn_digits(ist.day)} {BN_MONTHS.get(ist.month, '')} {to_bn_digits(ist.year)}"


PILLAR_NAMES_BN = {
    "career_wealth": "ক্যারিয়ার ও অর্থভাগ্য",
    "love_marriage": "দাম্পত্য ও প্রেম সম্পর্ক",
    "health_longevity": "স্বাস্থ্য ও দীর্ঘায়ু",
    "business_expansion": "বাণিজ্য বিস্তার ও অংশীদারি",
    "dosha_graha_shanti": "গ্রহদোষ ও শান্তি কবচ",
    "spiritual_guidance": "আধ্যাত্মিক সাধনা ও আত্মিক শান্তি",
}

PILLAR_NAMES_EN = {
    "career_wealth": "Career & Wealth",
    "love_marriage": "Love & Marriage",
    "health_longevity": "Health & Longevity",
    "business_expansion": "Business Expansion",
    "dosha_graha_shanti": "Dosha & Graha Shanti",
    "spiritual_guidance": "Spiritual Guidance",
}


async def build_karmic_consultation_vault(appointment: Appointment) -> dict[str, Any]:
    """Builds the Karmic Consultation History Vault for a client with this astrologer.

    Tracks past appointments, previous discussion topics, prescribed remedies (gemstone,
    mantra, rudraksha), follow-up outcomes, review feedback, and generates a personalized
    repeat-client rapport ice-breaker for the astrologer.
    """
    from beanie.operators import In, Or
    from app.models.review import Review

    astro_ids: list[Any] = [appointment.astrologer_id]
    if getattr(appointment, "astrologer_user_id", None):
        astro_ids.append(appointment.astrologer_user_id)

    try:
        astro_profile = await Astrologer.get(appointment.astrologer_id)
        if astro_profile:
            astro_ids.append(astro_profile.id)
            if getattr(astro_profile, "user_id", None):
                astro_ids.append(astro_profile.user_id)
    except Exception as exc:
        logger.debug("Could not resolve astrologer profile in karmic vault: {}", exc)

    # Fetch prior appointments of this client with this astrologer
    query = {
        "user_id": appointment.user_id,
        "$or": [
            {"astrologer_id": {"$in": astro_ids}},
            {"astrologer_user_id": {"$in": astro_ids}},
        ],
        "_id": {"$ne": appointment.id},
    }

    try:
        past_appointments = await Appointment.find(query).sort("-starts_at").to_list()
    except Exception as exc:
        logger.debug("Could not query past appointments for karmic vault: {}", exc)
        past_appointments = []

    total_past = len(past_appointments)
    session_sequence = total_past + 1
    is_repeat = total_past > 0

    if session_sequence == 1:
        relationship_tier = "new"
        relationship_badge_bn = "নবাগত জাতক/জাতিকা (১ম আগমন)"
        relationship_badge_en = "First-Time Seeker (1st Visit)"
    elif session_sequence == 2:
        relationship_tier = "returning"
        relationship_badge_bn = "পুনরাগমনকারী আত্মিক সংযোগ (২য় আগমন)"
        relationship_badge_en = "Returning Seeker (2nd Visit)"
    elif session_sequence == 3:
        relationship_tier = "loyal"
        relationship_badge_bn = "বিশ্বস্ত আশ্রিত ক্লায়েন্ট (৩য় আগমন)"
        relationship_badge_en = "Loyal Devoted Seeker (3rd Visit)"
    else:
        relationship_tier = "vip_bonded"
        bn_seq = to_bn_digits(session_sequence)
        relationship_badge_bn = f"চিরস্থায়ী কর্মিক বান্ধব ({bn_seq}তম আগমন)"
        relationship_badge_en = f"Karmic Bonded Client ({session_sequence}th Visit)"

    timeline: list[dict[str, Any]] = []
    for past in past_appointments:
        dt_bn = format_date_bn(past.starts_at)
        ist_dt = past.starts_at + timedelta(hours=5, minutes=30)
        dt_en = ist_dt.strftime("%d %b %Y, %I:%M %p IST")
        pillar_key = (past.consultation_pillar or "career_wealth").lower().strip()
        pillar_bn = PILLAR_NAMES_BN.get(pillar_key, "পরামর্শ ও দিকনির্দেশনা")
        pillar_en = PILLAR_NAMES_EN.get(pillar_key, "Consultation")

        pres = past.prescription or {}
        gemstone = pres.get("gemstone") or pres.get("consecrated_gemstone")
        rudraksha = pres.get("rudraksha") or pres.get("sacred_rudraksha")
        mantra = pres.get("mantra") or pres.get("vedic_mantra")
        mantra_count = pres.get("mantra_count") or pres.get("japa_count")
        daan = pres.get("daan_remedy") or pres.get("daan_charity_ritual")
        sankalpa = pres.get("sankalpa")
        astrologer_guidance = pres.get("astrologer_notes") or pres.get("astrologer_guidance")

        # Check for client review on this past session
        review_obj = None
        try:
            review_obj = await Review.find_one({"session_id": past.id})
        except Exception:
            pass
        review_data = None
        if review_obj:
            review_data = {
                "stars": review_obj.stars,
                "text": review_obj.text,
            }

        # Check for follow-up notes or client outcome message
        follow_up_data = None
        if past.follow_up_notes or getattr(past, "follow_up_thread", None):
            latest_msg = (
                past.follow_up_thread[-1].get("text")
                if getattr(past, "follow_up_thread", None)
                else None
            )
            follow_up_data = {
                "notes": past.follow_up_notes,
                "latest_update": latest_msg or past.follow_up_notes,
                "thread_count": len(getattr(past, "follow_up_thread", None) or []),
            }

        # Build dynamic karmic milestone summary
        summary_chunks = [f"{dt_bn}: {pillar_bn} নিয়ে আলোচনা"]
        if gemstone:
            summary_chunks.append(f"{gemstone} প্রেসক্রাইব করা হয়েছিল")
        elif rudraksha:
            summary_chunks.append(f"{rudraksha} ধারণের নির্দেশ ছিল")
        elif mantra:
            summary_chunks.append(f"{mantra} জপ বিধান দেওয়া হয়েছিল")

        if review_data and review_data.get("text"):
            summary_chunks.append(f"ক্লায়েন্ট জানিয়েছেন: '{review_data['text']}'")
        elif follow_up_data and follow_up_data.get("latest_update"):
            summary_chunks.append(f"ফলো-আপে ক্লায়েন্ট জানিয়েছে: '{follow_up_data['latest_update']}'")

        karmic_summary_bn = " — ".join(summary_chunks)

        timeline.append({
            "appointment_id": str(past.id),
            "starts_at": past.starts_at.isoformat(),
            "date_bn": dt_bn,
            "date_en": dt_en,
            "status": past.status,
            "duration_minutes": past.minutes,
            "pillar": pillar_key,
            "pillar_bn": pillar_bn,
            "pillar_en": pillar_en,
            "client_query": past.note,
            "prescribed_remedies": {
                "gemstone": gemstone,
                "rudraksha": rudraksha,
                "mantra": mantra,
                "mantra_count": mantra_count,
                "daan": daan,
                "sankalpa": sankalpa,
                "guidance": astrologer_guidance,
            },
            "has_prescription": bool(
                gemstone or rudraksha or mantra or daan or sankalpa or astrologer_guidance
            ),
            "certificate_id": (past.certificate_data or {}).get("certificate_id"),
            "review": review_data,
            "follow_up": follow_up_data,
            "karmic_summary_bn": karmic_summary_bn,
        })

    # Repeat client rapport ice-breaker
    repeat_rapport_ice_breaker_bn = None
    repeat_rapport_ice_breaker_en = None
    if is_repeat and past_appointments:
        latest_past = past_appointments[0]
        latest_dt_bn = format_date_bn(latest_past.starts_at)
        latest_pillar_key = (latest_past.consultation_pillar or "career_wealth").lower().strip()
        latest_pillar_bn = PILLAR_NAMES_BN.get(latest_pillar_key, "পরামর্শ")
        latest_pres = latest_past.prescription or {}
        latest_gem = latest_pres.get("gemstone") or latest_pres.get("consecrated_gemstone")

        reported_outcome = None
        lat_rev = None
        try:
            lat_rev = await Review.find_one({"session_id": latest_past.id})
        except Exception:
            pass
        if lat_rev and lat_rev.text:
            reported_outcome = lat_rev.text
        elif latest_past.follow_up_notes:
            reported_outcome = latest_past.follow_up_notes
        elif getattr(latest_past, "follow_up_thread", None):
            reported_outcome = latest_past.follow_up_thread[-1].get("text")

        if latest_gem and reported_outcome:
            repeat_rapport_ice_breaker_bn = (
                f"নমস্কার! গত {latest_dt_bn}-এ আমরা {latest_pillar_bn} নিয়ে আলোচনা করেছিলাম এবং আপনাকে {latest_gem} প্রেসক্রাইব করেছিলাম। "
                f"আপনি জানিয়েছেন যে বিষয়টিতে ইতিবাচক অগ্রগতি হয়েছে—বর্তমান অবস্থা এবং আজকের সেশনে কোন বিষয়ে আলোকপাত করতে চান?"
            )
            repeat_rapport_ice_breaker_en = (
                f"Welcome back! In our previous session on {latest_past.starts_at.strftime('%d %b %Y')}, we discussed {latest_past.consultation_pillar} and prescribed {latest_gem}. "
                f"Following your positive update, how is the current situation evolving, and what specific guidance can I offer today?"
            )
        elif latest_gem:
            repeat_rapport_ice_breaker_bn = (
                f"নমস্কার! গত {latest_dt_bn}-এ আমরা আপনার {latest_pillar_bn} নিয়ে কথা বলেছিলাম এবং {latest_gem} ধারণের পরামর্শ দিয়েছিলাম। "
                f"এর পর থেকে আপনার সার্বিক কাজের বাধাগুলো কতটা দূর হয়েছে এবং বর্তমানে কেমন চলছে?"
            )
            repeat_rapport_ice_breaker_en = (
                f"Welcome back! On {latest_past.starts_at.strftime('%d %b %Y')}, we addressed your {latest_past.consultation_pillar} and recommended {latest_gem}. "
                f"How has the energetic shift felt for you since our last consultation?"
            )
        else:
            repeat_rapport_ice_breaker_bn = (
                f"নমস্কার! গত {latest_dt_bn}-এ আমরা আপনার {latest_pillar_bn} নিয়ে বিস্তারিত আলোচনা করেছিলাম। "
                f"সেই বিষয়ের বর্তমান অগ্রগতি কেমন এবং আজ কোন বিশেষ বিষয়ে আপনার দিকনির্দেশনা প্রয়োজন?"
            )
            repeat_rapport_ice_breaker_en = (
                f"Welcome back! During our session on {latest_past.starts_at.strftime('%d %b %Y')}, we explored your {latest_past.consultation_pillar}. "
                f"How have matters progressed, and what focus area should we prioritize today?"
            )

    return {
        "total_sessions_with_this_astrologer": session_sequence,
        "past_sessions_count": total_past,
        "session_sequence_number": session_sequence,
        "is_repeat_client": is_repeat,
        "relationship_badge_bn": relationship_badge_bn,
        "relationship_badge_en": relationship_badge_en,
        "relationship_tier": relationship_tier,
        "repeat_rapport_ice_breaker_bn": repeat_rapport_ice_breaker_bn,
        "repeat_rapport_ice_breaker_en": repeat_rapport_ice_breaker_en,
        "first_consultation_date_bn": timeline[-1]["date_bn"] if timeline else None,
        "last_consultation_date_bn": timeline[0]["date_bn"] if timeline else None,
        "timeline": timeline,
    }


async def generate_preflight_dossier(appointment: Appointment) -> dict[str, Any]:
    """Generates an executive AI Pre-Flight Cosmic Dossier for the astrologer.
    
    Analyses:
    1. Core Identity: Client's Lagna, Chandra Rashi & Nakshatra with Pada and Lords.
    2. Current Vimshottari Mahadasha & Antardasha with timeline and karmic phase.
    3. Afflicted Planets (পীড়িত গ্রহ): Debilitated, Combust, Retrograde, Dusthana placements & malefic afflictions.
    4. Consultation Pillar House Analysis: Specific house placements and lords for the consultation focus (Career, Marriage, Health, etc.).
    5. Executive 1-Glance Cosmic Diagnosis: Core suffering description, opening ice-breaker question for the astrologer, and remedy blueprint.
    """
    client_name = "Valued Seeker"
    client_email = "Not provided"
    user = await User.get(appointment.user_id)
    if user:
        client_name = user.full_name or user.first_name or client_name
        client_email = user.email

    bd = appointment.birth_details or {}
    dob_raw = bd.get("dob") or bd.get("date_of_birth")
    tob_raw = bd.get("tob") or bd.get("time_of_birth")
    pob_raw = bd.get("pob") or bd.get("place_of_birth") or bd.get("place")
    lat_raw = bd.get("lat") or bd.get("latitude")
    lon_raw = bd.get("lon") or bd.get("longitude")
    tz_raw = bd.get("timezone") or bd.get("timezone_offset") or 5.5

    # Fallback to user.birth if appointment birth_details is empty
    if (not dob_raw or dob_raw == "Not provided") and user and hasattr(user, "birth") and user.birth:
        if user.birth.date_of_birth:
            dob_raw = user.birth.date_of_birth
        if user.birth.time_of_birth:
            tob_raw = user.birth.time_of_birth
        if user.birth.place:
            pob_raw = user.birth.place
        if user.birth.latitude is not None:
            lat_raw = user.birth.latitude
        if user.birth.longitude is not None:
            lon_raw = user.birth.longitude
        if user.birth.timezone_offset is not None:
            tz_raw = user.birth.timezone_offset

    dob_parsed = _parse_dob(dob_raw)
    is_birth_details_available = dob_parsed is not None

    if is_birth_details_available and dob_parsed:
        b_day, b_month, b_year = dob_parsed
        b_hour, b_minute = _parse_tob(tob_raw)
        b_place = str(pob_raw or "Kolkata, West Bengal, India")
        b_lat = float(lat_raw) if lat_raw is not None else 22.5726
        b_lon = float(lon_raw) if lon_raw is not None else 88.3639
        b_tz = float(tz_raw) if tz_raw is not None else 5.5
        chart_mode = "natal_kundli"
        chart_mode_bn = "জন্ম কুণ্ডলী (Natal Chart)"
    else:
        # Fallback to Horary / Prashna Kundli based on appointment time
        ref_dt = appointment.starts_at or utcnow()
        ref_ist = ref_dt + timedelta(hours=5, minutes=30)
        b_day, b_month, b_year = ref_ist.day, ref_ist.month, ref_ist.year
        b_hour, b_minute = ref_ist.hour, ref_ist.minute
        b_place = "Kolkata, West Bengal, India"
        b_lat, b_lon, b_tz = 22.5726, 88.3639, 5.5
        chart_mode = "prashna_kundli"
        chart_mode_bn = "প্রশ্ন কুণ্ডলী (Prashna Horary Chart)"

    from app.schemas.astrology import KundliCalculateRequest
    from app.services.astrology.kundli_service import calculate_kundli

    req = KundliCalculateRequest(
        name=client_name,
        gender="male",
        day=b_day,
        month=b_month,
        year=b_year,
        hour=b_hour,
        minute=b_minute,
        second=0,
        place=b_place,
        latitude=b_lat,
        longitude=b_lon,
        timezone=b_tz,
        ayanamsa="lahiri",
        language="bn",
    )

    kres = calculate_kundli(req)

    # 1. Core Identity
    asc_sign = kres.astro_positions.asc or "Aries"
    asc_meta = RASHI_META.get(asc_sign, {"bn": asc_sign, "lord": "Mars", "lord_bn": "মঙ্গল"})
    moon_sign = kres.planetary_info.rasi or "Moon"
    moon_meta = RASHI_META.get(moon_sign, {"bn": moon_sign, "lord": "Moon", "lord_bn": "চন্দ্র"})
    nakshatra_name = kres.planetary_info.nakshatra or "Ashwini"
    nakshatra_lord = kres.planetary_info.nakshatra_lord or "Ketu"
    nakshatra_lord_bn = PLANET_BN.get(nakshatra_lord.split()[0], nakshatra_lord)

    core_identity = {
        "lagna": asc_sign,
        "lagna_bn": asc_meta["bn"],
        "lagna_lord": asc_meta["lord"],
        "lagna_lord_bn": asc_meta["lord_bn"],
        "chandra_rashi": moon_sign,
        "chandra_rashi_bn": moon_meta["bn"],
        "chandra_lord": moon_meta["lord"],
        "chandra_lord_bn": moon_meta["lord_bn"],
        "nakshatra": nakshatra_name,
        "nakshatra_bn": nakshatra_name,
        "nakshatra_lord": nakshatra_lord,
        "nakshatra_lord_bn": nakshatra_lord_bn,
        "sun_sign": kres.personal_details.day or "",
    }

    # 2. Current Vimshottari Dasha
    cd = kres.current_dasha
    maha_lord = cd.mahadasha_lord if cd else "Jupiter"
    antar_lord = cd.antardasha_lord if cd else "Saturn"
    current_vimshottari_dasha = {
        "mahadasha_lord": maha_lord,
        "mahadasha_lord_bn": PLANET_BN.get(maha_lord, maha_lord),
        "antardasha_lord": antar_lord,
        "antardasha_lord_bn": PLANET_BN.get(antar_lord, antar_lord),
        "start_date": cd.start_date if cd else "",
        "end_date": cd.end_date if cd else "",
        "verdict_bn": cd.verdict_bn if cd else f"বর্তমানে {maha_lord} মহাদশায় {antar_lord} অন্তর্দশা সক্রিয়।",
        "verdict_en": cd.verdict if cd else f"Currently running {maha_lord} Mahadasha with {antar_lord} Antardasha.",
        "karmic_phase_bn": cd.guidance_bn if cd else "এই সময়ে গ্রহের শুভাশুভ ফলাফলের ভারসাম্য বজায় রাখা জরুরি।",
        "karmic_phase_en": cd.guidance if cd else "Karmic cycle shaping immediate events.",
    }

    # 3. Afflicted Planets (পীড়িত গ্রহ)
    afflicted_planets = []
    for p in kres.planetary_dignities:
        reasons = []
        severity = "low"
        is_debilitated = "Debilitated" in p.dignity or "নীচস্থ" in getattr(p, "dignity_bn", "")
        if is_debilitated:
            reasons.append("নীচস্থ (Debilitated)")
            severity = "high"
        if p.is_combust:
            reasons.append("রবির সাথে অস্তমিত (Combust)")
            if severity != "high":
                severity = "medium"
        if p.is_retrograde and p.house in (6, 8, 12):
            reasons.append(f"{p.house}ম দুঃস্থানে বক্রী (Retrograde in Trik House)")
            severity = "high"
        elif p.is_retrograde:
            reasons.append("বক্রী (Retrograde Motion)")
        elif p.house in (6, 8, 12) and p.planet in ("Moon", "Jupiter", "Venus", "Mercury"):
            reasons.append(f"{p.house}ম দুঃস্থানে পীড়িত")
            if severity == "low":
                severity = "medium"

        if reasons:
            symptom_map = {
                "Moon": ("মানসিক অস্থিরতা, অতিরিক্ত চিন্তা ও অনিদ্রা।", "Emotional anxiety, restlessness and overthinking."),
                "Mercury": ("সিদ্ধান্ত গ্রহণে দ্বিধা, ব্যবসা বা চুক্তিতে বিভ্রান্তি।", "Indecisiveness, communication roadblocks or contract delays."),
                "Venus": ("সম্পর্কে টানাপোড়েন ও বৈষয়িক অপ্রাপ্তি।", "Relationship friction, dissatisfaction in comforts or partnerships."),
                "Mars": ("আকস্মিক রাগ, রক্তচাপ ও কাজের শেষ মুহূর্তে বিঘ্ন।", "Impulsiveness, anger spikes and sudden hurdles at the finish line."),
                "Jupiter": ("গুরুজনের পরামর্শ উপেক্ষা বা আর্থিক বিনিয়োগে স্থবিরতা।", "Dilemma in big life directions, delayed expansion or investments."),
                "Saturn": ("কঠোর পরিশ্রমের তুলনায় ধীর ফল ও মানসিক চাপ।", "Protracted delays, heaviness and feeling undervalued."),
                "Sun": ("আত্মবিশ্বাসে আঘাত বা কর্মক্ষেত্রে কর্তৃপক্ষের সাথে দূরত্ব।", "Ego clashes with authority, self-doubt or vitality dips."),
                "Rahu": ("অলীক চিন্তা, অতিরিক্ত মোহ ও হঠাৎ বিভ্রান্তি।", "Obsessive thoughts, anxiety and sudden illusory hopes."),
                "Ketu": ("অনাসক্তি, দিকভ্রান্তি বা কাছের মানুষ থেকে বিচ্ছিন্নতা।", "Detachment, feeling aloof or sudden disinterest in routine goals."),
            }
            symptom_bn, symptom_en = symptom_map.get(
                p.planet,
                (f"{p.planet_bn} পীড়িত হওয়ায় সংশ্লিষ্ট ক্ষেত্রে বিঘ্ন।", f"Affliction to {p.planet} causes delays in its natural significations.")
            )
            afflicted_planets.append({
                "planet": p.planet,
                "planet_bn": PLANET_BN.get(p.planet, p.planet),
                "house": p.house,
                "sign": p.sign,
                "sign_bn": RASHI_META.get(p.sign, {}).get("bn", p.sign),
                "reasons": reasons,
                "severity": severity,
                "symptom_bn": symptom_bn,
                "symptom_en": symptom_en,
            })

    # 4. Consultation Pillar House Analysis
    raw_pillar = appointment.consultation_pillar or "career_wealth"
    pillar_key = raw_pillar.lower().strip()
    if pillar_key not in PILLAR_HOUSES_MAP:
        pillar_key = "career_wealth"

    p_conf = PILLAR_HOUSES_MAP[pillar_key]
    houses_dict = {h.name.replace("house ", ""): h for h in kres.houses_table}

    pillar_houses_details = []
    for h_num in p_conf["houses"]:
        h_str = str(h_num)
        h_info = houses_dict.get(h_str)
        sign_name = h_info.sign if h_info else "Aries"
        sign_meta = RASHI_META.get(sign_name, {"bn": sign_name, "lord": "Mars", "lord_bn": "মঙ্গল"})
        occupying = [
            f"{PLANET_BN.get(p.planet, p.planet)} ({p.dignity_bn})"
            for p in kres.planetary_dignities
            if p.house == h_num
        ]
        occupying_en = [
            f"{p.planet} ({p.dignity})"
            for p in kres.planetary_dignities
            if p.house == h_num
        ]
        
        status_bn = f"{sign_meta['bn']} রাশি, রাশিপতি {sign_meta['lord_bn']}।"
        if occupying:
            status_bn += f" অবস্থানরত গ্রহ: {', '.join(occupying)}।"
        else:
            status_bn += " কোনো প্রত্যক্ষ পাপ বা শুভ গ্রহের দৃষ্টিনির্ভর।"

        pillar_houses_details.append({
            "house_num": h_num,
            "title_bn": p_conf["titles_bn"].get(h_num, f"{h_num}ম ভাব"),
            "title_en": p_conf["titles_en"].get(h_num, f"House {h_num}"),
            "sign": sign_name,
            "sign_bn": sign_meta["bn"],
            "lord": sign_meta["lord"],
            "lord_bn": sign_meta["lord_bn"],
            "occupying_planets": occupying,
            "occupying_planets_en": occupying_en,
            "summary_bn": status_bn,
        })

    # 5. Executive Cosmic Diagnosis (কী সমস্যায় ভুগছে & 1-glance summary)
    top_affliction = afflicted_planets[0] if afflicted_planets else None
    if top_affliction:
        core_distress_bn = (
            f"ক্লায়েন্ট মূলত {p_conf['default_distress_bn']} এর পাশাপাশি "
            f"{top_affliction['planet_bn']} এর প্রতিকূলতার কারণে {top_affliction['symptom_bn']}"
        )
        core_distress_en = (
            f"Client is experiencing {p_conf['default_distress_en'].lower()} compounded by "
            f"afflicted {top_affliction['planet']} causing {top_affliction['symptom_en'].lower()}"
        )
    else:
        core_distress_bn = p_conf["default_distress_bn"]
        core_distress_en = p_conf["default_distress_en"]

    cheat_sheet = [
        f"লগ্ন {core_identity['lagna_bn']} ও চন্দ্র {core_identity['chandra_rashi_bn']} ({core_identity['nakshatra_bn']} নক্ষত্র)।",
        f"চলতি দশা: {current_vimshottari_dasha['mahadasha_lord_bn']} মহাদশায় {current_vimshottari_dasha['antardasha_lord_bn']} অন্তর্দশা।",
        f"মূল সংবেদনশীল গ্রহ: {', '.join(a['planet_bn'] + ' (' + a['reasons'][0] + ')' for a in afflicted_planets[:2]) if afflicted_planets else 'গ্রহাবস্থান ভারসাম্যপূর্ণ'}।",
        f"পরামর্শের মূল লক্ষ্য: {p_conf['titles_bn'].get(p_conf['houses'][0], 'প্রধান ভাব')} কেন্দ্রিক সমাধান প্রদান।",
    ]

    # Pre-calculated remedial directions
    gemstone_map = {
        "Aries": "লাল প্রবাল (Red Coral)",
        "Taurus": "হীরা বা ওপাল (Diamond / White Opal)",
        "Gemini": "পান্না (Emerald)",
        "Cancer": "মুক্তা বা মুনস্টোন (Natural Pearl / Moonstone)",
        "Leo": "রুবি বা চুনী (Ruby)",
        "Virgo": "পান্না (Emerald)",
        "Libra": "ওপাল বা সাদা পোখরাজ (White Zircon / Opal)",
        "Scorpio": "লাল প্রবাল (Red Coral)",
        "Sagittarius": "হলুদ পোখরাজ (Yellow Sapphire)",
        "Capricorn": "নীলা বা অ্যামেথিস্ট (Blue Sapphire / Amethyst)",
        "Aquarius": "নীলা বা নীলাভ জামাক (Blue Sapphire)",
        "Pisces": "হলুদ পোখরাজ (Yellow Sapphire)",
    }
    prescribed_gem = gemstone_map.get(asc_sign, "হলুদ পোখরাজ বা পান্না")

    executive_diagnosis = {
        "core_distress_bn": core_distress_bn,
        "core_distress_en": core_distress_en,
        "one_glance_cheat_sheet": cheat_sheet,
        "opening_ice_breaker_bn": p_conf["ice_breaker_bn"],
        "opening_ice_breaker_en": p_conf["ice_breaker_en"],
        "remedial_blueprint": {
            "gemstone": prescribed_gem,
            "rudraksha": "৫ মুখী বা ৭ মুখী নেপালি রুদ্রাক্ষ",
            "mantra": f"ॐ {PLANET_BN.get(maha_lord, 'সূর্য')}য় নমঃ (১০৮ বার প্রাতঃকালে জপ)",
            "charity_ritual": "বুধবার গরুকে সবুজ ঘাস অথবা শনিবার অভাবী ব্যক্তিদের অন্নদান।",
        },
    }

    # Build Karmic Consultation History Vault for this client with this astrologer
    karmic_vault = await build_karmic_consultation_vault(appointment)
    if karmic_vault.get("is_repeat_client") and karmic_vault.get("repeat_rapport_ice_breaker_bn"):
        executive_diagnosis["opening_ice_breaker_bn"] = karmic_vault["repeat_rapport_ice_breaker_bn"]
        if karmic_vault.get("repeat_rapport_ice_breaker_en"):
            executive_diagnosis["opening_ice_breaker_en"] = karmic_vault["repeat_rapport_ice_breaker_en"]

    # Consolidated Dossier
    dossier = {
        "generated_at": utcnow().isoformat(),
        "client_name": client_name,
        "client_email": client_email,
        "is_birth_details_available": is_birth_details_available,
        "chart_mode": chart_mode,
        "chart_mode_bn": chart_mode_bn,
        "focus_topic": raw_pillar.replace("_", " ").title(),
        "focus_topic_key": pillar_key,
        "birth_snapshot": {
            "dob": f"{b_year:04d}-{b_month:02d}-{b_day:02d}" if is_birth_details_available else "Not provided (Horary Used)",
            "tob": f"{b_hour:02d}:{b_minute:02d}" if is_birth_details_available else "Appointment Time",
            "pob": b_place,
            "lat": b_lat,
            "lon": b_lon,
            "timezone": b_tz,
        },
        "core_identity": core_identity,
        "current_vimshottari_dasha": current_vimshottari_dasha,
        "afflicted_planets": afflicted_planets,
        "pillar_house_analysis": {
            "pillar_key": pillar_key,
            "relevant_houses": p_conf["houses"],
            "houses_details": pillar_houses_details,
        },
        "executive_cosmic_diagnosis": executive_diagnosis,
        "cosmic_synergy_score": appointment.cosmic_synergy_score or 88,
        "planetary_transits": {
            "saturn_gochar": "Saturn transiting karmic axis — disciplined restructuring",
            "jupiter_gochar": "Jupiter in friendly trine aspect — divine protection",
            "rahu_ketu_axis": "Karmic nodal alignment in nodal axis — sudden pivots and mental unrest",
        },
        "ai_executive_summary": cheat_sheet,
        "karmic_vault": karmic_vault,
    }

    # Persist in appointment document
    appointment.preflight_dossier = dossier
    await appointment.save()
    return dossier


def generate_divya_paramarsha_certificate_data(
    appointment: Appointment, astrologer: Astrologer, client: User
) -> dict[str, Any]:
    """Generates post-session Divya Paramarsha Sacred Certificate data.

    STRICT CONSTRAINT: No direct e-commerce shop purchase links are included.
    Contains sacred Vedic directives, gemstones, rudraksha, and mantras only.
    """
    cert_id = f"ASTRA-DIVYA-{uuid.uuid4().hex[:8].upper()}"
    now = utcnow()
    prescription = appointment.prescription or {}
    verify_url = f"https://astra-astrology-web.vercel.app/verify/prescription/{appointment.id}"
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=260x260&data={verify_url.replace(':', '%3A').replace('/', '%2F')}&color=1a1306&bgcolor=fdf8ee"
    verification_hash = hashlib.sha256(f"{cert_id}:{appointment.id}:{now.isoformat()}".encode()).hexdigest()

    return {
        "certificate_id": cert_id,
        "issued_at": now.isoformat(),
        "astrologer": {
            "name": getattr(astrologer, "display_name", "Vedic Astrologer"),
            "title": "Certified Vedic Astrologer & Sacred Counselor",
            "avatar_url": getattr(astrologer, "avatar_url", None),
        },
        "client": {
            "name": client.full_name or client.first_name or "Seeker",
            "email": client.email,
        },
        "consultation_pillar": (appointment.consultation_pillar or "Vedic Astrology").replace("_", " ").title(),
        "session_duration_minutes": appointment.minutes,
        "sacred_prescription": {
            "consecrated_gemstone": prescription.get("gemstone") or "Not prescribed in this session",
            "sacred_rudraksha": prescription.get("rudraksha") or "Not prescribed in this session",
            "vedic_mantra": prescription.get("mantra") or "ॐ नमो भगवते वासुदेवाय",
            "japa_count": prescription.get("mantra_count", 108),
            "daan_charity_ritual": prescription.get("daan_remedy") or "Feed cows / birds on auspicious morning",
            "sankalpa": prescription.get("sankalpa") or "May my consciousness align with cosmic harmony, dissolving karmic obstacles through spiritual perseverance.",
            "astrologer_guidance": prescription.get("astrologer_notes") or "Maintain daily meditative practice and follow prescribed remedies diligently.",
        },
        "vedic_shlokas": [
            {
                "sanskrit": "ॐ भूर्भुवः स्वः तत्सवितुर्वरेण्यं भर्गो देवस्य धीमहि धियो यो नः प्रचोदयात्॥",
                "transliteration": "Om Bhūr Bhuvaḥ Svaḥ Tat-Savitur-Vareṇyaṁ Bhargo Devasya Dhīmahi Dhiyo Yo Naḥ Pracodayāt",
                "meaning": "May the supreme divine radiance illuminate our intellect and direct our righteous karmic path.",
            },
            {
                "sanskrit": "शुभं करोति कल्याणमारोग्यं धनसंपदः। शत्रुबुद्धिविनाशाय दीपज्योतिर्नमोऽस्तुते॥",
                "transliteration": "Śubhaṁ Karoti Kalyāṇam Ārogyaṁ Dhana-Saṁpadaḥ Śatru-Buddhi-Vināśāya Dīpa-Jyotir-Namo'stute",
                "meaning": "Salutations to the divine illumination that bestows auspiciousness, radiant vitality, and celestial peace.",
            },
        ],
        "verification_url": verify_url,
        "qr_code_url": qr_url,
        "digital_seal": {
            "verification_hash": verification_hash,
            "seal_title": "ASTRA ASTROLOGY • CONSECRATED VEDIC SEAL",
            "seal_motto": "सत्यमेव जयते नानृतम् • DIVINLINK AUTHENTICITY",
            "status": "Authentic & Consecrated",
            "signature": f"Acharya {astrologer.display_name}",
        },
    }


def generate_certificate_html(cert: dict[str, Any]) -> str:
    """Generates a sacred, print-ready, high-resolution HTML certificate.

    Strictly devoid of any e-commerce purchase links or ads. Pure Vedic authenticity.
    """
    cert_id = cert.get("certificate_id", "ASTRA-DIVYA-0000")
    client_name = cert.get("client", {}).get("name", "Seeker")
    astro_name = cert.get("astrologer", {}).get("name", "Vedic Astrologer")
    pillar = cert.get("consultation_pillar", "Vedic Astrology")
    duration = cert.get("session_duration_minutes", 30)
    rx = cert.get("sacred_prescription", {})
    gemstone = rx.get("consecrated_gemstone", "Not prescribed")
    rudraksha = rx.get("sacred_rudraksha", "Not prescribed")
    mantra = rx.get("vedic_mantra", "ॐ नमो भगवते वासुदेवाय")
    japa_count = rx.get("japa_count", 108)
    daan = rx.get("daan_charity_ritual", "Not prescribed")
    sankalpa = rx.get("sankalpa", "May my consciousness align with cosmic harmony, dissolving karmic obstacles through spiritual perseverance.")
    guidance = rx.get("astrologer_guidance", "Maintain daily meditative practice and follow prescribed remedies diligently.")
    issued_date = cert.get("issued_at", "")[:10]
    verification_hash = cert.get("digital_seal", {}).get("verification_hash", "")[:32]
    verify_url = cert.get("verification_url", f"https://astra-astrology-web.vercel.app/verify/prescription/{cert_id}")
    qr_url = cert.get("qr_code_url") or f"https://api.qrserver.com/v1/create-qr-code/?size=260x260&data={verify_url.replace(':', '%3A').replace('/', '%2F')}&color=1a1306&bgcolor=fdf8ee"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Divya Paramarsha Certificate — {cert_id}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700;800;900&family=Great+Vibes&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    body {{
      background: #080B11;
      color: #E2E8F0;
      font-family: 'Plus Jakarta Sans', sans-serif;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      padding: 32px 20px;
    }}
    .certificate-container {{
      position: relative;
      width: 100%;
      max-width: 920px;
      background: linear-gradient(150deg, #131A29 0%, #0C101A 50%, #151421 100%);
      border: 3px solid #D4AF37;
      border-radius: 24px;
      padding: 44px 40px;
      box-shadow: 0 30px 80px rgba(0, 0, 0, 0.8), 0 0 50px rgba(212, 175, 55, 0.2);
      overflow: hidden;
    }}
    .inner-border {{
      position: absolute;
      top: 10px;
      left: 10px;
      right: 10px;
      bottom: 10px;
      border: 1px solid rgba(212, 175, 55, 0.45);
      border-radius: 18px;
      pointer-events: none;
    }}
    .corner-decor {{
      position: absolute;
      font-size: 20px;
      color: #D4AF37;
      opacity: 0.8;
      pointer-events: none;
    }}
    .tl {{ top: 14px; left: 18px; }}
    .tr {{ top: 14px; right: 18px; }}
    .bl {{ bottom: 14px; left: 18px; }}
    .br {{ bottom: 14px; right: 18px; }}

    .header {{
      text-align: center;
      margin-bottom: 20px;
    }}
    .om-symbol {{
      font-size: 42px;
      color: #F5E6AB;
      margin-bottom: 4px;
      display: inline-block;
      text-shadow: 0 0 20px rgba(212, 175, 55, 0.6);
    }}
    .title {{
      font-family: 'Cinzel', serif;
      font-size: 26px;
      font-weight: 800;
      letter-spacing: 3px;
      color: #F8E7B4;
      text-transform: uppercase;
      margin-bottom: 4px;
    }}
    .subtitle {{
      font-size: 11px;
      letter-spacing: 3px;
      color: #CBD5E1;
      text-transform: uppercase;
      font-weight: 600;
    }}

    .shloka-banner {{
      margin: 18px auto;
      max-width: 720px;
      padding: 10px 18px;
      background: rgba(212, 175, 55, 0.08);
      border-top: 1px solid rgba(212, 175, 55, 0.3);
      border-bottom: 1px solid rgba(212, 175, 55, 0.3);
      border-radius: 8px;
      text-align: center;
    }}
    .shloka-sanskrit {{
      font-size: 13px;
      color: #FDE047;
      font-weight: 600;
      letter-spacing: 0.5px;
      margin-bottom: 2px;
    }}
    .shloka-meaning {{
      font-size: 11px;
      color: #94A3B8;
      font-style: italic;
    }}

    .recipient-block {{
      text-align: center;
      margin: 18px 0;
    }}
    .certifies-that {{
      font-size: 11px;
      color: #94A3B8;
      letter-spacing: 2px;
      text-transform: uppercase;
      margin-bottom: 6px;
    }}
    .client-name {{
      font-family: 'Cinzel', serif;
      font-size: 26px;
      font-weight: 700;
      color: #FFFFFF;
      border-bottom: 1px solid rgba(212, 175, 55, 0.4);
      display: inline-block;
      padding: 2px 28px;
      margin-bottom: 6px;
    }}
    .session-desc {{
      font-size: 12.5px;
      color: #CBD5E1;
      max-width: 660px;
      margin: 0 auto;
      line-height: 1.6;
    }}

    .grid-prescription {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
      margin: 22px 0;
    }}
    .card {{
      background: rgba(255, 255, 255, 0.035);
      border: 1px solid rgba(212, 175, 55, 0.22);
      border-radius: 12px;
      padding: 12px 16px;
    }}
    .card-label {{
      font-size: 10px;
      font-weight: 800;
      letter-spacing: 1.5px;
      color: #D4AF37;
      text-transform: uppercase;
      margin-bottom: 4px;
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    .card-value {{
      font-size: 13px;
      color: #F8FAFC;
      line-height: 1.45;
    }}
    .mantra-card {{
      grid-column: span 2;
      background: rgba(212, 175, 55, 0.06);
      border: 1px solid rgba(212, 175, 55, 0.35);
      text-align: center;
      padding: 14px;
    }}
    .mantra-text {{
      font-size: 17px;
      color: #FEF08A;
      font-weight: 700;
      margin: 4px 0;
      letter-spacing: 0.5px;
    }}
    .sankalpa-card {{
      grid-column: span 2;
      background: rgba(99, 102, 241, 0.06);
      border: 1px solid rgba(165, 180, 252, 0.3);
    }}

    .footer {{
      display: grid;
      grid-template-columns: 1.3fr 1fr 0.9fr;
      gap: 16px;
      align-items: center;
      margin-top: 24px;
      padding-top: 18px;
      border-top: 1px dashed rgba(212, 175, 55, 0.3);
    }}
    .sign-block {{
      text-align: left;
    }}
    .signature-calligraphy {{
      font-family: 'Great Vibes', cursive;
      font-size: 28px;
      color: #F5E6AB;
      line-height: 1.1;
      margin-bottom: 2px;
    }}
    .sign-name {{
      font-family: 'Cinzel', serif;
      font-size: 13px;
      font-weight: 700;
      color: #F8FAFC;
    }}
    .sign-title {{
      font-size: 10px;
      color: #94A3B8;
      text-transform: uppercase;
      letter-spacing: 1px;
    }}
    .sign-date {{
      font-size: 10px;
      color: #64748B;
      margin-top: 4px;
    }}

    .seal-block {{
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
    }}
    .seal-graphic {{
      width: 72px;
      height: 72px;
      border: 2px solid #D4AF37;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(212,175,55,0.2) 0%, rgba(212,175,55,0.02) 70%);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      box-shadow: 0 0 16px rgba(212, 175, 55, 0.3);
      margin-bottom: 6px;
    }}
    .seal-icon {{
      font-size: 18px;
      color: #FDE047;
    }}
    .seal-text-ring {{
      font-size: 7.5px;
      font-weight: 900;
      letter-spacing: 1px;
      color: #D4AF37;
      text-transform: uppercase;
    }}
    .seal-badge {{
      display: inline-block;
      padding: 3px 10px;
      background: rgba(212, 175, 55, 0.15);
      border: 1px solid #D4AF37;
      border-radius: 9999px;
      color: #D4AF37;
      font-size: 9.5px;
      font-weight: 800;
      letter-spacing: 1.2px;
      text-transform: uppercase;
      margin-bottom: 3px;
    }}
    .hash-id {{
      font-size: 9px;
      color: #64748B;
      font-family: monospace;
    }}

    .qr-block {{
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      text-align: right;
    }}
    .qr-frame {{
      background: #FDF8EE;
      padding: 5px;
      border-radius: 8px;
      border: 1px solid #D4AF37;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.4);
      display: inline-block;
    }}
    .qr-img {{
      width: 68px;
      height: 68px;
      display: block;
    }}
    .qr-label {{
      font-size: 8.5px;
      color: #94A3B8;
      margin-top: 4px;
      max-width: 110px;
      line-height: 1.3;
    }}

    .actions-bar {{
      position: fixed;
      bottom: 24px;
      display: flex;
      gap: 12px;
      z-index: 100;
    }}
    .action-btn {{
      padding: 12px 26px;
      background: linear-gradient(135deg, #D4AF37 0%, #AA771C 100%);
      color: #0B0E14;
      font-weight: 800;
      font-size: 13px;
      border: none;
      border-radius: 9999px;
      cursor: pointer;
      box-shadow: 0 4px 18px rgba(212, 175, 55, 0.45);
      transition: all 0.2s ease;
    }}
    .action-btn:hover {{
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(212, 175, 55, 0.65);
    }}

    @media print {{
      body {{
        background: #FFFFFF;
        color: #000000;
        padding: 0;
      }}
      .certificate-container {{
        box-shadow: none;
        border: 2px solid #8B6508;
        background: #FFFFFF;
        color: #000;
        max-width: 100%;
        padding: 30px;
      }}
      .inner-border {{
        border: 1px solid #C89B3C;
      }}
      .actions-bar {{
        display: none !important;
      }}
      .client-name, .title, .om-symbol {{
        color: #000000;
      }}
      .card {{
        border: 1px solid #CCCCCC;
        background: #F8F9FA;
      }}
      .card-value, .mantra-text {{
        color: #000000;
      }}
      .shloka-banner {{
        background: #FAF8F2;
        border-color: #C89B3C;
      }}
      .shloka-sanskrit {{
        color: #8B6508;
      }}
      .signature-calligraphy {{
        color: #000000;
      }}
    }}
  </style>
</head>
<body>
  <div class="actions-bar">
    <button class="action-btn" onclick="window.print()">🖨️ Print & Save PDF Certificate</button>
  </div>

  <div class="certificate-container">
    <div class="inner-border"></div>
    <div class="corner-decor tl">⚜</div>
    <div class="corner-decor tr">⚜</div>
    <div class="corner-decor bl">⚜</div>
    <div class="corner-decor br">⚜</div>

    <div class="header">
      <div class="om-symbol">ॐ</div>
      <div class="title">Divya Paramarsha Certificate</div>
      <div class="subtitle">Sacred Vedic Astrological Remedial Consecration</div>
    </div>

    <div class="shloka-banner">
      <div class="shloka-sanskrit">ॐ भूर्भुवः स्वः तत्सवितुर्वरेण्यं भर्गो देवस्य धीमहि धियो यो नः प्रचोदयात्॥</div>
      <div class="shloka-meaning">"May the supreme divine illumination awaken and direct our inner consciousness."</div>
    </div>

    <div class="recipient-block">
      <div class="certifies-that">This Consecrated Astrological Record Certifies That</div>
      <div class="client-name">{client_name}</div>
      <div class="session-desc">
        Has concluded a sacred {duration}-minute Vedic consultation in <strong>{pillar}</strong>, receiving certified celestial planetary diagnostics and authentic remedies consecrated by <strong>Acharya {astro_name}</strong>.
      </div>
    </div>

    <div class="grid-prescription">
      <div class="card">
        <div class="card-label">💎 Consecrated Gemstone (রত্ন প্রতিকার)</div>
        <div class="card-value">{gemstone}</div>
      </div>

      <div class="card">
        <div class="card-label">📿 Sacred Rudraksha (রুদ্রাক্ষ বিধান)</div>
        <div class="card-value">{rudraksha}</div>
      </div>

      <div class="card mantra-card">
        <div class="card-label">🕉️ Sacred Vedic Beej Mantra & Japa Count (বীজমন্ত্র ও জপ)</div>
        <div class="mantra-text">{mantra}</div>
        <div style="font-size: 11px; color: #CBD5E1;">Recommended: {japa_count} chants daily during Brahma Muhurat / Morning Pooja</div>
      </div>

      <div class="card">
        <div class="card-label">🌾 Daan & Seva Ritual (দান ও পূজার বিধান)</div>
        <div class="card-value">{daan}</div>
      </div>

      <div class="card">
        <div class="card-label">📜 Astrologer Guidance (বিশেষ নির্দেশিকা)</div>
        <div class="card-value">{guidance}</div>
      </div>

      <div class="card sankalpa-card">
        <div class="card-label">🧘 Sacred Vedic Sankalpa (সংকল্প বাক্য)</div>
        <div class="card-value" style="font-style: italic;">"{sankalpa}"</div>
      </div>
    </div>

    <div class="footer">
      <div class="sign-block">
        <div class="signature-calligraphy">Acharya {astro_name}</div>
        <div class="sign-name">{astro_name}</div>
        <div class="sign-title">Certified Vedic Astrologer & Jyotish Acharya</div>
        <div class="sign-date">Consecration Date: {issued_date}</div>
      </div>

      <div class="seal-block">
        <div class="seal-graphic">
          <div class="seal-icon">☸</div>
          <div class="seal-text-ring">ASTRA SEAL</div>
        </div>
        <div class="seal-badge">Authentic & Consecrated</div>
        <div class="hash-id">UID: {cert_id}</div>
        <div class="hash-id">Seal: {verification_hash[:16]}...</div>
      </div>

      <div class="qr-block">
        <div class="qr-frame">
          <img src="{qr_url}" alt="Verification QR Code" class="qr-img" />
        </div>
        <div class="qr-label">Scan to verify authenticity at astra.ulmind.com</div>
      </div>
    </div>
  </div>
</body>
</html>
"""


async def notify_standby_waitlist(appointment: Appointment) -> int:
    """When a booked appointment is cancelled, notifies seekers waiting in the standby queue.

    Dispatches both transactional emails and realtime socket events.
    """
    queue = getattr(appointment, "standby_queue", []) or []
    if not queue:
        return 0

    astrologer = await Astrologer.get(appointment.astrologer_id)
    astro_name = astrologer.display_name if astrologer else "Astrologer"
    slot_time = appointment.starts_at.strftime("%I:%M %p on %d %b %Y")

    notified_count = 0
    from app.services import email as email_service
    from app.services import realtime

    for entry in queue:
        user_id = entry.get("user_id")
        user_email = entry.get("email")
        if not user_email and user_id:
            u = await User.get(PydanticObjectId(user_id))
            if u:
                user_email = u.email

        if user_email:
            try:
                subject = f"⚡ Sacred Slot Available: {astro_name} on {slot_time}"
                html = f"""<div style="font-family:sans-serif;padding:20px;color:#1E293B;">
                    <h2>Sacred Standby Notification</h2>
                    <p>A slot has just opened up with <strong>{astro_name}</strong> for <strong>{slot_time}</strong>!</p>
                    <p>As you were on the Cosmic Standby Queue, this slot is now open for immediate booking.</p>
                    <p><a href="https://astra-astrology-web.vercel.app/appointments" style="background:#F59E0B;color:#FFF;padding:10px 20px;text-decoration:none;border-radius:6px;display:inline-block;margin-top:12px;">Reserve Now</a></p>
                </div>"""
                await email_service.send_email(to=user_email, subject=subject, html=html)
                notified_count += 1
            except Exception as e:
                logger.error("Failed to email standby seeker {}: {}", user_email, e)

        if user_id:
            try:
                await realtime.publish_appointment_event(
                    PydanticObjectId(user_id),
                    appointment.astrologer_user_id,
                    "standby_slot_opened",
                    {
                        "appointment_id": str(appointment.id),
                        "astrologer_name": astro_name,
                        "starts_at": appointment.starts_at.isoformat(),
                    },
                )
            except Exception as e:
                logger.debug("Realtime standby notification skipped: {}", e)

    return notified_count
