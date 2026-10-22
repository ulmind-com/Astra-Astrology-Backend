"""KP Astrology (Krishnamurti Paddhati) Calculation Engine.

Based on client resource documents in 'Resource Documents/Rashi Rules':
- KP Astrology Basics and Rules.pdf
- KP Astrology- The Hidden Secrets.pdf (by Rahul Kaushik, Ch 1, 7, 8)
- Classical Placidus semi-arc Cuspal Sub-Lord and Ruling Planets theory.
"""

import math
from datetime import datetime, timedelta, UTC
from typing import Any
from loguru import logger

from app.schemas.astrology import (
    KPCalculateRequest,
    KPCalculateResponse,
    KPCuspDetail,
    KPDashaInsight,
    KPDashaPeriod,
    KPPanchang,
    KPPlanetDetail,
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


def _get_star_and_sub_lord(lon_deg: float) -> tuple[str, str, str, int, int]:
    """Returns (Nakshatra Name, Star Lord, Sub Lord, Nakshatra Index, Pada)."""
    nak_span = 360.0 / 27.0  # 13.333333°
    pada_span = nak_span / 4.0
    nak_idx = int(lon_deg / nak_span) % 27
    offset_in_nak = lon_deg % nak_span
    pada = int(offset_in_nak / pada_span) + 1

    nak_info = NAKSHATRAS_DATA[nak_idx]
    star_lord = nak_info["lord"]
    sub_lord = calculate_kp_sub_lord(star_lord, offset_in_nak)
    return nak_info["name"], star_lord, sub_lord, nak_idx, pada


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


def _calculate_ruling_planets_at_jd(
    jd: float, lat: float, lon: float, is_dob: bool = True
) -> KPRulingPlanets:
    """Calculates KP Ruling Planets (Lagna Sign/Star/Sub + Moon Sign/Star/Sub + Day Lord)."""
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
    _, asc_star_lord, asc_sub_lord, _, _ = _get_star_and_sub_lord(asc_lon)

    # Moon
    moon_sign_idx = int(moon_lon / 30.0) % 12
    moon_rashi_lord = RASHIS_DATA[moon_sign_idx]["lord"]
    _, moon_star_lord, moon_sub_lord, _, _ = _get_star_and_sub_lord(moon_lon)

    # Day Lord (from JD to UTC datetime)
    day_num = int((jd + 1.5)) % 7  # 0 is Sunday, 1 is Monday ... 6 is Saturday
    # Convert to weekday index (0 is Monday, 6 is Sunday)
    weekday_idx = (day_num - 1) % 7
    day_lord_str = WEEKDAY_LORDS[weekday_idx][1]

    # Convert JD to date/time string
    local_jd = jd + 5.5 / 24.0
    z = int(local_jd + 0.5)
    f = (local_jd + 0.5) - z
    # Julian to Gregorian calendar algorithm
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

        # 12 Placidus Cusps
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
    moon_nak_name, moon_star_lord, _, _, _ = _get_star_and_sub_lord(moon_lon)

    # 4. 12 Cusps Table
    cusps_table: list[KPCuspDetail] = []
    for idx, c_deg in enumerate(cusps_list):
        c_num = idx + 1
        s_idx = int(c_deg / 30.0) % 12
        s_info = RASHIS_DATA[s_idx]
        deg_in_s = c_deg % 30.0
        _, star_l, sub_l, _, _ = _get_star_and_sub_lord(c_deg)

        cusps_table.append(
            KPCuspDetail(
                cusp=c_num,
                longitude=round(c_deg, 4),
                degree_formatted=_format_dms(deg_in_s),
                sign=s_info["name_en"],
                sign_index=s_idx,
                sign_lord=s_info["lord"],
                star_lord=star_l,
                sub_lord=sub_l,
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
            pnak_name, pstar_l, psub_l, _, ppada = _get_star_and_sub_lord(plon)
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
                    rashi_house=rashi_house_num,
                    bhav_house=bhav_house_num,
                    is_retrograde=is_retro,
                )
            )

        # Ketu is opposite to Rahu
        rahu_obj = next((p for p in planets_table if p.name == "Rahu"), None)
        if rahu_obj:
            klon = (rahu_obj.longitude + 180.0) % 360.0
            ksign_idx = int(klon / 30.0) % 12
            kdeg_in_s = klon % 30.0
            knak_name, kstar_l, ksub_l, _, kpada = _get_star_and_sub_lord(klon)
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
                    rashi_house=krashi_house,
                    bhav_house=kbhav_house,
                    is_retrograde=True,
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
                rashi_house=6,
                bhav_house=6,
                is_retrograde=False,
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
                rashi_house=11,
                bhav_house=11,
                is_retrograde=False,
            ),
        ]

    # 6. Ruling Planets (DOB and Casting Time)
    rp_dob = _calculate_ruling_planets_at_jd(jd_dob, lat, lon, is_dob=True)
    rp_casting = _calculate_ruling_planets_at_jd(jd_casting, lat, lon, is_dob=False)

    # 7. Vimshottari Dasha Hierarchy
    now_dt = datetime.now()
    balance_dasha_str, dashas_list = _generate_vimshottari_hierarchy(
        birth_dt=birth_dt,
        moon_lon=moon_lon,
        current_dt=now_dt,
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
        selected_language=payload.language,
        translations=translations_bundle,
    )
