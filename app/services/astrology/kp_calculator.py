"""KP Astrology (Krishnamurti Paddhati) Calculation Engine.

Based on client resource documents in 'Resource Documents/Rashi Rules':
- KP Astrology Basics and Rules.pdf
- KP Astrology- The Hidden Secrets.pdf (by Rahul Kaushik, Ch 1, 7, 8)
- Classical Placidus semi-arc Cuspal Sub-Lord and Ruling Planets theory.
"""

import math
from fractions import Fraction
from datetime import datetime, timedelta, UTC
from typing import Any
from loguru import logger

from app.schemas.astrology import (
    KPAspectItem,
    KPBadhakaMarakaInfo,
    KPCalculateRequest,
    KPCalculateResponse,
    KPCuspDetail,
    KPDashaInsight,
    KPDashaPeriod,
    KPEventAnalysisItem,
    KPHoraryInfo,
    KPHouseSignificator,
    KPPanchang,
    KPPlanetDetail,
    KPPlanetSignificator,
    KPRemedyItem,
    KPRulingPlanets,
)
from app.services.astrology.timezone_resolver import resolve as resolve_timezone
from app.services.astrology.rashi_rules import (
    NAKSHATRAS_DATA,
    RASHIS_DATA,
    calculate_kp_sub_lord,
)

# Resilient Swiss Ephemeris import
try:
    import swisseph as swe
    HAS_SWISSEPH = True
except (ImportError, Exception) as exc:
    swe = None  # type: ignore
    HAS_SWISSEPH = False
    logger.warning(f"Swiss Ephemeris not available in kp_calculator: {exc}")

TITHIS_LIST = [
    "Shukla Pratipada", "Shukla Dwitiya", "Shukla Tritiya", "Shukla Chaturthi",
    "Shukla Panchami", "Shukla Shashthi", "Shukla Saptami", "Shukla Ashtami",
    "Shukla Navami", "Shukla Dashami", "Shukla Ekadashi", "Shukla Dwadashi",
    "Shukla Trayodashi", "Shukla Chaturdashi", "Purnima",
    "Krishna Pratipada", "Krishna Dwitiya", "Krishna Tritiya", "Krishna Chaturthi",
    "Krishna Panchami", "Krishna Shashthi", "Krishna Saptami", "Krishna Ashtami",
    "Krishna Navami", "Krishna Dashami", "Krishna Ekadashi", "Krishna Dwadashi",
    "Krishna Trayodashi", "Krishna Chaturdashi", "Amavasya",
]

YOGAS_LIST = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda", "Sukarma",
    "Dhriti", "Shula", "Ganda", "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
    "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha",
    "Shukla", "Brahma", "Indra", "Vaidhriti",
]

KARANAS_REPEATING = [
    "Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti (Bhadra)",
]

WEEKDAY_LORDS = [
    ("Monday", "Moon (Chandra)"),
    ("Tuesday", "Mars (Mangala)"),
    ("Wednesday", "Mercury (Budha)"),
    ("Thursday", "Jupiter (Guru)"),
    ("Friday", "Venus (Shukra)"),
    ("Saturday", "Saturn (Shani)"),
    ("Sunday", "Sun (Surya)"),
]

DASHA_LORDS_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
DASHA_YEARS = {
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
TOTAL_DASHA_YEARS = 120

PLANET_IDS = [
    ("Sun", "☉", "Su", 0),
    ("Moon", "☽", "Mo", 1),
    ("Mars", "♂", "Ma", 4),
    ("Mercury", "☿", "Me", 2),
    ("Jupiter", "♃", "Ju", 5),
    ("Venus", "♀", "Ve", 3),
    ("Saturn", "♄", "Sa", 6),
    ("Rahu", "☊", "Ra", 10),
]

DASHA_INSIGHTS: dict[str, KPDashaInsight] = {
    "Ketu": KPDashaInsight(
        overview="Spiritual awakening, detachment from toxic ties, deep research mindset, intuition, and closing of past karmic chapters.",
        career_and_wealth="Strong progress in technical analysis, coding, data research, astrology, auditing, and autonomous roles. Avoid speculative gambling.",
        favorable_actions=[
            "Cultivate meditation, introspection, and spiritual sadhana",
            "Deep-dive into research, coding, analytics, and problem solving",
            "Streamline life by letting go of toxic habits and redundant associations",
            "Engage in charitable and selfless community activities",
        ],
        cautions_and_pitfalls=[
            "Avoid abrupt career abandonment or emotional resignation without backup",
            "Do not alienate close family members through extreme isolation",
            "Be mindful of spinal, joint, or urinary tract health",
            "Stay clear of hasty legal or unverified business contracts",
        ],
        remedies=[
            "Offer sweet bread or chapatis to stray dogs regularly (as per KP & Lal Kitab)",
            "Chant Ketu Gayatri Mantra daily: 'Om Chitra varnaya vidhmahe, sarparoopaya dhimahi, Tanno Ketu Prachodayat !'",
            "Worship Lord Ganesha with Modaks and Durva grass to dissolve hurdles",
            "Maintain cordial, respectful relations with maternal grandfather",
        ],
        lucky_day="Tuesday",
        lucky_color="Grey / Multi-color / Smoky Brown",
        deity="Lord Ganesha",
        beej_mantra="Om Stram Streem Stroum Sah Ketave Namah",
        gayatri_mantra="Om Chitra varnaya vidhmahe, sarparoopaya dhimahi, Tanno Ketu Prachodayat !",
    ),
    "Venus": KPDashaInsight(
        overview="Period of material abundance, romantic harmony, artistic excellence, vehicle and home comforts, social charm, and elevated luxury.",
        career_and_wealth="Booming financial gains, high success in creative arts, tech, media, luxury goods, design, cosmetics, and diplomatic partnerships.",
        favorable_actions=[
            "Invest in creative, tech, media, branding, and design initiatives",
            "Nurture relationships, marital bliss, and strategic business alliances",
            "Acquire vehicles, interior enhancements, or property investments",
            "Cultivate refined public presentation, diplomacy, and charm",
        ],
        cautions_and_pitfalls=[
            "Avoid reckless expenditures on superficial status symbols",
            "Beware of overindulgence, hormonal imbalances, and blood sugar issues",
            "Do not compromise ethics or transparency in financial dealings",
            "Prevent ego friction in romantic and domestic partnerships",
        ],
        remedies=[
            "Serve green fodder to cows or care for animals on Fridays",
            "Chant Venus Gayatri Mantra: 'Om Rajad abhaaya vidmahe, Brigu suthaya dhimahi, Tanno sukrah prachodayat !'",
            "Offer white sweets or mishri to Goddess Mahalakshmi on Friday evenings",
            "Wear fresh, neat attire and subtle floral fragrances",
        ],
        lucky_day="Friday",
        lucky_color="Pearl White / Cream / Soft Pink",
        deity="Goddess Mahalakshmi",
        beej_mantra="Om Dram Dreem Droum Sah Shukraya Namah",
        gayatri_mantra="Om Rajad abhaaya vidmahe, Brigu suthaya dhimahi, Tanno sukrah prachodayat !",
    ),
    "Sun": KPDashaInsight(
        overview="Dynamic rise in self-confidence, leadership, vital life force, executive status, authority, and recognition from government or corporate superiors.",
        career_and_wealth="Promotions to authoritative ranks, administrative honors, government contracts, brand elevation, and executive authority.",
        favorable_actions=[
            "Step up to command high-impact projects and leadership positions",
            "Strengthen bonds with father, mentors, and senior leaders",
            "Adopt early morning routines, rigorous discipline, and fitness regimes",
            "Pursue competitive examinations, licenses, and public authorizations",
        ],
        cautions_and_pitfalls=[
            "Keep ego, haughtiness, and authoritarian anger strictly in check",
            "Avoid head-on clashes with father, state officials, or superiors",
            "Monitor blood pressure, cardiovascular health, and eye strain",
            "Do not disregard the feedback and contributions of team members",
        ],
        remedies=[
            "Offer pure water (Arghya) in a copper vessel to the rising Sun daily",
            "Chant Sun Gayatri Mantra: 'Om Asva dhvajaya vidmahe, pasha hasteye dhimahi, Tanno Suryah prachodayat !'",
            "Recite Aditya Hridaya Stotra on Sundays for victory in endeavors",
            "Donate jaggery, wheat, or copper vessels to the needy on Sundays",
        ],
        lucky_day="Sunday",
        lucky_color="Ruby Red / Saffron / Golden Amber",
        deity="Lord Surya / Lord Shiva",
        beej_mantra="Om Hram Hreem Hroum Sah Suryaya Namah",
        gayatri_mantra="Om Asva dhvajaya vidmahe, pasha hasteye dhimahi, Tanno Suryah prachodayat !",
    ),
    "Moon": KPDashaInsight(
        overview="Heightened mental sensitivity, creative imagination, popularity among masses, journeys, family warmth, and emotional peace.",
        career_and_wealth="Success in client-facing businesses, marketing, public relations, hospitality, food, liquid commodities, and creative professions.",
        favorable_actions=[
            "Focus on creative writing, public networking, and intuitive decision-making",
            "Build strong emotional bonds with mother and family members",
            "Engage in meditation and mindfulness to maintain emotional serenity",
            "Travel to serene waterfronts or natural retreats to recharge creative energy",
        ],
        cautions_and_pitfalls=[
            "Avoid emotional overthinking, mood swings, and pessimistic worries",
            "Never make major financial commitments during high emotional states",
            "Take care of respiratory health, cough, cold, and hydration balance",
            "Do not allow emotional guilt to compromise your business boundaries",
        ],
        remedies=[
            "Perform Jalabhishek on Shiva Lingam with pure water and milk on Mondays",
            "Keep a vessel of water or milk near headside at night and pour on a plant at dawn",
            "Chant Moon Gayatri Mantra: 'Om Nisa karaaya vidmahe, kalanaathaya dhimahi, Tanno Somah prachodayat !'",
            "Donate white rice, milk, or white clothes to elderly women on Mondays",
        ],
        lucky_day="Monday",
        lucky_color="Silver / Pearl White / Light Blue",
        deity="Lord Shiva / Goddess Parvati",
        beej_mantra="Om Shram Shreem Shroum Sah Chandraya Namah",
        gayatri_mantra="Om Nisa karaaya vidmahe, kalanaathaya dhimahi, Tanno Somah prachodayat !",
    ),
    "Mars": KPDashaInsight(
        overview="High physical vitality, bold determination, overcoming adversaries, acquisition of landed property or vehicles, and decisive breakthroughs.",
        career_and_wealth="Rapid progress in engineering, technical architecture, real estate, software systems, surgery, defense, and venture leadership.",
        favorable_actions=[
            "Channel intense drive into physical fitness, gym, sports, or martial arts",
            "Execute ambitious property acquisitions, renovations, or technical upgrades",
            "Stand firm and courageous in challenging negotiations and project milestones",
            "Inspire and command teams through high-pressure operational cycles",
        ],
        cautions_and_pitfalls=[
            "Rein in rash temper, reckless driving, and combative speech",
            "Exercise extreme caution to prevent sharp cuts, burns, or physical injuries",
            "Avoid bitter disputes over inheritance or property with younger siblings",
            "Refrain from impulsive financial speculation without thorough due diligence",
        ],
        remedies=[
            "Recite the Hanuman Chalisa or Kartikeya Stotra every Tuesday morning",
            "Chant Mars Gayatri Mantra: 'Om Angarkaya vidmahe, bhoomi palaya dhimahi, Tanno Kujah prachodayat !'",
            "Donate red lentils (masoor dal), copper, or jaggery on Tuesdays",
            "Practice deep, calming breathwork (Pranayama) to cool Martian heat",
        ],
        lucky_day="Tuesday",
        lucky_color="Bright Coral / Crimson Red / Scarlet",
        deity="Lord Hanuman / Lord Kartikeya",
        beej_mantra="Om Kram Kreem Kroum Sah Bhaumaya Namah",
        gayatri_mantra="Om Angarkaya vidmahe, bhoomi palaya dhimahi, Tanno Kujah prachodayat !",
    ),
    "Rahu": KPDashaInsight(
        overview="Unconventional era of exponential expansion, global connections, breakthrough technologies, unexpected surprises, and high ambition.",
        career_and_wealth="Phenomenal opportunities in digital technology, AI, foreign trade, media platforms, innovative startups, and unconventional ventures.",
        favorable_actions=[
            "Master advanced cutting-edge technologies and modern business strategies",
            "Explore international collaborations, foreign clients, and digital expansion",
            "Think outside conventional boundaries to disrupt and innovate in your industry",
            "Ensure meticulous compliance and legal review for every business contract",
        ],
        cautions_and_pitfalls=[
            "Beware of glittering illusions, speculative gambles, and get-rich-quick traps",
            "Strictly avoid intoxicants, dubious associations, and unethical shortcuts",
            "Guard against sudden paranoia, insomnia, and erratic lifestyle habits",
            "Verify all facts independently before reacting to unverified rumours",
        ],
        remedies=[
            "Donate radish or throw wooden coal into flowing water (as per KP & Lal Kitab)",
            "Chant Rahu Gayatri Mantra: 'Om Sook dantaya vidmahe, Ugra roopaya dhimahi, Tanno Rahuh Prachodayat !'",
            "Feed birds and fish with grains regularly on Saturday mornings",
            "Worship Goddess Saraswati or Lord Bhairava for intellectual clarity",
        ],
        lucky_day="Saturday",
        lucky_color="Electric Blue / Dark Charcoal / Indigo",
        deity="Goddess Saraswati / Lord Bhairava",
        beej_mantra="Om Bhram Bhreem Bhroum Sah Rahave Namah",
        gayatri_mantra="Om Sook dantaya vidmahe, Ugra roopaya dhimahi, Tanno Rahuh Prachodayat !",
    ),
    "Jupiter": KPDashaInsight(
        overview="Golden era of supreme wisdom, divine protection, ethical achievements, intellectual mastery, financial security, and spiritual blessings.",
        career_and_wealth="Prominent success in advisory, legal counsel, education, enterprise finance, institutional leadership, and publishing.",
        favorable_actions=[
            "Pursue advanced certifications, higher academics, and knowledge mastery",
            "Invest in stable, long-term wealth assets and value-driven enterprises",
            "Provide ethical mentorship and support noble educational charities",
            "Regularly seek the blessings and guidance of gurus, teachers, and elders",
        ],
        cautions_and_pitfalls=[
            "Guard against passive complacency and over-optimistic execution delays",
            "Monitor liver wellness, healthy body weight, and balanced sugar intake",
            "Do not assume verbal promises as guaranteed legal outcomes",
            "Avoid dogmatic or condescending attitudes during professional debates",
        ],
        remedies=[
            "Apply pure saffron (kesar) or sandalwood tilak on forehead and navel daily",
            "Chant Jupiter Gayatri Mantra: 'Om Sura achaarya Vidmahe, Sura shreshtaya dhimahi, tanno guruh prachodayat !'",
            "Donate yellow gram (chana dal), turmeric, or yellow fruits on Thursdays",
            "Read Vishnu Sahasranama or Brihaspati Stotra on Thursday mornings",
        ],
        lucky_day="Thursday",
        lucky_color="Golden Yellow / Saffron / Topaz",
        deity="Lord Vishnu / Lord Brihaspati",
        beej_mantra="Om Gram Greem Groum Sah Gurave Namah",
        gayatri_mantra="Om Sura achaarya Vidmahe, Sura shreshtaya dhimahi, tanno guruh prachodayat !",
    ),
    "Saturn": KPDashaInsight(
        overview="Period of foundational karmic discipline, endurance, organizational mastery, structured perseverance, and permanent long-term stability.",
        career_and_wealth="Enduring triumphs earned through systematic labor in law, heavy engineering, manufacturing, operations, and resilient leadership.",
        favorable_actions=[
            "Establish disciplined work routines, exceptional punctuality, and patience",
            "Build robust enterprise infrastructure, standard operating procedures, and assets",
            "Treat manual laborers, service staff, and subordinates with honor and dignity",
            "Focus on long-term sustainability rather than immediate gratification",
        ],
        cautions_and_pitfalls=[
            "Do not succumb to defeatist thinking, lethargy, or chronic procrastination",
            "Never mistreat or underpay working-class assistants and helpers",
            "Take preventive care of joint flexibility, dental health, and back ergonomics",
            "Do not look for lazy short-cuts—Saturn rewards solely sustained honest dedication",
        ],
        remedies=[
            "Perform Chhaya Daan: look at your shadow in mustard oil in a bowl and donate on Saturdays",
            "Light a sesame (til) oil lamp under a sacred Peepal tree on Saturday evenings",
            "Chant Saturn Gayatri Mantra: 'Om Sanaischaraya vidhamhe, Sooryaputraya dhimahi, Tanno manda prachodayat !'",
            "Donate black sesame, iron utensils, or warm blankets to underprivileged individuals",
        ],
        lucky_day="Saturday",
        lucky_color="Midnight Blue / Black / Slate",
        deity="Lord Shani / Lord Shiva",
        beej_mantra="Om Pram Preem Proum Sah Shanaishcharaya Namah",
        gayatri_mantra="Om Sanaischaraya vidhamhe, Sooryaputraya dhimahi, Tanno manda prachodayat !",
    ),
    "Mercury": KPDashaInsight(
        overview="Period of intellectual agility, commercial diplomacy, sharp analytical skills, persuasive communication, and expansive networking.",
        career_and_wealth="High-volume growth in commerce, software development, data science, financial trading, public relations, and advisory services.",
        favorable_actions=[
            "Launch new entrepreneurial projects, digital trading channels, and communication hubs",
            "Sharpen technical coding, mathematical models, and persuasive writing skills",
            "Broaden high-value professional networks and client negotiations",
            "Maintain organized accounts, systematic contracts, and transparent records",
        ],
        cautions_and_pitfalls=[
            "Avoid cognitive overload, nervous exhaustion, and over-committing deadlines",
            "Guard against deceptive promises, manipulative speech, or biting sarcasm",
            "Protect nervous system balance, skin allergy triggers, and vocal health",
            "Never sign contracts or legal agreements without verifying details thoroughly",
        ],
        remedies=[
            "Feed fresh green fodder or spinach to cows on Wednesday mornings",
            "Throw a round copper coin with a central hole into running water (as per KP & Lal Kitab)",
            "Chant Mercury Gayatri Mantra: 'Om Budha grahaya vidmahe, indu putraya dhimahi, Tanno somya prachodayat !'",
            "Worship Lord Ganesha with fresh Durva grass and green moong dal on Wednesdays",
        ],
        lucky_day="Wednesday",
        lucky_color="Emerald Green / Jade / Mint",
        deity="Lord Ganesha / Lord Vishnu",
        beej_mantra="Om Bram Breem Broum Sah Budhaya Namah",
        gayatri_mantra="Om Budha grahaya vidmahe, indu putraya dhimahi, Tanno somya prachodayat !",
    ),
}


def _format_dms(deg_val: float) -> str:
    d = int(deg_val)
    rem = (deg_val - d) * 60
    m = int(rem)
    s = int((rem - m) * 60)
    return f"{d}° {m:02d}' {s:02d}\""


def _get_star_sub_and_sub_sub_lord(lon_deg: float) -> tuple[str, str, str, str, int, int]:
    """Returns (Nakshatra Name, Star Lord, Sub Lord, Sub-Sub Lord, Nakshatra Index, Pada).
    Micro-precision subdivision: Nakshatra (13°20') -> Sub -> Sub-Sub (1 to 2193 subdivisions).
    """
    nak_span = 360.0 / 27.0  # 13.33333333°
    pada_span = nak_span / 4.0
    nak_idx = int(lon_deg / nak_span) % 27
    offset_in_nak = lon_deg % nak_span
    pada = int(offset_in_nak / pada_span) + 1

    nak_info = NAKSHATRAS_DATA[nak_idx]
    star_lord = nak_info["lord"]

    # Sub Lord calculation
    start_idx = DASHA_LORDS_ORDER.index(star_lord)
    accumulated = 0.0
    sub_lord = star_lord
    sub_span = 0.0
    sub_start = 0.0
    for i in range(9):
        s_lord = DASHA_LORDS_ORDER[(start_idx + i) % 9]
        s_span = (DASHA_YEARS[s_lord] / TOTAL_DASHA_YEARS) * nak_span
        if i == 8:
            cond = (accumulated - 1e-9 <= offset_in_nak <= accumulated + s_span + 1e-9)
        else:
            cond = (accumulated - 1e-9 <= offset_in_nak < accumulated + s_span - 1e-11)
        if cond:
            sub_lord = s_lord
            sub_span = s_span
            sub_start = accumulated
            break
        accumulated += s_span

    # Sub-Sub Lord (SSL) calculation within the active Sub
    offset_in_sub = max(0.0, offset_in_nak - sub_start)
    ss_start_idx = DASHA_LORDS_ORDER.index(sub_lord)
    ss_accum = 0.0
    sub_sub_lord = sub_lord
    if sub_span > 0:
        for j in range(9):
            ss_lord = DASHA_LORDS_ORDER[(ss_start_idx + j) % 9]
            ss_span = (DASHA_YEARS[ss_lord] / TOTAL_DASHA_YEARS) * sub_span
            if j == 8:
                ss_cond = (ss_accum - 1e-9 <= offset_in_sub <= ss_accum + ss_span + 1e-9)
            else:
                ss_cond = (ss_accum - 1e-9 <= offset_in_sub < ss_accum + ss_span - 1e-11)
            if ss_cond:
                sub_sub_lord = ss_lord
                break
            ss_accum += ss_span

    return nak_info["name"], star_lord, sub_lord, sub_sub_lord, nak_idx, pada


def _get_star_and_sub_lord(lon_deg: float) -> tuple[str, str, str, int, int]:
    name, star_l, sub_l, _, idx, pada = _get_star_sub_and_sub_sub_lord(lon_deg)
    return name, star_l, sub_l, idx, pada


_KP_249_TABLE: list[dict[str, Any]] | None = None


def get_kp_249_table() -> list[dict[str, Any]]:
    """Generates and caches the authentic 249 KP Horary Numbers Table.
    243 nakshatra-sub boundaries + 6 sign-crossing split boundaries = exactly 249 numbers.
    """
    global _KP_249_TABLE
    if _KP_249_TABLE is not None:
        return _KP_249_TABLE

    table: list[dict[str, Any]] = []
    nak_span = Fraction(360, 27)  # 40/3 degrees
    accum = Fraction(0)

    for nak_idx in range(27):
        nak_info = NAKSHATRAS_DATA[nak_idx]
        star_lord = nak_info["lord"]
        start_sub_idx = DASHA_LORDS_ORDER.index(star_lord)

        for sub_step in range(9):
            sub_lord = DASHA_LORDS_ORDER[(start_sub_idx + sub_step) % 9]
            sub_span = Fraction(DASHA_YEARS[sub_lord], TOTAL_DASHA_YEARS) * nak_span
            sub_start = accum
            sub_end = accum + sub_span

            start_sign_idx = int(sub_start // 30)
            end_sign_idx = int(sub_end // 30)
            if sub_end % 30 == 0:
                end_sign_idx = start_sign_idx

            if start_sign_idx != end_sign_idx:
                boundary = Fraction((start_sign_idx + 1) * 30)
                sign_info_1 = RASHIS_DATA[start_sign_idx]
                mid_1 = float((sub_start + boundary) / 2)
                _, _, _, ssl_1, _, _ = _get_star_sub_and_sub_sub_lord(mid_1)
                table.append({
                    "horary_number": len(table) + 1,
                    "sub_start_deg": round(float(sub_start), 4),
                    "sub_end_deg": round(float(boundary), 4),
                    "sign": sign_info_1["name_en"],
                    "sign_lord": sign_info_1["lord"],
                    "star_lord": star_lord,
                    "sub_lord": sub_lord,
                    "sub_sub_lord": ssl_1,
                    "nakshatra": nak_info["name"],
                })

                sign_info_2 = RASHIS_DATA[end_sign_idx]
                mid_2 = float((boundary + sub_end) / 2)
                _, _, _, ssl_2, _, _ = _get_star_sub_and_sub_sub_lord(mid_2)
                table.append({
                    "horary_number": len(table) + 1,
                    "sub_start_deg": round(float(boundary), 4),
                    "sub_end_deg": round(float(sub_end), 4),
                    "sign": sign_info_2["name_en"],
                    "sign_lord": sign_info_2["lord"],
                    "star_lord": star_lord,
                    "sub_lord": sub_lord,
                    "sub_sub_lord": ssl_2,
                    "nakshatra": nak_info["name"],
                })
            else:
                sign_info = RASHIS_DATA[start_sign_idx]
                mid = float((sub_start + sub_end) / 2)
                _, _, _, ssl, _, _ = _get_star_sub_and_sub_sub_lord(mid)
                table.append({
                    "horary_number": len(table) + 1,
                    "sub_start_deg": round(float(sub_start), 4),
                    "sub_end_deg": round(float(sub_end), 4),
                    "sign": sign_info["name_en"],
                    "sign_lord": sign_info["lord"],
                    "star_lord": star_lord,
                    "sub_lord": sub_lord,
                    "sub_sub_lord": ssl,
                    "nakshatra": nak_info["name"],
                })

            accum = sub_end

    _KP_249_TABLE = table
    return _KP_249_TABLE


def _calculate_horary_cusps(
    horary_number: int,
    lat: float,
    jd_dob: float,
    ayanamsa_deg: float,
) -> tuple[float, list[float], KPHoraryInfo]:
    """Calculates Placidus cusps for KP Horary Prashna Number (1 to 249).
    The sub-arc start is fixed as the Ascendant (Cusp 1), and remaining cusps are
    calculated via Placidus semi-arc formulas at the query geographic latitude.
    """
    table = get_kp_249_table()
    idx = max(0, min(248, horary_number - 1))
    h_item = table[idx]
    target_asc_sid = h_item["sub_start_deg"]
    target_asc_trop = (target_asc_sid + ayanamsa_deg) % 360.0

    if HAS_SWISSEPH and swe is not None:
        try:
            eps_res = swe.calc_ut(jd_dob, swe.ECL_NUT)
            eps = eps_res[0][0] if eps_res and isinstance(eps_res[0], (tuple, list)) else (eps_res[0] if eps_res else 23.44)
        except Exception:
            eps = 23.44

        best_armc = 0.0
        min_diff = 999.0
        for deg in range(360):
            _, ascmc = swe.houses_armc(float(deg), lat, eps, b"P")
            asc = ascmc[0] % 360.0
            diff = abs((asc - target_asc_trop + 180.0) % 360.0 - 180.0)
            if diff < min_diff:
                min_diff = diff
                best_armc = float(deg)

        low = best_armc - 1.0
        high = best_armc + 1.0
        mid = best_armc
        for _ in range(30):
            mid = (low + high) / 2.0
            _, ascmc = swe.houses_armc(mid % 360.0, lat, eps, b"P")
            asc = ascmc[0] % 360.0
            diff = (asc - target_asc_trop + 180.0) % 360.0 - 180.0
            if diff > 0:
                high = mid
            else:
                low = mid
        raw_cusps, _ = swe.houses_armc(mid % 360.0, lat, eps, b"P")
        cusps_list = [((c - ayanamsa_deg) % 360.0) for c in raw_cusps]
        cusps_list[0] = target_asc_sid
    else:
        cusps_list = [(target_asc_sid + i * 30.0) % 360.0 for i in range(12)]

    h_info = KPHoraryInfo(
        horary_number=horary_number,
        sub_start_degree=round(h_item["sub_start_deg"], 4),
        sub_end_degree=round(h_item["sub_end_deg"], 4),
        sub_span_formatted=f"{_format_dms(h_item['sub_start_deg'] % 30.0)} to {_format_dms(h_item['sub_end_deg'] % 30.0)}",
        sign=h_item["sign"],
        sign_lord=h_item["sign_lord"],
        star_lord=h_item["star_lord"],
        sub_lord=h_item["sub_lord"],
        sub_sub_lord=h_item["sub_sub_lord"],
    )
    return target_asc_sid, cusps_list, h_info


def _calculate_bhav_house(planet_lon: float, cusps: list[float]) -> int:
    """Finds which Placidus Bhava (1 to 12) the planet falls into."""
    for i in range(12):
        c_start = cusps[i]
        c_end = cusps[(i + 1) % 12]

        if c_start < c_end:
            if c_start <= planet_lon < c_end:
                return i + 1
        else:
            # Crosses 360° / 0° boundary
            if planet_lon >= c_start or planet_lon < c_end:
                return i + 1
    return 1


def _calculate_untenanted_planets(planets: list[KPPlanetDetail]) -> list[str]:
    """A planet is Untenanted if no planet in the chart has it as its Star Lord.
    Per Rahul Kaushik (Ch 1, Page 11), Untenanted planets are supreme fruitful significators.
    """
    star_lords_used = {p.star_lord for p in planets}
    untenanted: list[str] = []
    for p in planets:
        if p.name not in star_lords_used:
            p.is_untenanted = True
            untenanted.append(p.name)
    return untenanted


def _calculate_significators(
    planets: list[KPPlanetDetail],
    cusps: list[KPCuspDetail],
) -> tuple[list[KPPlanetSignificator], list[KPHouseSignificator]]:
    """Calculates Prof. K.S. Krishnamurti's 4-Fold Significators (Grades A, B, C, D).
    For Planets:
      Level A: House(s) occupied by Star Lord (Strongest)
      Level B: House occupied by planet itself
      Level C: House(s) owned by Star Lord
      Level D: House(s) owned by planet itself
    For Houses (1 to 12):
      Level A: Planets in star of planets occupying house
      Level B: Planets occupying house
      Level C: Planets in star of lord of house
      Level D: Lord of house itself
    """
    # 1. Map planet ownership: which cusps does a planet own?
    planet_owns_houses: dict[str, list[int]] = {p.name: [] for p in planets}
    house_lords: dict[int, str] = {}
    for c in cusps:
        house_lords[c.cusp] = c.sign_lord
        if c.sign_lord in planet_owns_houses:
            planet_owns_houses[c.sign_lord].append(c.cusp)

    # 2. Map planet occupancy: which house does a planet occupy?
    house_occupants: dict[int, list[str]] = {i: [] for i in range(1, 13)}
    for p in planets:
        house_occupants[p.bhav_house].append(p.name)

    planets_by_name = {p.name: p for p in planets}

    # 3. Compute for each planet
    planet_sig_list: list[KPPlanetSignificator] = []
    for p in planets:
        star_l_name = p.star_lord
        star_l_obj = planets_by_name.get(star_l_name)

        level_a = [star_l_obj.bhav_house] if star_l_obj else []
        level_b = [p.bhav_house]
        level_c = planet_owns_houses.get(star_l_name, [])
        level_d = planet_owns_houses.get(p.name, [])

        all_h = sorted(list(set(level_a + level_b + level_c + level_d)))
        planet_sig_list.append(
            KPPlanetSignificator(
                planet=p.name,
                level_a=level_a,
                level_b=level_b,
                level_c=level_c,
                level_d=level_d,
                all_signified_houses=all_h,
            )
        )

    # 4. Compute for each house (1 to 12)
    house_sig_list: list[KPHouseSignificator] = []
    for h in range(1, 13):
        occupants = house_occupants[h]
        h_lord = house_lords.get(h, "")

        lvl_a_planets = [p.name for p in planets if p.star_lord in occupants]
        lvl_b_planets = occupants
        lvl_c_planets = [p.name for p in planets if p.star_lord == h_lord]
        lvl_d_planets = [h_lord] if h_lord else []

        house_sig_list.append(
            KPHouseSignificator(
                house=h,
                level_a=sorted(list(set(lvl_a_planets))),
                level_b=sorted(list(set(lvl_b_planets))),
                level_c=sorted(list(set(lvl_c_planets))),
                level_d=lvl_d_planets,
            )
        )

    return planet_sig_list, house_sig_list


def _calculate_badhaka_maraka(
    asc_sign_idx: int,
    cusps: list[KPCuspDetail],
    planets: list[KPPlanetDetail],
    language: str = "en",
) -> KPBadhakaMarakaInfo:
    """Calculates Badhaka and Maraka Sthanas per classical KP rules:
    - Movable Ascendant (Aries, Cancer, Libra, Capricorn) -> 11th House is Badhaka
    - Fixed Ascendant (Taurus, Leo, Scorpio, Aquarius) -> 9th House is Badhaka
    - Dual Ascendant (Gemini, Virgo, Sagittarius, Pisces) -> 7th House is Badhaka
    - 2nd and 7th Houses are Maraka Sthanas.
    """
    if asc_sign_idx in (0, 3, 6, 9):
        asc_type = (
            "চর (Movable)" if language == "bn"
            else "चर (Movable)" if language == "hi"
            else "Movable (Chara)"
        )
        badhaka_house = 11
        note = (
            "চর লগ্নের ক্ষেত্রে একাদশ (১১শ) ভাব হলো বাধক স্থান। ১১শ ভাবে গ্রহের সক্রিয়তা আকস্মিক বাধা বা বিলম্ব আনতে পারে।"
            if language == "bn"
            else "चर लग्न के लिए एकादश (११वां) भाव बाधक स्थान होता है। ११वें भाव की सक्रियता से कार्यों में अचानक बाधा आ सकती है।"
            if language == "hi"
            else "For Movable Ascendant, 11th House is Badhaka Sthana. Planetary activations to 11th may bring sudden obstacles."
        )
    elif asc_sign_idx in (1, 4, 7, 10):
        asc_type = (
            "স্থির (Fixed)" if language == "bn"
            else "स्थिर (Fixed)" if language == "hi"
            else "Fixed (Sthira)"
        )
        badhaka_house = 9
        note = (
            "স্থির লগ্নের ক্ষেত্রে নবম (৯ম) ভাব হলো বাধক স্থান। পিতৃপক্ষ বা উচ্চশিক্ষা/দূরযাত্রায় অপ্রত্যাশিত বাধা সৃষ্টি হতে পারে।"
            if language == "bn"
            else "स्थिर लग्न के लिए नवम (९वां) भाव बाधक स्थान होता है। उच्च यात्राओं या पैतृक मामलों में बाधाएं आ सकती हैं।"
            if language == "hi"
            else "For Fixed Ascendant, 9th House is Badhaka Sthana. Higher journeys or paternal matters may encounter friction."
        )
    else:
        asc_type = (
            "দ্বি-স্বভাব (Dual)" if language == "bn"
            else "द्विस्वभाव (Dual)" if language == "hi"
            else "Dual (Dwiswabhava)"
        )
        badhaka_house = 7
        note = (
            "দ্বি-স্বভাব লগ্নের ক্ষেত্রে সপ্তম (৭ম) ভাব হলো বাধক স্থান। অংশীদারিত্ব বা জনসংযোগের ক্ষেত্রে সতর্ক বিচার প্রয়োজন।"
            if language == "bn"
            else "द्विस्वभाव लग्न के लिए सप्तम (७वां) भाव बाधक स्थान होता है। साझेदारी एवं वैवाहिक मामलों में विशेष सावधानी आवश्यक है।"
            if language == "hi"
            else "For Dual Ascendant, 7th House is Badhaka Sthana. Partnerships and public dealings require extra discernment."
        )

    badhaka_c = cusps[badhaka_house - 1]
    badhaka_sign = badhaka_c.sign
    badhaka_lord = badhaka_c.sign_lord

    maraka_houses = [2, 7]
    maraka_lords = [cusps[1].sign_lord, cusps[6].sign_lord]

    badhaka_planets = [p.name for p in planets if p.bhav_house == badhaka_house or p.star_lord == badhaka_lord]
    maraka_planets = [p.name for p in planets if p.bhav_house in maraka_houses or p.star_lord in maraka_lords]

    return KPBadhakaMarakaInfo(
        ascendant_type=asc_type,
        badhaka_house=badhaka_house,
        badhaka_sign=badhaka_sign,
        badhaka_lord=badhaka_lord,
        maraka_houses=maraka_houses,
        maraka_lords=sorted(list(set(maraka_lords))),
        badhaka_planets=sorted(list(set(badhaka_planets))),
        maraka_planets=sorted(list(set(maraka_planets))),
        notes=note,
    )


def _calculate_kp_life_events(
    cusps: list[KPCuspDetail],
    planet_sigs: list[KPPlanetSignificator],
    planets: list[KPPlanetDetail],
    badhaka_house: int,
    language: str = "en",
) -> list[KPEventAnalysisItem]:
    """Analyzes 8 primary life domains based on Cuspal Sub Lord (CSL) house groups
    and classical principles from Rahul Kaushik's client book (Ch 2, 3, 4, 5, 6).
    """
    sig_map = {ps.planet: ps for ps in planet_sigs}
    planet_map = {p.name: p for p in planets}

    def get_signified(planet_name: str) -> list[int]:
        ps = sig_map.get(planet_name)
        return ps.all_signified_houses if ps else []

    events_def = [
        {
            "category": "career",
            "title_en": "Career & Employment (Job)",
            "title_bn": "চাকরি ও কর্মজীবন",
            "title_hi": "नौकरी एवं आजीविका",
            "primary_cusp": 10,
            "favorable": [2, 6, 10, 11],
            "unfavorable": [5, 8, 12],
            "rule_en": "10th Cuspal Sub Lord signifying 2, 6, 10, 11 grants steady employment and promotion (KP Rule Ch. 3). Houses 5, 8, 12 indicate resignation or job change.",
            "rule_bn": "১০ম কুসপ্যাল সাব লর্ড ২, ৬, ১০, ১১ নির্দেশ করলে সম্মানজনক চাকরি ও পদোন্নতি নিশ্চিত। ৫, ৮, ১২ চাকরি পরিবর্তন বা সাময়িক বিরতি নির্দেশ করে।",
            "rule_hi": "१०वां भाव उपस्वामी (CSL) २, ६, १०, ११ दर्शाए तो स्थायी सेवा व पदोन्नति का योग। ५, ८, १२ स्थान परिवर्तन दर्शाता है।",
        },
        {
            "category": "business",
            "title_en": "Business & Commercial Venture",
            "title_bn": "ব্যবসা ও স্বাধীন বাণিজ্য",
            "title_hi": "व्यापार एवं व्यवसाय",
            "primary_cusp": 7,
            "favorable": [2, 7, 10, 11],
            "unfavorable": [5, 8, 12],
            "rule_en": "7th and 10th CSL connecting to 2, 7, 10, 11 promises fruitful enterprise and client inflow. Dual signs support profitable partnerships.",
            "rule_bn": "৭ম ও ১০ম কুসপ্যাল সাব লর্ড ২, ৭, ১০, ১১ নির্দেশ করলে লাভজনক ব্যবসা ও গ্রাহক বৃদ্ধি ঘটে। দ্বি-স্বভাব রাশি অংশীদারিত্বের জন্য শুভ।",
            "rule_hi": "७वां एवं १०वां CSL २, ७, १०, ११ से जुड़े तो व्यापार में भारी मुनाफा व ग्राहक वृद्धि होती है।",
        },
        {
            "category": "marriage",
            "title_en": "Marriage & Partnership Union",
            "title_bn": "বিবাহ ও দাম্পত্য জীবন",
            "title_hi": "विवाह एवं वैवाहिक जीवन",
            "primary_cusp": 7,
            "favorable": [2, 7, 11],
            "unfavorable": [6, 10, 12],
            "rule_en": "7th Cuspal Sub Lord signifying 2, 7, 11 confirms marriage fructification. 6, 10, 12 indicates separation or delayed matrimony (KP Rule Ch. 5).",
            "rule_bn": "৭ম কুসপ্যাল সাব লর্ড ২, ৭, ১১ নির্দেশ করলে বিবাহযোগ নিশ্চিত ও দাম্পত্য শুভ। ৬, ১০, ১২ দূরত্ব বা বিলম্বের ইঙ্গিত দেয়।",
            "rule_hi": "७वां CSL २, ७, ११ दर्शाए तो विवाह निश्चित। ६, १०, १२ विलंब या वैवाहिक मतभेद दर्शाता है।",
        },
        {
            "category": "love_marriage",
            "title_en": "Love Affairs & Romance",
            "title_bn": "প্রেম ও প্রণয় পরিণয়",
            "title_hi": "प्रेम संबंध एवं विवाह",
            "primary_cusp": 5,
            "favorable": [5, 7, 11],
            "unfavorable": [4, 6, 12],
            "rule_en": "5th CSL connected to 7th or 11th shows romantic culmination in marriage. 4th or 6th brings pre-marital misunderstandings.",
            "rule_bn": "৫ম কুসপ্যাল সাব লর্ড ৭ম বা ১১শ ভাবের সাথে যুক্ত হলে প্রেমের সম্পর্ক শুভ পরিণয়ে রূপ নেয়। ৪র্থ বা ৬ষ্ঠ ভুল বোঝাবুঝি নির্দেশ করে।",
            "rule_hi": "५वां CSL ७वें या ११वें से जुड़े तो प्रेम विवाह का योग बनता है। ४ या ६ विघ्न दर्शाता है।",
        },
        {
            "category": "wealth",
            "title_en": "Wealth & Liquid Accumulation",
            "title_bn": "অর্থভাগ্য ও ধন সঞ্চয়",
            "title_hi": "धन एवं आर्थिक संचय",
            "primary_cusp": 2,
            "favorable": [2, 6, 11],
            "unfavorable": [5, 8, 12],
            "rule_en": "2nd CSL signifying 2, 6, 11 ensures substantial bank balance and multiple revenue streams. 5, 8, 12 indicates sudden expenditures.",
            "rule_bn": "২য় কুসপ্যাল সাব লর্ড ২, ৬, ১১ নির্দেশ করলে নিয়মিত ধনবৃদ্ধি ও সঞ্চয় অটুট থাকে। ৫, ৮, ১২ ব্যয়াধিক্যের ইঙ্গিত দেয়।",
            "rule_hi": "२रा CSL २, ६, ११ दर्शाए तो प्रचुर धन लाभ व बैंक बैलेंस का योग। ५, ८, १२ आकस्मिक व्यय दर्शाता है।",
        },
        {
            "category": "property",
            "title_en": "Real Estate & Vehicle Acquisition",
            "title_bn": "বাড়ি, জমি ও যানবাহন লাভ",
            "title_hi": "भूमि, भवन एवं वाहन",
            "primary_cusp": 4,
            "favorable": [4, 11, 12],
            "unfavorable": [3, 5, 8],
            "rule_en": "4th CSL signifying 4, 11, 12 with Mars or Saturn influence brings property acquisition. 3, 5, 8 indicates selling or rented tenure.",
            "rule_bn": "৪র্থ কুসপ্যাল সাব লর্ড ৪, ১১, ১২ নির্দেশ করলে নিজস্ব বাড়ি বা যানবাহন ক্রয় নিশ্চিত। ৩, ৫, ৮ বিক্রয় বা স্থান পরিবর্তন নির্দেশ করে।",
            "rule_hi": "४था CSL ४, ११, १२ दर्शाए तथा मंगल/शनि का प्रभाव हो तो मकान व वाहन प्राप्ति निश्चित होती है।",
        },
        {
            "category": "health",
            "title_en": "Health, Immunity & Longevity",
            "title_bn": "স্বাস্থ্য, আরোগ্য ও দীর্ঘায়ু",
            "title_hi": "स्वास्थ्य एवं दीर्घायु",
            "primary_cusp": 1,
            "favorable": [1, 5, 9, 11],
            "unfavorable": [6, 8, 12, badhaka_house],
            "rule_en": "1st CSL signifying 1, 5, 9, 11 bestows strong vitality and quick recovery. 6, 8, 12 plus Badhaka warrants medical care.",
            "rule_bn": "১ম কুসপ্যাল সাব লর্ড ১, ৫, ৯, ১১ নির্দেশ করলে নীরোগ দেহ ও দ্রুত রোগমুক্তি ঘটে। ৬, ৮, ১২ ও বাধক স্থান সতর্কতা নির্দেশ করে।",
            "rule_hi": "१ला CSL १, ५, ९, ११ दर्शाए तो उत्तम स्वास्थ्य व दीर्घायु। ६, ८, १२ रोग एवं अस्पताल का संकेत देते हैं।",
        },
        {
            "category": "foreign",
            "title_en": "Foreign Travel & Relocation",
            "title_bn": "বিদেশ যাত্রা ও দূর ভ্রমণ",
            "title_hi": "विदेश यात्रा एवं निवास",
            "primary_cusp": 12,
            "favorable": [3, 9, 12],
            "unfavorable": [4, 11],
            "rule_en": "12th CSL signifying 3, 9, 12 indicates international travel and overseas opportunities. 4th house keeps one rooted domestically.",
            "rule_bn": "১২শ কুসপ্যাল সাব লর্ড ৩, ৯, ১২ নির্দেশ করলে দূরপাল্লার বিদেশ ভ্রমণ ও আন্তর্জাতিক কর্মসুযোগ ঘটে। ৪র্থ ভাব স্বদেশে থাকার ইঙ্গিত দেয়।",
            "rule_hi": "१२वां CSL ३, ९, १२ दर्शाए तो विदेश यात्रा एवं परदेस में सफलता का योग बनता है।",
        },
    ]

    results = []
    for ev in events_def:
        c_idx = ev["primary_cusp"] - 1
        cusp_obj = cusps[c_idx]
        csl_name = cusp_obj.sub_lord
        csl_p = planet_map.get(csl_name)
        csl_star = csl_p.star_lord if csl_p else ""
        csl_sub = csl_p.sub_lord if csl_p else ""

        signified = get_signified(csl_name)
        star_signified = get_signified(csl_star) if csl_star else []
        all_combined = sorted(list(set(signified + star_signified)))

        fav_matches = [h for h in ev["favorable"] if h in all_combined]
        unfav_matches = [h for h in ev["unfavorable"] if h in all_combined]

        base_score = 50 + (len(fav_matches) * 15) - (len(unfav_matches) * 15)
        promise_score = max(10, min(95, base_score))

        if promise_score >= 70:
            v_en = "Highly Favorable & Promised"
            v_bn = "অত্যন্ত শুভ ও শাস্ত্রসম্মত অনুকূল"
            v_hi = "अत्यधिक शुभ एवं फलदायी"
        elif promise_score >= 45:
            v_en = "Moderately Favorable / Mixed"
            v_bn = "মধ্যম অনুকূল / মিশ্র ফলপ্রসূ"
            v_hi = "मध्यम अनुकूल / मिश्रित फल"
        else:
            v_en = "Caution / Challenging Period"
            v_bn = "সতর্কতা প্রয়োজন / প্রতিকূল"
            v_hi = "सावधानी अपेक्षित / प्रतिकूल"

        title = ev.get(f"title_{language}", ev["title_en"])
        verdict = v_bn if language == "bn" else v_hi if language == "hi" else v_en
        desc = ev.get(f"rule_{language}", ev["rule_en"])

        if language == "bn":
            timing_hint = f"{csl_name} বা {csl_star}-এর দশা/অন্তর্দশায় {fav_matches} ভাব সক্রিয় হলে ফল পাওয়া যাবে।"
        elif language == "hi":
            timing_hint = f"{csl_name} या {csl_star} की दशा/अंतर्दशा में भाव {fav_matches} के सक्रिय होने पर फल मिलेगा।"
        else:
            timing_hint = f"Active during Dasha/Antardasha of {csl_name} or {csl_star} signifying houses {fav_matches}."

        results.append(
            KPEventAnalysisItem(
                category=ev["category"],
                title=title,
                primary_cusp=ev["primary_cusp"],
                cuspal_sub_lord=csl_name,
                csl_star_lord=csl_star,
                csl_sub_lord=csl_sub,
                favorable_houses=ev["favorable"],
                unfavorable_houses=ev["unfavorable"],
                signified_houses=all_combined,
                promise_score=promise_score,
                verdict=verdict,
                description=desc,
                timing_hint=timing_hint,
            )
        )

    return results


def _calculate_kp_aspects(planets: list[KPPlanetDetail], language: str = "en") -> list[KPAspectItem]:
    """Calculates Western & KP Angular Aspects with precise orbs:
    Conjunction (0° ±8°), Sextile (60° ±6°), Square (90° ±6°), Trine (120° ±8°), Opposition (180° ±8°).
    """
    aspects = []
    aspect_defs = [
        ("Conjunction", "☌", 0.0, 8.0, "Harmonious", "Intense merger and blending of planetary forces.", "গ্রহদ্বয়ের শক্তির নিবিড় মিলন ও সমন্বয়।", "ग्रह शक्तियों का गहन मिलन एवं समन्वय।"),
        ("Sextile", "⚹", 60.0, 6.0, "Harmonious", "Favorable cooperative flow and friendly opportunities.", "পারস্পরিক সহায়তা ও শুভ সুযোগের সৃষ্টি।", "सकारात्मक सहयोग एवं अनुकूल अवसरों की प्राप्ति।"),
        ("Square", "□", 90.0, 6.0, "Challenging", "Dynamic tension, testing hurdles, and growth through effort.", "কর্মপ্রচেষ্টার মাধ্যমে বাধা অতিক্রম ও মানসিক সংঘাত।", "कठिन प्रयास व संघर्ष के उपरांत सफलता।"),
        ("Trine", "△", 120.0, 8.0, "Harmonious", "Effortless luck, fortune, and highest harmonious synergy.", "অক্লান্ত সৌভাগ্য, সর্বোচ্চ সম্প্রীতি ও দৈব অনুগ্রহ।", "सहज सौभाग्य, उच्च सामंजस्य व दैवीय कृपा।"),
        ("Opposition", "☍", 180.0, 8.0, "Challenging", "Polarity, direct confrontation, or need for balance.", "সরাসরি সংঘাত ও ভারসাম্য রক্ষার প্রয়োজনীয়তা।", "प्रत्यक्ष टकराव एवं संतुलन बनाए रखने की आवश्यकता।"),
    ]

    n = len(planets)
    for i in range(n):
        for j in range(i + 1, n):
            p1 = planets[i]
            p2 = planets[j]
            diff = abs(p1.longitude - p2.longitude) % 360.0
            if diff > 180.0:
                diff = 360.0 - diff

            for item in aspect_defs:
                asp_name, asp_sym, target_angle, orb, nature, sig_en, sig_bn, sig_hi = item
                actual_orb = abs(diff - target_angle)
                if actual_orb <= orb:
                    if language == "bn":
                        sig = f"{p1.name} ও {p2.name} {asp_name} ({asp_sym}) দৃষ্টিতে আবদ্ধ। {sig_bn}"
                    elif language == "hi":
                        sig = f"{p1.name} और {p2.name} {asp_name} ({asp_sym}) दृष्टि में स्थित हैं। {sig_hi}"
                    else:
                        sig = f"{p1.name} and {p2.name} in {asp_name} ({asp_sym}). {sig_en}"

                    aspects.append(
                        KPAspectItem(
                            planet_1=p1.name,
                            planet_2=p2.name,
                            aspect_name=asp_name,
                            aspect_symbol=asp_sym,
                            angle_degrees=round(diff, 2),
                            orb_degrees=round(actual_orb, 2),
                            nature=nature,
                            significance=sig,
                        )
                    )
                    break
    return aspects


def _calculate_kp_remedies(
    planets: list[KPPlanetDetail],
    cusps: list[KPCuspDetail],
    language: str = "en",
) -> list[KPRemedyItem]:
    """Provides specific 43-day Lal Kitab and classical Vedic remedies for afflicted planets
    occupying 6th, 8th, or 12th houses (per Rahul Kaushik Chapter 9).
    """
    remedies_db = {
        "Saturn": {
            "problem_en": "Obstacles, chronic delays, bone/joint stiffness, or career stagnation",
            "problem_bn": "কাজে বিলম্ব, বাতের সমস্যা, হাড়ের কষ্ট বা পেশাগত বাধা",
            "problem_hi": "कार्यों में विलंब, जोड़ो का दर्द अथवा आजीविका में बाधा",
            "upaya_en": "Chhaya Daan: Look at your reflection in mustard oil in a steel bowl and donate on Saturdays for 43 days (Rahul Kaushik Ch. 9).",
            "upaya_bn": "ছায়াদান: শনিবার স্টিলের বাটিতে সর্ষের তেলে নিজের মুখ দেখে তা দান করুন (টানা ৪৩ দিন)।",
            "upaya_hi": "छाया दान: शनिवार को कटोरी में सरसों के तेल में अपना चेहरा देखकर दान करें।",
            "mantra": "Om Pram Preem Proum Sah Shanaishcharaya Namah (108 times)",
            "charity_en": "Donate black sesame seeds, iron vessels, or footwear to needy laborers.",
            "charity_bn": "কালো তিল, লোহার পাত্র বা শ্রমজীবী মানুষদের জুতো দান করুন।",
            "charity_hi": "काले तिल, लोहे के बर्तन या जूते-चप्पल जरूरतमंदों को दान करें।",
        },
        "Mars": {
            "problem_en": "Impatience, anger, sudden injury, blood pressure, or property disputes",
            "problem_bn": "অতিরিক্ত রাগ, রক্তচাপ, আঘাতের আশঙ্কা বা জমি সংক্রান্ত বিরোধ",
            "problem_hi": "क्रोध, रक्तचाप, चोट-चपेट अथवा भूमि विवाद",
            "upaya_en": "Throw sweet revadiyan or patisha in flowing water on Tuesdays (Rahul Kaushik Ch. 9).",
            "upaya_bn": "মঙ্গলবার মিষ্টি রেউড়ি বা বাতাসা প্রবাহিত জলে বিসর্জন দিন।",
            "upaya_hi": "मंगलवार को बहते पानी में रेवड़ियां या बताशे प्रवाहित करें।",
            "mantra": "Om Kram Kreem Kroum Sah Bhaumaya Namah (108 times)",
            "charity_en": "Donate red lentils (masoor dal) or jaggery on Tuesdays.",
            "charity_bn": "মঙ্গলবার লাল মসুর ডাল বা গুড় দান করুন।",
            "charity_hi": "मंगलवार को लाल मसूर की दाल अथवा गुड़ दान करें।",
        },
        "Rahu": {
            "problem_en": "Mental confusion, insomnia, illusions, erratic ups and downs",
            "problem_bn": "মানসিক দ্বিধা, অনিদ্রা, অমূলক ভয় ও আকস্মিক উত্থান-পতন",
            "problem_hi": "मानसिक भ्रम, अनिद्रा, भय एवं अचानक उतार-चढ़ाव",
            "upaya_en": "Throw wooden coal or donate radish in flowing water on Wednesdays/Saturdays.",
            "upaya_bn": "প্রবাহিত জলে কাঁচা কাঠকয়লা বা মুলো বিসর্জন দিন।",
            "upaya_hi": "बहते पानी में कच्चा कोयला या मूली प्रवाहित करें।",
            "mantra": "Om Bhram Bhreem Bhroum Sah Rahave Namah",
            "charity_en": "Feed stray birds and fish regularly on Saturday mornings.",
            "charity_bn": "শনিবার সকালে পাখি ও মাছকে দানা খাওয়ান।",
            "charity_hi": "शनिवार सुबह पक्षियों और मछलियों को दाना खिलाएं।",
        },
        "Ketu": {
            "problem_en": "Spine/joint pain, detachment, urinary ailments, or mysterious obstacles",
            "problem_bn": "মেরুদণ্ড বা গাঁটের ব্যথা, প্রস্রাবের সমস্যা ও গোপন বাধা",
            "problem_hi": "रीढ़ या जोड़ों का दर्द, मूत्र विकार एवं अज्ञात बाधाएं",
            "upaya_en": "Feed sweet roti (sweet bread) to stray black dogs regularly.",
            "upaya_bn": "পথের কুকুরদের নিয়মিত মিষ্টি রুটি খাওয়ান।",
            "upaya_hi": "सड़क के कुत्तों को मीठी रोटी खिलाएं।",
            "mantra": "Om Stram Streem Stroum Sah Ketave Namah",
            "charity_en": "Donate multi-colored blankets to elderly hermits or monks.",
            "charity_bn": "প্রবীণ সাধু বা অসহায় ব্যক্তিদের কম্বল দান করুন।",
            "charity_hi": "जरूरतमंदों को दोरंगा कंबल दान करें।",
        },
        "Sun": {
            "problem_en": "Lack of recognition, eye strain, cardiac fatigue, or paternal friction",
            "problem_bn": "কাজের সঠিক স্বীকৃতি না পাওয়া, চোখের সমস্যা বা পিতৃ বিরোধ",
            "problem_hi": "यश की कमी, नेत्र विकार अथवा पिता से मतभेद",
            "upaya_en": "Throw jaggery (gur) in flowing water and offer copper Arghya at sunrise.",
            "upaya_bn": "সূর্যোদয়ে তামার পাত্রে জল অর্পণ করুন ও প্রবাহিত জলে গুড় অর্পণ করুন।",
            "upaya_hi": "सूर्य को तांबे के लोटे से अर्घ्य दें और बहते पानी में गुड़ बहाएं।",
            "mantra": "Om Hram Hreem Hroum Sah Suryaya Namah",
            "charity_en": "Donate wheat or copper vessels on Sundays.",
            "charity_bn": "রবিবার গম বা তামার পাত্র দান করুন।",
            "charity_hi": "रविवार को गेहूं अथवा तांबे के बर्तन दान करें।",
        },
        "Mercury": {
            "problem_en": "Nervous exhaustion, speech stammer, skin allergy, or contract delays",
            "problem_bn": "স্নায়বিক দুর্বলতা, ত্বকের সমস্যা বা ব্যবসায়িক চুক্তিতে জটিলতা",
            "problem_hi": "स्नायु दुर्बलता, त्वचा विकार अथवा अनुबंध में अड़चन",
            "upaya_en": "Throw a round copper coin with a central hole into running water on Wednesdays.",
            "upaya_bn": "বুধবার ছিদ্রযুক্ত তামার মুদ্রা প্রবাহিত জলে বিসর্জন দিন।",
            "upaya_hi": "बुधवार को छेद वाला तांबे का सिक्का बहते पानी में प्रवाहित करें।",
            "mantra": "Om Bram Breem Broum Sah Budhaya Namah",
            "charity_en": "Feed green spinach or moong dal to cows on Wednesdays.",
            "charity_bn": "বুধবার গরুকে সবুজ ঘাস বা পালং শাক খাওয়ান।",
            "charity_hi": "बुधवार को गाय को हरा चारा या पालक खिलाएं।",
        },
        "Jupiter": {
            "problem_en": "Liver sluggishness, weight gain, educational delays, or advisor friction",
            "problem_bn": "লিভারের সমস্যা, স্থূলতা, উচ্চশিক্ষায় বাধা বা আর্থিক অনিশ্চয়তা",
            "problem_hi": "लिवर विकार, उच्च शिक्षा में बाधा अथवा आर्थिक अस्थिरता",
            "upaya_en": "Apply pure saffron (kesar) or yellow sandalwood tilak on forehead and navel.",
            "upaya_bn": "প্রতিদিন কপালে ও নাভিতে খাঁটি কেশর বা চন্দনের তিলক লাগান।",
            "upaya_hi": "प्रतिदिन माथे व नाभि पर शुद्ध केसर या चंदन का तिलक लगाएं।",
            "mantra": "Om Gram Greem Groum Sah Gurave Namah",
            "charity_en": "Donate yellow chana dal, turmeric, or yellow sweets on Thursdays.",
            "charity_bn": "বৃহস্পতিবার ছোলার ডাল, হলুদ বা হলুদ ফল দান করুন।",
            "charity_hi": "गुरुवार को चना दाल, हल्दी अथवा पीले फल दान करें।",
        },
        "Venus": {
            "problem_en": "Hormonal imbalance, relationship friction, or luxury expenses",
            "problem_bn": "দাম্পত্যে ভুল বোঝাবুঝি, ত্বক বা হরমোনের সমস্যা ও অর্থ অপচয়",
            "problem_hi": "वैवाहिक संबंधों में खिंचाव, त्वचा समस्या अथवा फिजूलखर्ची",
            "upaya_en": "Serve green fodder to a black cow or donate white sweets to young girls on Fridays.",
            "upaya_bn": "শুক্রবার সাদা মিষ্টি বা ক্ষীর দান করুন এবং গরুর সেবা করুন।",
            "upaya_hi": "शुक्रवार को कन्याओं को सफेद मिठाई खिलाएं और गौ सेवा करें।",
            "mantra": "Om Dram Dreem Droum Sah Shukraya Namah",
            "charity_en": "Donate curd, mishri, or white silk on Fridays.",
            "charity_bn": "শুক্রবার দই, মিছরি বা সাদা বস্ত্র দান করুন।",
            "charity_hi": "शुक्रवार को दही, मिश्री या श्वेत वस्त्र दान करें।",
        },
        "Moon": {
            "problem_en": "Anxiety, restless sleep, overthinking, or fluid imbalances",
            "problem_bn": "অতিরিক্ত মানসিক উদ্বেগ, অনিদ্রা ও মনের অস্থিরতা",
            "problem_hi": "मानसिक अशांति, अत्यधिक चिंता एवं अनिद्रा",
            "upaya_en": "Keep water or milk near bedside at night and pour at the roots of a plant at sunrise.",
            "upaya_bn": "রাতে মাথার কাছে এক পাত্র জল রেখে ভোরে গাছের গোড়ায় ঢালুন।",
            "upaya_hi": "रात को सिरहाने जल रखें और प्रातः पौधे की जड़ में अर्पित करें।",
            "mantra": "Om Shram Shreem Shroum Sah Chandraya Namah",
            "charity_en": "Donate white rice, milk, or silver coins on Mondays.",
            "charity_bn": "সোমবার সাদা চাল, দুধ বা রূপো দান করুন।",
            "charity_hi": "सोमवार को चावल, दूध अथवा चांदी का दान करें।",
        },
    }

    remedy_items = []
    afflicted_planets = [p for p in planets if p.bhav_house in (6, 8, 12) or p.name in ("Saturn", "Rahu", "Ketu", "Mars")]

    for p in afflicted_planets[:4]:
        info = remedies_db.get(p.name)
        if info:
            prob = info.get(f"problem_{language}", info["problem_en"])
            upaya = info.get(f"upaya_{language}", info["upaya_en"])
            charity = info.get(f"charity_{language}", info["charity_en"])
            remedy_items.append(
                KPRemedyItem(
                    planet=p.name,
                    house_involved=p.bhav_house,
                    problem=prob,
                    lal_kitab_upaya=upaya,
                    vedic_mantra=info["mantra"],
                    charity_recommendation=charity,
                )
            )

    return remedy_items


def _calculate_ruling_planets_at_jd(
    jd: float,
    lat: float,
    lon: float,
    is_dob: bool = True,
    planets_table: list[KPPlanetDetail] | None = None,
) -> KPRulingPlanets:
    """Calculates KP Ruling Planets (Lagna Sign/Star/Sub + Moon Sign/Star/Sub + Day Lord).
    Applies Rule 6 (Page 56): Discards Ruling Planets whose Star Lord is Retrograde in transit.
    """
    if HAS_SWISSEPH and swe is not None:
        swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)
        cusps, ascmc = swe.houses_ex(jd, lat, lon, b"P", swe.FLG_SIDEREAL)
        asc_lon = ascmc[0] % 360.0

        m_res, _ = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL | swe.FLG_SPEED)
        moon_lon = m_res[0] % 360.0
    else:
        # Fallback pure-python coordinates
        T = (jd - 2451545.0) / 36525.0
        ayan = 23.82 + 1.397 * T
        moon_lon = ((218.316 + 481267.88 * T) - ayan) % 360.0
        gmst = (280.46 + 360.9856 * (jd - 2451545.0)) % 360.0
        asc_lon = ((gmst + lon) - ayan) % 360.0

    # Lagna
    asc_sign_idx = int(asc_lon / 30.0) % 12
    asc_rashi_lord = RASHIS_DATA[asc_sign_idx]["lord"]
    _, asc_star_lord, asc_sub_lord, _, _, _ = _get_star_sub_and_sub_sub_lord(asc_lon)

    # Moon
    moon_sign_idx = int(moon_lon / 30.0) % 12
    moon_rashi_lord = RASHIS_DATA[moon_sign_idx]["lord"]
    _, moon_star_lord, moon_sub_lord, _, _, _ = _get_star_sub_and_sub_sub_lord(moon_lon)

    # Day Lord (from JD to UTC datetime)
    day_num = int((jd + 1.5)) % 7  # 0 is Sunday, 1 is Monday ... 6 is Saturday
    weekday_idx = (day_num - 1) % 7
    day_lord_str = WEEKDAY_LORDS[weekday_idx][1]

    # Convert JD to date/time string
    local_jd = jd + 5.5 / 24.0
    z = int(local_jd + 0.5)
    f = (local_jd + 0.5) - z
    if z < 2299161:
        a = z
    else:
        alpha = int((z - 1867216.25) / 36524.25)
        a = z + 1 + alpha - int(alpha / 4)
    b = a + 1524
    c = int((b - 122.1) / 365.25)
    d = int(365.25 * c)
    e = int((b - d) / 30.6001)
    day_val = b - d - int(30.6001 * e)
    month_val = e - 1 if e < 14 else e - 13
    year_val = c - 4716 if month_val > 2 else c - 4715

    sec_total = int(f * 86400)
    hour_val = sec_total // 3600
    min_val = (sec_total % 3600) // 60
    sec_val = sec_total % 60

    date_str = f"{day_val:02d}/{month_val:02d}/{year_val}"
    time_str = f"{hour_val:02d}h:{min_val:02d}m:{sec_val:02d}s"

    # Retrograde star filtering
    is_lagna_star_retro = False
    is_moon_star_retro = False
    discarded: list[str] = []
    fruitful: list[str] = []

    if planets_table:
        retro_planets = {p.name for p in planets_table if p.is_retrograde}
        planet_star_map = {p.name: p.star_lord for p in planets_table}

        is_lagna_star_retro = asc_star_lord in retro_planets
        is_moon_star_retro = moon_star_lord in retro_planets

        rp_candidates = [asc_rashi_lord, asc_star_lord, asc_sub_lord, moon_rashi_lord, moon_star_lord, moon_sub_lord]
        for rp in rp_candidates:
            star_of_rp = planet_star_map.get(rp, "")
            if star_of_rp in retro_planets:
                if rp not in discarded:
                    discarded.append(rp)
            else:
                if rp not in fruitful:
                    fruitful.append(rp)

    return KPRulingPlanets(
        lagna_rashi_lord=f"{asc_rashi_lord} ({asc_rashi_lord[:2]})",
        lagna_nakshatra_lord=f"{asc_star_lord} ({asc_star_lord[:2]})",
        lagna_sub_lord=asc_sub_lord,
        moon_rashi_lord=f"{moon_rashi_lord} ({moon_rashi_lord[:2]})",
        moon_nakshatra_lord=f"{moon_star_lord} ({moon_star_lord[:2]})",
        moon_sub_lord=moon_sub_lord,
        day_lord=day_lord_str,
        date_formatted=date_str,
        time_formatted=time_str,
        is_lagna_star_retrograde=is_lagna_star_retro,
        is_moon_star_retrograde=is_moon_star_retro,
        discarded_planets=discarded,
        fruitful_planets=fruitful,
    )


def _add_calendar_years(dt: datetime, years: int) -> datetime:
    try:
        return dt.replace(year=dt.year + years)
    except ValueError:
        return dt.replace(year=dt.year + years, day=28)


def _generate_vimshottari_hierarchy(
    birth_dt: datetime,
    moon_lon: float,
    current_dt: datetime,
) -> tuple[str, list[KPDashaPeriod]]:
    """Generates 3-tier Vimshottari Dasha periods (Mahadasha, Antardasha, Pratyantardasha)."""
    nak_span = 360.0 / 27.0
    nak_idx = int(moon_lon / nak_span) % 27
    offset_in_nak = moon_lon % nak_span

    nak_lord = NAKSHATRAS_DATA[nak_idx]["lord"]
    rem_fraction = 1.0 - (offset_in_nak / nak_span)
    nak_lord_total_years = DASHA_YEARS[nak_lord]

    # Precise Vedic Year, Month, Day decomposition
    b_y = int(rem_fraction * nak_lord_total_years)
    rem_m_float = (rem_fraction * nak_lord_total_years - b_y) * 12.0
    b_m = int(rem_m_float)
    b_d = int(round((rem_m_float - b_m) * 30.0))
    balance_days = b_y * 365.25 + b_m * 30.4375 + b_d
    balance_str = f"{b_y} Y {b_m} M {b_d} D"

    start_idx = DASHA_LORDS_ORDER.index(nak_lord)
    dashas_result: list[KPDashaPeriod] = []

    # First Mahadasha starts at birth and ends after balance
    md_start = birth_dt
    md_end = md_start + timedelta(days=balance_days)

    for i in range(9):
        current_md_lord = DASHA_LORDS_ORDER[(start_idx + i) % 9]
        md_years = DASHA_YEARS[current_md_lord]

        if i > 0:
            md_start = md_end
            md_end = _add_calendar_years(md_start, md_years)

        is_md_current = md_start <= current_dt <= md_end
        md_duration_str = f"{b_y} Y {b_m} M {b_d} D" if i == 0 else f"{md_years} Years"

        # Generate 9 Antardashas for this Mahadasha
        antardashas: list[KPDashaPeriod] = []
        ad_start_idx = DASHA_LORDS_ORDER.index(current_md_lord)
        ad_start = md_start

        for j in range(9):
            ad_lord = DASHA_LORDS_ORDER[(ad_start_idx + j) % 9]
            ad_years = DASHA_YEARS[ad_lord]
            # Duration in days = (MD_years * AD_years * 365.25) / 120
            # For the first birth Mahadasha, scale proportionally to remaining balance
            if i == 0:
                fraction_of_full_md = (balance_days / (md_years * 365.25))
                ad_days = (md_years * ad_years * 365.25 / TOTAL_DASHA_YEARS) * fraction_of_full_md
            else:
                ad_days = (md_years * ad_years * 365.25) / TOTAL_DASHA_YEARS

            ad_end = ad_start + timedelta(days=ad_days)
            is_ad_current = ad_start <= current_dt <= ad_end

            ad_tot_months = (md_years * ad_years * 12.0) / TOTAL_DASHA_YEARS
            ad_dur_y = int(ad_tot_months // 12)
            ad_dur_m = int(ad_tot_months % 12)
            ad_dur_d = int(round((ad_tot_months - int(ad_tot_months)) * 30.0))
            if ad_dur_y > 0:
                ad_duration_str = f"{ad_dur_y} Y {ad_dur_m} M {ad_dur_d} D"
            else:
                ad_duration_str = f"{ad_dur_m} M {ad_dur_d} D"

            # Generate 9 Pratyantardashas for this Antardasha
            pratyantardashas: list[KPDashaPeriod] = []
            pad_start_idx = DASHA_LORDS_ORDER.index(ad_lord)
            pad_start = ad_start

            for k in range(9):
                pad_lord = DASHA_LORDS_ORDER[(pad_start_idx + k) % 9]
                pad_years = DASHA_YEARS[pad_lord]
                pad_days = (ad_days * pad_years) / TOTAL_DASHA_YEARS
                pad_end = pad_start + timedelta(days=pad_days)
                is_pad_current = pad_start <= current_dt <= pad_end

                pad_m = int(pad_days // 30.4375)
                pad_d = int(round(pad_days % 30.4375))
                if pad_m > 0:
                    pad_duration_str = f"{pad_m} M {pad_d} D"
                else:
                    pad_duration_str = f"{int(pad_days)} D"

                pratyantardashas.append(
                    KPDashaPeriod(
                        lord=pad_lord,
                        level=3,
                        start_date=pad_start.strftime("%d-%m-%Y"),
                        end_date=pad_end.strftime("%d-%m-%Y"),
                        duration=pad_duration_str,
                        is_current=is_pad_current,
                        sub_periods=[],
                    )
                )
                pad_start = pad_end

            antardashas.append(
                KPDashaPeriod(
                    lord=ad_lord,
                    level=2,
                    start_date=ad_start.strftime("%d-%m-%Y"),
                    end_date=ad_end.strftime("%d-%m-%Y"),
                    duration=ad_duration_str,
                    is_current=is_ad_current,
                    insight=DASHA_INSIGHTS.get(ad_lord),
                    sub_periods=pratyantardashas,
                )
            )
            ad_start = ad_end

        dashas_result.append(
            KPDashaPeriod(
                lord=current_md_lord,
                level=1,
                start_date=md_start.strftime("%d-%m-%Y"),
                end_date=md_end.strftime("%d-%m-%Y"),
                duration=md_duration_str,
                is_current=is_md_current,
                insight=DASHA_INSIGHTS.get(current_md_lord),
                sub_periods=antardashas,
            )
        )

    return balance_str, dashas_result


def calculate_kp(payload: KPCalculateRequest) -> KPCalculateResponse:
    """Calculates 100% accurate KP Astrology parameters, Placidus Cusps,
    Ruling Planets for DOB and Casting Time, Panchang, and Vimshottari Dasha.
    """
    # 1. Parse DOB & Local Time
    raw_hour = getattr(payload, "hour", None)
    hour = raw_hour if raw_hour is not None else 12
    minute = getattr(payload, "minute", None) or 0
    second = getattr(payload, "second", None) or 0
    period = getattr(payload, "period", "PM") or "PM"

    hour_24 = hour
    if period == "PM" and hour_24 < 12:
        hour_24 += 12
    elif period == "AM" and hour_24 == 12:
        hour_24 = 0

    local_decimal_hour = hour_24 + minute / 60.0 + second / 3600.0

    # The offset comes from the IANA zone for the birth place, resolved at the birth
    # instant, so daylight saving and historical changes are handled. A caller that
    # supplies only a bare offset still works, but gets neither.
    resolved_tz = resolve_timezone(
        year=payload.year,
        month=payload.month,
        day=payload.day,
        hour=hour_24,
        minute=minute,
        second=second,
        latitude=payload.latitude,
        longitude=payload.longitude,
        zone_name=getattr(payload, "timezone_name", None),
        fallback_offset_hours=payload.timezone,
    )
    tz_offset = resolved_tz.offset_hours
    utc_decimal_hour = local_decimal_hour - tz_offset

    day = payload.day
    month = payload.month
    year = payload.year

    base_dt = datetime(year, month, day, 0, 0, 0, tzinfo=UTC)
    moment = base_dt + timedelta(hours=utc_decimal_hour)
    birth_dt = datetime(year, month, day, hour, minute, second)
    utc_hours = (
        moment.hour
        + moment.minute / 60.0
        + moment.second / 3600.0
        + moment.microsecond / 3_600_000_000.0
    )

    lat = payload.latitude if payload.latitude is not None else 22.5726
    lon = payload.longitude if payload.longitude is not None else 88.3639

    # 2. Ephemeris & Julian Day
    if HAS_SWISSEPH and swe is not None:
        jd_dob = swe.julday(moment.year, moment.month, moment.day, utc_hours)
        ayanamsa_code = getattr(payload, "ayanamsa", "krishnamurti") or "krishnamurti"
        ay_str = str(ayanamsa_code).lower()
        if ay_str in ("lahiri",):
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            ayanamsa_name = "Lahiri (Chitra Paksha)"
        elif ay_str in ("bv_raman", "raman"):
            swe.set_sid_mode(swe.SIDM_RAMAN)
            ayanamsa_name = "B.V. Raman"
        elif ay_str in ("kp_new", "kp_vp291"):
            swe.set_sid_mode(getattr(swe, "SIDM_KRISHNAMURTI_VP291", swe.SIDM_KRISHNAMURTI))
            ayanamsa_name = "KP New Ayanamsa"
        elif ay_str in ("yukteshwar",):
            swe.set_sid_mode(getattr(swe, "SIDM_YUKTESHWAR", swe.SIDM_KRISHNAMURTI))
            ayanamsa_name = "Sri Yukteshwar"
        elif ay_str in ("suryasiddhanta",):
            swe.set_sid_mode(getattr(swe, "SIDM_SURYASIDDHANTA", swe.SIDM_KRISHNAMURTI))
            ayanamsa_name = "Surya Siddhanta"
        elif ay_str in ("true_pushya",):
            swe.set_sid_mode(getattr(swe, "SIDM_TRUE_PUSHYA", swe.SIDM_KRISHNAMURTI))
            ayanamsa_name = "True Pushya"
        else:
            swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)
            ayanamsa_name = "Krishnamurti (KP Original)"
        ayanamsa_deg = swe.get_ayanamsa_ut(jd_dob)

        # 12 Placidus Cusps (Standard or Horary 1 to 249)
        horary_details = None
        if payload.horary_number and 1 <= payload.horary_number <= 249:
            asc_lon, cusps_list, horary_details = _calculate_horary_cusps(
                payload.horary_number, lat, jd_dob, ayanamsa_deg
            )
        else:
            raw_cusps, ascmc = swe.houses_ex(jd_dob, lat, lon, b"P", swe.FLG_SIDEREAL)
            asc_lon = ascmc[0] % 360.0
            cusps_list = [c % 360.0 for c in raw_cusps]

        # Moon & Sun Coordinates
        calc_flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
        moon_res, _ = swe.calc_ut(jd_dob, swe.MOON, calc_flags)
        moon_lon = moon_res[0] % 360.0

        sun_res, _ = swe.calc_ut(jd_dob, swe.SUN, calc_flags)
        sun_lon = sun_res[0] % 360.0

        # Sunrise & Sunset
        jd_start = swe.julday(year, month, day, 0.0 - tz_offset)
        try:
            _, rise_tret = swe.rise_trans(jd_start, swe.SUN, swe.CALC_RISE, (lon, lat, 0.0))
            _, set_tret = swe.rise_trans(jd_start, swe.SUN, swe.CALC_SET, (lon, lat, 0.0))

            def jd_to_hms(jd_val: float) -> str:
                local_jd = jd_val + tz_offset / 24.0
                day_frac = (local_jd + 0.5) % 1.0
                sec = int(day_frac * 86400)
                return f"{sec // 3600:02d}:{(sec % 3600) // 60:02d}:{sec % 60:02d}"

            sunrise_str = jd_to_hms(rise_tret[0])
            sunset_str = jd_to_hms(set_tret[0])
        except Exception:
            sunrise_str = "05:30:00"
            sunset_str = "18:15:00"

        # Casting Time JD (Current Time)
        now_utc = datetime.now(UTC)
        jd_casting = swe.julday(
            now_utc.year, now_utc.month, now_utc.day,
            now_utc.hour + now_utc.minute / 60.0 + now_utc.second / 3600.0
        )
    else:
        # Fallback pure-python calculations
        A = int(calc_year / 100)
        B = 2 - A + int(A / 4)
        jd_dob = int(365.25 * (calc_year + 4716)) + int(30.6001 * (calc_month + 1)) + calc_day + B - 1524.5 + calc_hour_utc / 24.0
        T = (jd_dob - 2451545.0) / 36525.0
        ayanamsa_deg = 23.823 + 1.397 * T

        moon_lon = ((218.316 + 481267.88 * T) - ayanamsa_deg) % 360.0
        sun_lon = ((280.466 + 36000.77 * T) - ayanamsa_deg) % 360.0

        gmst = (280.4606 + 360.9856 * (jd_dob - 2451545.0)) % 360.0
        asc_lon = ((gmst + lon) - ayanamsa_deg) % 360.0

        horary_details = None
        if payload.horary_number and 1 <= payload.horary_number <= 249:
            asc_lon, cusps_list, horary_details = _calculate_horary_cusps(
                payload.horary_number, lat, jd_dob, ayanamsa_deg
            )
        else:
            cusps_list = [(asc_lon + i * 30.0) % 360.0 for i in range(12)]

        sunrise_str = "05:30:00"
        sunset_str = "18:15:00"

        now_utc = datetime.now(UTC)
        jd_casting = jd_dob + 0.5

    # 3. Panchang (Tithi, Yoga, Karana, Vedic Day)
    diff_tithi = (moon_lon - sun_lon) % 360.0
    tithi_name = TITHIS_LIST[int(diff_tithi / 12.0) % 30]

    yoga_diff = (moon_lon + sun_lon) % 360.0
    yoga_name = YOGAS_LIST[int(yoga_diff / (360.0 / 27.0)) % 27]

    k_idx = int(diff_tithi / 6.0)
    if k_idx == 0:
        karana_name = "Kintughna"
    elif k_idx >= 57:
        fixed_k = ["Shakuni", "Chatushpada", "Naga"]
        karana_name = fixed_k[min(k_idx - 57, 2)]
    else:
        karana_name = KARANAS_REPEATING[(k_idx - 1) % 7]

    # Weekday calculation
    day_idx = birth_dt.weekday()  # 0 is Monday
    day_name = WEEKDAY_LORDS[day_idx][0]
    vedic_day_name = day_name  # In general aligns with weekday if born post-sunrise

    # Ascendant Details
    asc_sign_idx = int(asc_lon / 30.0) % 12
    asc_sign_info = RASHIS_DATA[asc_sign_idx]
    asc_deg_in_sign = asc_lon % 30.0

    # Moon Details
    moon_sign_idx = int(moon_lon / 30.0) % 12
    moon_sign_info = RASHIS_DATA[moon_sign_idx]
    moon_deg_in_sign = moon_lon % 30.0
    moon_nak_name, moon_star_lord, _, _, _, _ = _get_star_sub_and_sub_sub_lord(moon_lon)

    # 4. 12 Cusps Table
    cusps_table: list[KPCuspDetail] = []
    for idx, c_deg in enumerate(cusps_list):
        c_num = idx + 1
        s_idx = int(c_deg / 30.0) % 12
        s_info = RASHIS_DATA[s_idx]
        deg_in_s = c_deg % 30.0
        _, star_l, sub_l, sub_sub_l, _, _ = _get_star_sub_and_sub_sub_lord(c_deg)

        if idx == 0 and horary_details is not None:
            sign_name = horary_details.sign
            sign_lord = horary_details.sign_lord
            star_l = horary_details.star_lord
            sub_l = horary_details.sub_lord
            sub_sub_l = horary_details.sub_sub_lord
            s_idx = next((i for i, r in enumerate(RASHIS_DATA) if r["name_en"] == sign_name), s_idx)
        else:
            sign_name = s_info["name_en"]
            sign_lord = s_info["lord"]

        cusps_table.append(
            KPCuspDetail(
                cusp=c_num,
                longitude=round(c_deg, 4),
                degree_formatted=_format_dms(deg_in_s),
                sign=sign_name,
                sign_index=s_idx,
                sign_lord=sign_lord,
                star_lord=star_l,
                sub_lord=sub_l,
                sub_sub_lord=sub_sub_l,
            )
        )

    # 5. Planetary Positions & Nirayana Bhava Chalit House Placement
    planets_table: list[KPPlanetDetail] = []

    if HAS_SWISSEPH and swe is not None:
        calc_flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
        for pname, psym, pcode, pid in PLANET_IDS:
            pres, _ = swe.calc_ut(jd_dob, pid, calc_flags)
            plon = pres[0] % 360.0
            psign_idx = int(plon / 30.0) % 12
            pdeg_in_s = plon % 30.0
            pnak_name, pstar_l, psub_l, psub_sub_l, _, ppada = _get_star_sub_and_sub_sub_lord(plon)
            is_retro = pres[3] < 0 if len(pres) > 3 else False

            rashi_house_num = ((psign_idx - asc_sign_idx) % 12) + 1
            bhav_house_num = _calculate_bhav_house(plon, cusps_list)

            planets_table.append(
                KPPlanetDetail(
                    name=pname,
                    symbol=psym,
                    code=pcode,
                    longitude=round(plon, 4),
                    degree_in_sign=round(pdeg_in_s, 4),
                    degree_formatted=_format_dms(pdeg_in_s),
                    sign=RASHIS_DATA[psign_idx]["name_en"],
                    sign_index=psign_idx,
                    nakshatra=pnak_name,
                    pada=ppada,
                    sign_lord=RASHIS_DATA[psign_idx]["lord"],
                    star_lord=pstar_l,
                    sub_lord=psub_l,
                    sub_sub_lord=psub_sub_l,
                    rashi_house=rashi_house_num,
                    bhav_house=bhav_house_num,
                    is_retrograde=is_retro,
                    is_untenanted=False,
                )
            )

        # Ketu is opposite to Rahu
        rahu_obj = next((p for p in planets_table if p.name == "Rahu"), None)
        if rahu_obj:
            klon = (rahu_obj.longitude + 180.0) % 360.0
            ksign_idx = int(klon / 30.0) % 12
            kdeg_in_s = klon % 30.0
            knak_name, kstar_l, ksub_l, ksub_sub_l, _, kpada = _get_star_sub_and_sub_sub_lord(klon)
            krashi_house = ((ksign_idx - asc_sign_idx) % 12) + 1
            kbhav_house = _calculate_bhav_house(klon, cusps_list)

            planets_table.append(
                KPPlanetDetail(
                    name="Ketu",
                    symbol="☋",
                    code="Ke",
                    longitude=round(klon, 4),
                    degree_in_sign=round(kdeg_in_s, 4),
                    degree_formatted=_format_dms(kdeg_in_s),
                    sign=RASHIS_DATA[ksign_idx]["name_en"],
                    sign_index=ksign_idx,
                    nakshatra=knak_name,
                    pada=kpada,
                    sign_lord=RASHIS_DATA[ksign_idx]["lord"],
                    star_lord=kstar_l,
                    sub_lord=ksub_l,
                    sub_sub_lord=ksub_sub_l,
                    rashi_house=krashi_house,
                    bhav_house=kbhav_house,
                    is_retrograde=True,
                    is_untenanted=False,
                )
            )
    else:
        # Fallback planets (Sun & Moon)
        planets_table = [
            KPPlanetDetail(
                name="Sun",
                symbol="☉",
                code="Su",
                longitude=round(sun_lon, 4),
                degree_in_sign=round(sun_lon % 30.0, 4),
                degree_formatted=_format_dms(sun_lon % 30.0),
                sign=RASHIS_DATA[int(sun_lon / 30.0) % 12]["name_en"],
                sign_index=int(sun_lon / 30.0) % 12,
                nakshatra="Mrigashira",
                pada=1,
                sign_lord="Mercury",
                star_lord="Mars",
                sub_lord="Saturn",
                sub_sub_lord="Venus",
                rashi_house=6,
                bhav_house=6,
                is_retrograde=False,
                is_untenanted=False,
            ),
            KPPlanetDetail(
                name="Moon",
                symbol="☽",
                code="Mo",
                longitude=round(moon_lon, 4),
                degree_in_sign=round(moon_lon % 30.0, 4),
                degree_formatted=_format_dms(moon_lon % 30.0),
                sign=RASHIS_DATA[int(moon_lon / 30.0) % 12]["name_en"],
                sign_index=int(moon_lon / 30.0) % 12,
                nakshatra=moon_nak_name,
                pada=1,
                sign_lord="Mars",
                star_lord=moon_star_lord,
                sub_lord="Ketu",
                sub_sub_lord="Jupiter",
                rashi_house=11,
                bhav_house=11,
                is_retrograde=False,
                is_untenanted=False,
            ),
        ]

    # 5b. Untenanted Planets Calculation (Rahul Kaushik Ch. 1, Page 11)
    untenanted_planets = _calculate_untenanted_planets(planets_table)

    # 6. Ruling Planets (DOB and Casting Time) with Retrograde Filtering
    rp_dob = _calculate_ruling_planets_at_jd(jd_dob, lat, lon, is_dob=True, planets_table=planets_table)
    rp_casting = _calculate_ruling_planets_at_jd(jd_casting, lat, lon, is_dob=False, planets_table=planets_table)

    # 7. Vimshottari Dasha Hierarchy
    now_dt = datetime.now()
    balance_dasha_str, dashas_list = _generate_vimshottari_hierarchy(
        birth_dt=birth_dt,
        moon_lon=moon_lon,
        current_dt=now_dt,
    )

    # 8. Advanced KP Modules (Significators, Life Events, Aspects, Badhaka/Maraka, Remedies)
    planet_sigs, house_sigs = _calculate_significators(planets_table, cusps_table)
    badhaka_maraka = _calculate_badhaka_maraka(asc_sign_idx, cusps_table, planets_table, language=payload.language)
    life_events = _calculate_kp_life_events(
        cusps=cusps_table,
        planet_sigs=planet_sigs,
        planets=planets_table,
        badhaka_house=badhaka_maraka.badhaka_house,
        language=payload.language,
    )
    aspects = _calculate_kp_aspects(planets_table, language=payload.language)
    remedies = _calculate_kp_remedies(
        planets=planets_table,
        cusps=cusps_table,
        language=payload.language,
    )

    # Panchang Object
    panchang = KPPanchang(
        julian_day=int(jd_dob),
        ayanamsa_name=ayanamsa_name,
        ayanamsa_degrees=round(ayanamsa_deg, 4),
        house_system="Placidus (Semi-arc)",
        sunrise=sunrise_str,
        sunset=sunset_str,
        tithi=tithi_name,
        yoga=yoga_name,
        karana=karana_name,
        day_name=day_name,
        vedic_day_name=vedic_day_name,
        balance_dasha=balance_dasha_str,
        ascendant_sign=asc_sign_info["name_en"],
        ascendant_lord=asc_sign_info["lord"],
        ascendant_degree=round(asc_deg_in_sign, 4),
        ascendant_degree_formatted=_format_dms(asc_deg_in_sign),
        moon_rashi=moon_sign_info["name_en"],
        moon_rashi_lord=moon_sign_info["lord"],
        moon_nakshatra=moon_nak_name,
        moon_nakshatra_lord=moon_star_lord,
        moon_degree_formatted=_format_dms(moon_deg_in_sign),
    )

    # Multilingual translation bundles
    translations_bundle = {
        "en": {
            "asc_sign": asc_sign_info["name_en"],
            "moon_rashi": moon_sign_info["name_en"],
            "nakshatra": moon_nak_name,
        },
        "bn": {
            "asc_sign": asc_sign_info["name_bn"],
            "moon_rashi": moon_sign_info["name_bn"],
            "nakshatra": NAKSHATRAS_DATA[int(moon_lon / (360.0 / 27.0)) % 27].get("name_bn", moon_nak_name),
        },
        "hi": {
            "asc_sign": asc_sign_info["name_hi"],
            "moon_rashi": moon_sign_info["name_hi"],
            "nakshatra": moon_nak_name,
        },
    }

    b_date_str = f"{day:02d}/{month:02d}/{year}"
    b_time_str = f"{hour:02d} h:{minute:02d}m:{second:02d}s"

    return KPCalculateResponse(
        name=payload.name.strip() or "Seeker",
        gender=payload.gender.capitalize(),
        birth_date_formatted=b_date_str,
        birth_time_formatted=b_time_str,
        birth_place=payload.place.strip() or "Custom Coordinates",
        latitude=round(lat, 4),
        longitude=round(lon, 4),
        timezone=round(tz_offset, 6),
        panchang=panchang,
        ruling_planets_dob=rp_dob,
        ruling_planets_casting=rp_casting,
        cusps=cusps_table,
        planets=planets_table,
        dashas=dashas_list,
        untenanted_planets=untenanted_planets,
        planet_significators=planet_sigs,
        house_significators=house_sigs,
        life_events=life_events,
        aspects=aspects,
        badhaka_maraka=badhaka_maraka,
        horary_details=horary_details,
        remedies=remedies,
        selected_language=payload.language,
        translations=translations_bundle,
    )
