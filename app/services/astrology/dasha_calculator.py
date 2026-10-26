"""Advanced Dasha Calculation Engine.

Based on client resource documents:
- Rahul Pandat PDFs/Kusthi Rules/matching-pdf-english.pdf (4-level Vimshottari Dasha with exact timestamps)
- Astrology Data and API Solutions - Google Gemini.pdf (self-hosted pyswisseph, exact Moon degrees)
- Basics of Kundali Reading Explained.pdf (Functional benefic/malefic, Yogakaraka, Maraka, house placements)
- Rahul Kaushik - KP Astrology: The Hidden Secrets.pdf (Ch. 9 remedies, Dasha balance & Sub-lord interactions)

Provides:
1. True Pre-natal Inception Vimshottari hierarchy (eliminating Antardasha compression bug)
2. 5-Tier Vimshottari micro-timing (Mahadasha, Antar, Pratyantar, Sookshma, Pran Dasha down to exact minute)
3. Current running Dasha snapshot with live remaining days and countdown metrics
4. Dasha Sandhi & Chidra Dasha warning detector
5. Personalized Kundli-Aware Dasha Phala (Lagna-specific Yogakaraka, Maraka, house placement, dignity)
6. Yogini Dasha (36-year cycle, 8 Yoginis from Janma Nakshatra with Antar-Yogini breakdown)
7. Live Dasha-Gochar (Transit Overlay) synergy engine with Saturn's Sade Sati phase detection
8. Interactive Life Timeline Bar segments from birth to 100+ years
"""

import math
from datetime import datetime, timedelta, UTC
from typing import Any
from loguru import logger

from app.schemas.astrology import (
    CurrentRunningDashaInfo,
    DashaSandhiChidraInfo,
    DashaTimelineSegment,
    DashaTransitSynergy,
    KPCalculateRequest,
    KPCalculateResponse,
    KPDashaPeriod,
    PersonalizedDashaPhalaItem,
    YoginiDashaSystem,
    YoginiPeriodItem,
)
from app.services.astrology.kp_calculator import (
    DASHA_INSIGHTS,
    DASHA_LORDS_ORDER,
    DASHA_YEARS,
    NAKSHATRAS_DATA,
    RASHIS_DATA,
    TOTAL_DASHA_YEARS,
    calculate_kp,
)

# Swiss Ephemeris for real-time transit calculation
try:
    import swisseph as swe
    HAS_SWISSEPH = True
except (ImportError, Exception) as exc:
    swe = None  # type: ignore
    HAS_SWISSEPH = False
    logger.warning(f"Swiss Ephemeris not available in dasha_calculator: {exc}")

# Yogini Dasha definitions (36-year cycle)
YOGINI_NAMES = [
    "Mangala", "Pingala", "Dhanya", "Bhramari",
    "Bhadrika", "Ulka", "Siddha", "Sankata",
]
YOGINI_YEARS = {
    "Mangala": 1,
    "Pingala": 2,
    "Dhanya": 3,
    "Bhramari": 4,
    "Bhadrika": 5,
    "Ulka": 6,
    "Siddha": 7,
    "Sankata": 8,
}
YOGINI_RULERS = {
    "Mangala": "Moon",
    "Pingala": "Sun",
    "Dhanya": "Jupiter",
    "Bhramari": "Mars",
    "Bhadrika": "Mercury",
    "Ulka": "Saturn",
    "Siddha": "Venus",
    "Sankata": "Rahu",
}
YOGINI_NATURES = {
    "Mangala": "Benefic",
    "Pingala": "Neutral",
    "Dhanya": "Benefic",
    "Bhramari": "Challenging",
    "Bhadrika": "Benefic",
    "Ulka": "Challenging",
    "Siddha": "Benefic",
    "Sankata": "Challenging",
}
TOTAL_YOGINI_YEARS = 36

# Classical Planetary Dignity Signs
EXALTATION_SIGNS = {
    "Sun": 0,       # Aries
    "Moon": 1,      # Taurus
    "Mars": 9,      # Capricorn
    "Mercury": 5,   # Virgo
    "Jupiter": 3,   # Cancer
    "Venus": 11,    # Pisces
    "Saturn": 6,    # Libra
    "Rahu": 2,      # Gemini / Taurus
    "Ketu": 8,      # Sagittarius / Scorpio
}
DEBILITATION_SIGNS = {
    "Sun": 6,       # Libra
    "Moon": 7,      # Scorpio
    "Mars": 3,      # Cancer
    "Mercury": 11,  # Pisces
    "Jupiter": 9,   # Capricorn
    "Venus": 5,     # Virgo
    "Saturn": 0,    # Aries
    "Rahu": 8,      # Sagittarius
    "Ketu": 2,      # Gemini
}
OWN_SIGNS = {
    "Sun": [4],             # Leo
    "Moon": [3],            # Cancer
    "Mars": [0, 7],         # Aries, Scorpio
    "Mercury": [2, 5],      # Gemini, Virgo
    "Jupiter": [8, 11],     # Sagittarius, Pisces
    "Venus": [1, 6],        # Taurus, Libra
    "Saturn": [9, 10],      # Capricorn, Aquarius
    "Rahu": [10],           # Co-rules Aquarius
    "Ketu": [7],            # Co-rules Scorpio
}

# Lagna Functional Nature Matrix based on Parashara Hora Shastra & Basics of Kundali Reading Explained
LAGNA_FUNCTIONAL_RULES: dict[int, dict[str, str]] = {
    # 0: Aries
    0: {
        "Mars": "Functional Benefic (Lagna Lord)",
        "Sun": "Functional Benefic (5th Lord - Trikona)",
        "Jupiter": "Functional Benefic (9th Lord - Bhagyadhipati)",
        "Moon": "Neutral (4th Lord)",
        "Venus": "Maraka (2nd & 7th Lord)",
        "Mercury": "Functional Malefic (3rd & 6th Lord)",
        "Saturn": "Badhaka & Upachaya (10th & 11th Lord)",
        "Rahu": "Functional Malefic",
        "Ketu": "Neutral / Mokshakaraka",
    },
    # 1: Taurus
    1: {
        "Saturn": "Yogakaraka (9th & 10th Lord - Supreme Kendra/Trikona)",
        "Mercury": "Functional Benefic (2nd & 5th Lord)",
        "Venus": "Functional Benefic (Lagna & 6th Lord)",
        "Sun": "Neutral (4th Lord)",
        "Moon": "Exalted Friend (3rd Lord)",
        "Mars": "Maraka & Malefic (7th & 12th Lord)",
        "Jupiter": "Functional Malefic (8th & 11th Lord)",
        "Rahu": "Functional Benefic (Exalted friend of Venus)",
        "Ketu": "Functional Malefic",
    },
    # 2: Gemini
    2: {
        "Mercury": "Functional Benefic (Lagna & 4th Lord)",
        "Venus": "Functional Benefic (5th & 12th Lord)",
        "Saturn": "Functional Benefic (8th & 9th Lord - Bhagyadhipati)",
        "Sun": "Neutral (3rd Lord)",
        "Moon": "Maraka (2nd Lord)",
        "Jupiter": "Maraka & Kendradhipati Dosha (7th & 10th Lord)",
        "Mars": "Functional Malefic (6th & 11th Lord)",
        "Rahu": "Functional Benefic (Exalted)",
        "Ketu": "Functional Malefic (Debilitated)",
    },
    # 3: Cancer
    3: {
        "Mars": "Yogakaraka (5th & 10th Lord - Supreme Benefic)",
        "Moon": "Functional Benefic (Lagna Lord)",
        "Jupiter": "Functional Benefic (6th & 9th Lord - Bhagyadhipati)",
        "Sun": "Neutral Benefic (2nd Lord)",
        "Saturn": "Maraka & Dusthana (7th & 8th Lord)",
        "Mercury": "Functional Malefic (3rd & 12th Lord)",
        "Venus": "Badhaka & Malefic (4th & 11th Lord)",
        "Rahu": "Functional Malefic",
        "Ketu": "Neutral",
    },
    # 4: Leo
    4: {
        "Mars": "Yogakaraka (4th & 9th Lord - Supreme Benefic)",
        "Sun": "Functional Benefic (Lagna Lord)",
        "Jupiter": "Functional Benefic (5th & 8th Lord)",
        "Moon": "Neutral (12th Lord)",
        "Mercury": "Neutral (2nd & 11th Lord)",
        "Venus": "Functional Malefic (3rd & 10th Lord)",
        "Saturn": "Maraka & Malefic (6th & 7th Lord)",
        "Rahu": "Functional Malefic",
        "Ketu": "Neutral",
    },
    # 5: Virgo
    5: {
        "Mercury": "Functional Benefic (Lagna & 10th Lord)",
        "Venus": "Functional Benefic (2nd & 9th Lord - Bhagyadhipati)",
        "Saturn": "Functional Benefic (5th & 6th Lord)",
        "Sun": "Neutral (12th Lord)",
        "Moon": "Neutral (11th Lord)",
        "Jupiter": "Maraka & Kendradhipati Dosha (4th & 7th Lord)",
        "Mars": "Functional Malefic (3rd & 8th Lord)",
        "Rahu": "Functional Benefic",
        "Ketu": "Functional Malefic",
    },
    # 6: Libra
    6: {
        "Saturn": "Yogakaraka (4th & 5th Lord - Supreme Benefic)",
        "Mercury": "Functional Benefic (9th & 12th Lord - Bhagyadhipati)",
        "Venus": "Functional Benefic (Lagna & 8th Lord)",
        "Moon": "Functional Benefic (10th Lord)",
        "Sun": "Badhaka (11th Lord)",
        "Mars": "Maraka (2nd & 7th Lord)",
        "Jupiter": "Functional Malefic (3rd & 6th Lord)",
        "Rahu": "Functional Benefic",
        "Ketu": "Functional Malefic",
    },
    # 7: Scorpio
    7: {
        "Jupiter": "Functional Benefic (2nd & 5th Lord)",
        "Moon": "Functional Benefic (9th Lord - Bhagyadhipati)",
        "Mars": "Functional Benefic (Lagna & 6th Lord)",
        "Sun": "Functional Benefic (10th Lord - Karma)",
        "Venus": "Maraka (7th & 12th Lord)",
        "Saturn": "Neutral / Malefic (3rd & 4th Lord)",
        "Mercury": "Functional Malefic (8th & 11th Lord)",
        "Rahu": "Functional Malefic",
        "Ketu": "Functional Benefic (Exalted co-ruler)",
    },
    # 8: Sagittarius
    8: {
        "Jupiter": "Functional Benefic (Lagna & 4th Lord)",
        "Sun": "Functional Benefic (9th Lord - Bhagyadhipati)",
        "Mars": "Functional Benefic (5th & 12th Lord)",
        "Moon": "Neutral (8th Lord)",
        "Mercury": "Maraka & Kendradhipati (7th & 10th Lord)",
        "Saturn": "Maraka (2nd & 3rd Lord)",
        "Venus": "Functional Malefic (6th & 11th Lord)",
        "Rahu": "Functional Malefic",
        "Ketu": "Functional Benefic (Exalted)",
    },
    # 9: Capricorn
    9: {
        "Venus": "Yogakaraka (5th & 10th Lord - Supreme Benefic)",
        "Mercury": "Functional Benefic (6th & 9th Lord - Bhagyadhipati)",
        "Saturn": "Functional Benefic (Lagna & 2nd Lord)",
        "Sun": "Neutral (8th Lord)",
        "Moon": "Maraka (7th Lord)",
        "Mars": "Badhaka (4th & 11th Lord)",
        "Jupiter": "Functional Malefic (3rd & 12th Lord)",
        "Rahu": "Functional Benefic",
        "Ketu": "Neutral",
    },
    # 10: Aquarius
    10: {
        "Venus": "Yogakaraka (4th & 9th Lord - Supreme Benefic)",
        "Saturn": "Functional Benefic (Lagna & 12th Lord)",
        "Mercury": "Functional Benefic (5th & 8th Lord)",
        "Sun": "Maraka (7th Lord)",
        "Moon": "Functional Malefic (6th Lord)",
        "Mars": "Neutral Malefic (3rd & 10th Lord)",
        "Jupiter": "Maraka & Malefic (2nd & 11th Lord)",
        "Rahu": "Functional Benefic (Co-ruler)",
        "Ketu": "Neutral",
    },
    # 11: Pisces
    11: {
        "Moon": "Functional Benefic (5th Lord - Trikona)",
        "Mars": "Functional Benefic (2nd & 9th Lord - Bhagyadhipati)",
        "Jupiter": "Functional Benefic (Lagna & 10th Lord)",
        "Sun": "Neutral (6th Lord)",
        "Mercury": "Maraka & Kendradhipati (4th & 7th Lord)",
        "Venus": "Functional Malefic (3rd & 8th Lord)",
        "Saturn": "Maraka & Malefic (11th & 12th Lord)",
        "Rahu": "Functional Malefic",
        "Ketu": "Functional Benefic (Exalted)",
    },
}

# Chidra Dasha Specific Alerts (9th and final Antardasha of Mahadasha)
CHIDRA_DASHA_ALERTS = {
    ("Ketu", "Mercury"): "Final phase of Ketu Mahadasha. Transitioning to 20-year Venus period. Mental restlessness, skin sensitivity, and major spiritual closure.",
    ("Venus", "Ketu"): "Final phase of Venus Mahadasha. Moving into Sun Mahadasha. Detachment from luxury, relationship reassessment, and sudden career shifts.",
    ("Sun", "Venus"): "Final phase of Sun Mahadasha. Preparing for 10-year Moon Mahadasha. Ego softening, domestic focus, and health recovery.",
    ("Moon", "Sun"): "Final phase of Moon Mahadasha. Transitioning to Mars Mahadasha. Emotional assertiveness, property matters, and vitality surges.",
    ("Mars", "Rahu"): "Final phase of Mars Mahadasha. Moving into 18-year Rahu Mahadasha. Volatile energy, sudden travel, and career disruption. Extreme care advised.",
    ("Rahu", "Mars"): "Final phase of Rahu Mahadasha. Moving into 16-year Jupiter Mahadasha. Major relief from Rahu turmoil, sudden settlement, and spiritual alignment.",
    ("Jupiter", "Rahu"): "Final phase of Jupiter Mahadasha. Moving into 19-year Saturn Mahadasha. Shifting from expansion to disciplined responsibility. Financial caution required.",
    ("Saturn", "Jupiter"): "Final phase of Saturn Mahadasha. Moving into 17-year Mercury Mahadasha. Resolution of long karma, relief from heavy burdens, and business opportunities.",
    ("Mercury", "Saturn"): "Final phase of Mercury Mahadasha. Moving into Ketu Mahadasha. Career fatigue, nervous strain, and deep desire for solitude and higher knowledge.",
}


def _format_datetime(dt: datetime) -> str:
    return dt.strftime("%d-%m-%Y %H:%M")


def _format_date(dt: datetime) -> str:
    return dt.strftime("%d-%m-%Y")


def _calculate_uncompressed_vimshottari(
    birth_dt: datetime,
    moon_lon: float,
    current_dt: datetime,
) -> tuple[str, list[KPDashaPeriod], CurrentRunningDashaInfo]:
    """Calculates authentic, uncompressed Vimshottari Dasha with theoretical pre-natal inception.
    
    Eliminates the proportional compression flaw and provides Sookshma (Level 4) and Pran (Level 5)
    micro-periods for the running time window.
    """
    nak_span = 360.0 / 27.0
    nak_idx = int(moon_lon / nak_span) % 27
    offset_in_nak = moon_lon % nak_span

    nak_lord = NAKSHATRAS_DATA[nak_idx]["lord"]
    elapsed_fraction = offset_in_nak / nak_span
    rem_fraction = 1.0 - elapsed_fraction
    nak_lord_total_years = DASHA_YEARS[nak_lord]

    # Balance string at birth
    b_y = int(rem_fraction * nak_lord_total_years)
    rem_m_float = (rem_fraction * nak_lord_total_years - b_y) * 12.0
    b_m = int(rem_m_float)
    b_d = int(round((rem_m_float - b_m) * 30.0))
    balance_days = b_y * 365.25 + b_m * 30.4375 + b_d
    balance_str = f"{b_y} Y {b_m} M {b_d} D"

    # Theoretical start of birth Mahadasha before birth moment
    elapsed_days = (elapsed_fraction * nak_lord_total_years) * 365.25
    theoretical_first_md_start = birth_dt - timedelta(days=elapsed_days)

    start_idx = DASHA_LORDS_ORDER.index(nak_lord)
    dashas_result: list[KPDashaPeriod] = []

    # Running tracking
    active_md_period: KPDashaPeriod | None = None
    active_ad_period: KPDashaPeriod | None = None
    active_pd_period: KPDashaPeriod | None = None
    active_sd_period: KPDashaPeriod | None = None
    active_pran_period: KPDashaPeriod | None = None

    running_sookshma_list: list[KPDashaPeriod] = []
    running_pran_list: list[KPDashaPeriod] = []

    md_start = theoretical_first_md_start

    for i in range(9):
        current_md_lord = DASHA_LORDS_ORDER[(start_idx + i) % 9]
        md_years = DASHA_YEARS[current_md_lord]
        md_full_days = md_years * 365.25
        md_end = md_start + timedelta(days=md_full_days)

        # For the birth MD, the native only experiences from birth_dt to md_end
        is_first_md = (i == 0)
        display_md_start = birth_dt if is_first_md else md_start
        is_md_current = display_md_start <= current_dt <= md_end

        md_duration_str = balance_str if is_first_md else f"{md_years} Years"

        # Generate 9 Antardashas with uncompressed classical spans
        antardashas: list[KPDashaPeriod] = []
        ad_start_idx = DASHA_LORDS_ORDER.index(current_md_lord)
        ad_start = md_start

        for j in range(9):
            ad_lord = DASHA_LORDS_ORDER[(ad_start_idx + j) % 9]
            ad_years = DASHA_YEARS[ad_lord]
            ad_days = (md_years * ad_years * 365.25) / TOTAL_DASHA_YEARS
            ad_end = ad_start + timedelta(days=ad_days)

            # Check if this Antardasha happened completely before birth
            if is_first_md and ad_end <= birth_dt:
                ad_start = ad_end
                continue

            # Active start for native
            display_ad_start = birth_dt if (is_first_md and ad_start < birth_dt) else ad_start
            is_ad_current = display_ad_start <= current_dt <= ad_end

            ad_tot_months = (md_years * ad_years * 12.0) / TOTAL_DASHA_YEARS
            ad_dur_y = int(ad_tot_months // 12)
            ad_dur_m = int(ad_tot_months % 12)
            ad_dur_d = int(round((ad_tot_months - int(ad_tot_months)) * 30.0))
            if ad_dur_y > 0:
                ad_duration_str = f"{ad_dur_y} Y {ad_dur_m} M {ad_dur_d} D"
            else:
                ad_duration_str = f"{ad_dur_m} M {ad_dur_d} D"

            # Generate 9 Pratyantardashas
            pratyantardashas: list[KPDashaPeriod] = []
            pad_start_idx = DASHA_LORDS_ORDER.index(ad_lord)
            pad_start = ad_start

            for k in range(9):
                pad_lord = DASHA_LORDS_ORDER[(pad_start_idx + k) % 9]
                pad_years = DASHA_YEARS[pad_lord]
                pad_days = (ad_days * pad_years) / TOTAL_DASHA_YEARS
                pad_end = pad_start + timedelta(days=pad_days)

                if is_first_md and pad_end <= birth_dt:
                    pad_start = pad_end
                    continue

                display_pad_start = birth_dt if (is_first_md and pad_start < birth_dt) else pad_start
                is_pad_current = display_pad_start <= current_dt <= pad_end

                pad_m = int(pad_days // 30.4375)
                pad_d = int(round(pad_days % 30.4375))
                pad_duration_str = f"{pad_m} M {pad_d} D" if pad_m > 0 else f"{int(pad_days)} D"

                pad_period = KPDashaPeriod(
                    lord=pad_lord,
                    level=3,
                    start_date=_format_date(display_pad_start),
                    end_date=_format_date(pad_end),
                    duration=pad_duration_str,
                    is_current=is_pad_current,
                    start_time=display_pad_start.strftime("%H:%M"),
                    end_time=pad_end.strftime("%H:%M"),
                    sub_periods=[],
                )
                pratyantardashas.append(pad_period)

                if is_pad_current:
                    active_pd_period = pad_period

                    # Generate Sookshma Dashas (Level 4) under active Pratyantardasha
                    sookshma_start_idx = DASHA_LORDS_ORDER.index(pad_lord)
                    sookshma_start = display_pad_start
                    for s in range(9):
                        sd_lord = DASHA_LORDS_ORDER[(sookshma_start_idx + s) % 9]
                        sd_years = DASHA_YEARS[sd_lord]
                        sd_days = (pad_days * sd_years) / TOTAL_DASHA_YEARS
                        sd_end = sookshma_start + timedelta(days=sd_days)
                        is_sd_current = sookshma_start <= current_dt <= sd_end

                        sd_hours = int(sd_days * 24.0)
                        sd_period = KPDashaPeriod(
                            lord=sd_lord,
                            level=4,
                            start_date=_format_date(sookshma_start),
                            end_date=_format_date(sd_end),
                            duration=f"{int(sd_days)} D {sd_hours % 24} H" if sd_days >= 1 else f"{sd_hours} Hours",
                            is_current=is_sd_current,
                            start_time=sookshma_start.strftime("%H:%M"),
                            end_time=sd_end.strftime("%H:%M"),
                            sub_periods=[],
                        )
                        running_sookshma_list.append(sd_period)

                        if is_sd_current:
                            active_sd_period = sd_period

                            # Generate Pran Dashas (Level 5) under active Sookshma Dasha
                            pran_start_idx = DASHA_LORDS_ORDER.index(sd_lord)
                            pran_start = sookshma_start
                            for p in range(9):
                                pr_lord = DASHA_LORDS_ORDER[(pran_start_idx + p) % 9]
                                pr_years = DASHA_YEARS[pr_lord]
                                pr_days = (sd_days * pr_years) / TOTAL_DASHA_YEARS
                                pr_end = pran_start + timedelta(days=pr_days)
                                is_pr_current = pran_start <= current_dt <= pr_end

                                pr_mins = int(pr_days * 1440.0)
                                pr_period = KPDashaPeriod(
                                    lord=pr_lord,
                                    level=5,
                                    start_date=_format_date(pran_start),
                                    end_date=_format_date(pr_end),
                                    duration=f"{pr_mins // 60} H {pr_mins % 60} M",
                                    is_current=is_pr_current,
                                    start_time=pran_start.strftime("%H:%M"),
                                    end_time=pr_end.strftime("%H:%M"),
                                    sub_periods=[],
                                )
                                running_pran_list.append(pr_period)
                                if is_pr_current:
                                    active_pran_period = pr_period

                                pran_start = pr_end

                        sookshma_start = sd_end

                pad_start = pad_end

            ad_period = KPDashaPeriod(
                lord=ad_lord,
                level=2,
                start_date=_format_date(display_ad_start),
                end_date=_format_date(ad_end),
                duration=ad_duration_str,
                is_current=is_ad_current,
                start_time=display_ad_start.strftime("%H:%M"),
                end_time=ad_end.strftime("%H:%M"),
                insight=DASHA_INSIGHTS.get(ad_lord),
                sub_periods=pratyantardashas,
            )
            antardashas.append(ad_period)

            if is_ad_current:
                active_ad_period = ad_period

            ad_start = ad_end

        md_period = KPDashaPeriod(
            lord=current_md_lord,
            level=1,
            start_date=_format_date(display_md_start),
            end_date=_format_date(md_end),
            duration=md_duration_str,
            is_current=is_md_current,
            start_time=display_md_start.strftime("%H:%M"),
            end_time=md_end.strftime("%H:%M"),
            insight=DASHA_INSIGHTS.get(current_md_lord),
            sub_periods=antardashas,
        )
        dashas_result.append(md_period)

        if is_md_current:
            active_md_period = md_period

        md_start = md_end

    # Fallbacks if current date is outside or on edge
    if not active_md_period and dashas_result:
        active_md_period = dashas_result[0]
    if not active_ad_period and active_md_period and active_md_period.sub_periods:
        active_ad_period = active_md_period.sub_periods[0]
    if not active_pd_period and active_ad_period and active_ad_period.sub_periods:
        active_pd_period = active_ad_period.sub_periods[0]
    if not active_sd_period and running_sookshma_list:
        active_sd_period = running_sookshma_list[0]
    if not active_pran_period and running_pran_list:
        active_pran_period = running_pran_list[0]

    # Calculate remaining days and percentages
    rem_days_ad = 0
    rem_days_md = 0
    pct_ad = 50.0
    pct_md = 50.0

    if active_ad_period:
        try:
            ad_end_dt = datetime.strptime(active_ad_period.end_date, "%d-%m-%Y").replace(tzinfo=UTC)
            ad_start_dt = datetime.strptime(active_ad_period.start_date, "%d-%m-%Y").replace(tzinfo=UTC)
            tot_ad_span = max((ad_end_dt - ad_start_dt).total_seconds(), 1.0)
            elapsed_ad = max((current_dt - ad_start_dt).total_seconds(), 0.0)
            rem_days_ad = max(int((ad_end_dt - current_dt).days), 0)
            pct_ad = min(max(round((elapsed_ad / tot_ad_span) * 100.0, 1), 0.0), 100.0)
        except Exception:
            pass

    if active_md_period:
        try:
            md_end_dt = datetime.strptime(active_md_period.end_date, "%d-%m-%Y").replace(tzinfo=UTC)
            md_start_dt = datetime.strptime(active_md_period.start_date, "%d-%m-%Y").replace(tzinfo=UTC)
            tot_md_span = max((md_end_dt - md_start_dt).total_seconds(), 1.0)
            elapsed_md = max((current_dt - md_start_dt).total_seconds(), 0.0)
            rem_days_md = max(int((md_end_dt - current_dt).days), 0)
            pct_md = min(max(round((elapsed_md / tot_md_span) * 100.0, 1), 0.0), 100.0)
        except Exception:
            pass

    active_path = (
        f"{active_md_period.lord if active_md_period else ''} > "
        f"{active_ad_period.lord if active_ad_period else ''} > "
        f"{active_pd_period.lord if active_pd_period else ''} > "
        f"{active_sd_period.lord if active_sd_period else ''} > "
        f"{active_pran_period.lord if active_pran_period else ''}"
    )

    running_info = CurrentRunningDashaInfo(
        mahadasha=active_md_period.lord if active_md_period else "Sun",
        antardasha=active_ad_period.lord if active_ad_period else "Sun",
        pratyantardasha=active_pd_period.lord if active_pd_period else "Sun",
        sookshma_dasha=active_sd_period.lord if active_sd_period else "Sun",
        pran_dasha=active_pran_period.lord if active_pran_period else "Sun",
        active_path=active_path,
        md_start=active_md_period.start_date if active_md_period else "",
        md_end=active_md_period.end_date if active_md_period else "",
        ad_start=active_ad_period.start_date if active_ad_period else "",
        ad_end=active_ad_period.end_date if active_ad_period else "",
        pd_start=active_pd_period.start_date if active_pd_period else "",
        pd_end=active_pd_period.end_date if active_pd_period else "",
        sd_start=active_sd_period.start_date if active_sd_period else "",
        sd_end=active_sd_period.end_date if active_sd_period else "",
        pran_start=active_pran_period.start_date if active_pran_period else "",
        pran_end=active_pran_period.end_date if active_pran_period else "",
        remaining_days_ad=rem_days_ad,
        remaining_days_md=rem_days_md,
        percentage_completed_ad=pct_ad,
        percentage_completed_md=pct_md,
        sookshma_periods=running_sookshma_list,
        pran_periods=running_pran_list,
    )

    return balance_str, dashas_result, running_info


def _calculate_dasha_sandhi_and_chidra(
    running_info: CurrentRunningDashaInfo,
    dashas: list[KPDashaPeriod],
    current_dt: datetime,
) -> DashaSandhiChidraInfo:
    """Detects Chidra Dasha (final Antardasha) and Dasha Sandhi transition boundaries."""
    current_md_lord = running_info.mahadasha
    current_ad_lord = running_info.antardasha

    # Find the current MD in dashas list
    md_idx = -1
    for idx, md in enumerate(dashas):
        if md.lord == current_md_lord:
            md_idx = idx
            break

    is_chidra = False
    chidra_msg = ""
    next_md_lord = ""
    transition_date_str = ""
    days_to_trans = 0
    is_sandhi = False
    sandhi_msg = ""
    severity = "none"
    precautions: list[str] = []
    remedies: list[str] = []

    if md_idx >= 0 and md_idx < len(dashas):
        curr_md = dashas[md_idx]
        transition_date_str = curr_md.end_date
        next_md_lord = dashas[(md_idx + 1) % len(dashas)].lord

        # Is current AD the last AD in this MD?
        if curr_md.sub_periods and curr_md.sub_periods[-1].lord == current_ad_lord:
            is_chidra = True
            severity = "warning"
            chidra_key = (current_md_lord, current_ad_lord)
            chidra_msg = CHIDRA_DASHA_ALERTS.get(
                chidra_key,
                f"You are undergoing Chidra Dasha ({current_md_lord}-{current_ad_lord}), the closing chapter of {current_md_lord} Mahadasha. Prepare for transition to {next_md_lord}."
            )
            precautions.append("Avoid signing major irrevocable contracts without double-checking.")
            precautions.append("Postpone high-risk speculations or emotional real estate transactions.")
            precautions.append("Practice mindfulness and health checkups as planetary vibrations shift.")
            remedies.append(f"Chant Gayatri Mantra daily to balance the planetary exchange between {current_md_lord} and {next_md_lord}.")

        # Check Dasha Sandhi: within 180 days before or after MD transition
        try:
            trans_dt = datetime.strptime(curr_md.end_date, "%d-%m-%Y").replace(tzinfo=UTC)
            days_to_trans = int((trans_dt - current_dt).days)
            if 0 <= days_to_trans <= 180:
                is_sandhi = True
                severity = "critical" if days_to_trans <= 60 else "warning"
                sandhi_msg = f"Active Dasha Sandhi: Only {days_to_trans} days remain until entering {next_md_lord} Mahadasha. Overlapping energies are strong."
                precautions.append(f"Upcoming major shift from {current_md_lord} to {next_md_lord}. Maintain psychological composure.")
            elif -180 <= days_to_trans < 0:
                is_sandhi = True
                days_since = abs(days_to_trans)
                severity = "warning"
                sandhi_msg = f"Fresh Dasha Sandhi: Entered {current_md_lord} Mahadasha {days_since} days ago. The new planetary ruler is settling."
        except Exception:
            pass

    return DashaSandhiChidraInfo(
        is_in_chidra_dasha=is_chidra,
        is_in_dasha_sandhi=is_sandhi,
        chidra_message=chidra_msg,
        sandhi_message=sandhi_msg,
        current_md_lord=current_md_lord,
        next_md_lord=next_md_lord,
        transition_date=transition_date_str,
        days_to_transition=days_to_trans,
        alert_severity=severity,
        precautions=precautions,
        remedial_measures=remedies,
    )


def _get_rashi_name(idx: int) -> str:
    r = RASHIS_DATA[idx % 12]
    return r.get("name_en") or r.get("name") or "Aries"


def _calculate_personalized_dasha_phala(
    asc_sign_index: int,
    planets: list[Any],
) -> list[PersonalizedDashaPhalaItem]:
    """Generates personalized, Lagna-aware predictions for each planet."""
    asc_name = _get_rashi_name(asc_sign_index)
    functional_map = LAGNA_FUNCTIONAL_RULES.get(asc_sign_index, {})

    # Map planet locations
    planet_locs: dict[str, Any] = {}
    for p in planets:
        name = getattr(p, "name", "")
        if name:
            planet_locs[name] = p

    phala_list: list[PersonalizedDashaPhalaItem] = []

    for lord in DASHA_LORDS_ORDER:
        func_nature = functional_map.get(lord, "Neutral")
        p_obj = planet_locs.get(lord)

        house_placed = getattr(p_obj, "bhav_house", 1) if p_obj else 1
        sign_idx = getattr(p_obj, "sign_index", 0) if p_obj else 0
        sign_name = _get_rashi_name(sign_idx)
        is_retro = getattr(p_obj, "is_retrograde", False) if p_obj else False

        # Determine Dignity
        dignity = "Neutral"
        if sign_idx == EXALTATION_SIGNS.get(lord):
            dignity = "Exalted"
        elif sign_idx == DEBILITATION_SIGNS.get(lord):
            dignity = "Debilitated"
        elif sign_idx in OWN_SIGNS.get(lord, []):
            dignity = "Own Sign"
        elif house_placed in [1, 4, 7, 10]:
            dignity = "Kendra Strong"
        elif house_placed in [5, 9]:
            dignity = "Trikona Auspicious"

        # Calculate Favorability Score
        score = 50
        if "Yogakaraka" in func_nature:
            score += 35
        elif "Benefic" in func_nature:
            score += 25
        elif "Maraka" in func_nature:
            score -= 20
        elif "Malefic" in func_nature:
            score -= 25

        if dignity == "Exalted":
            score += 20
        elif dignity == "Own Sign":
            score += 15
        elif dignity == "Debilitated":
            score -= 25
        elif dignity in ["Kendra Strong", "Trikona Auspicious"]:
            score += 10

        if house_placed in [6, 8, 12]:
            score -= 15

        score = min(max(score, 10), 98)

        # Dynamic Life Domain Impacts
        houses_owned = [h for h in range(1, 13) if RASHIS_DATA[(asc_sign_index + h - 1) % 12]["lord"] == lord]

        career_text = (
            f"As {func_nature} placed in House {house_placed} ({sign_name}), career brings notable expansion, authority, and recognized efforts."
            if score >= 60 else
            f"Placed in House {house_placed}, career demands disciplined patience, avoiding sudden job leaps or conflicts with superiors."
        )

        wealth_text = (
            f"Financial stability is bolstered through structured earnings, assets, and timely investment growth."
            if score >= 55 else
            f"Expenditure pressures may arise; maintain strict liquid cash reserves and avoid speculative investments."
        )

        relationship_text = (
            "Harmonious domestic bliss, support from mentors, and rewarding mutual understanding."
            if score >= 50 else
            "Sensitivities in communication may emerge; cultivate patience and clear boundaries."
        )

        health_text = (
            "Robust vitality, strong immunity, and high energy for daily pursuits."
            if score >= 55 else
            "Energy fluctuations or vulnerability in digestion/nervous system; maintain adequate sleep and balanced diet."
        )

        gemstone_warn = ""
        if "Maraka" in func_nature or house_placed in [6, 8, 12] or dignity == "Debilitated":
            gemstone_warn = f"CAUTION: Do NOT wear gemstones of {lord} without an astrologer's prescription, as it rules sensitive/maraka houses for {asc_name} Lagna."
        else:
            gemstone_warn = f"Gemstone amplification for {lord} is supportive and auspicious during its sub-periods."

        phala_list.append(
            PersonalizedDashaPhalaItem(
                planet=lord,
                lagna=asc_name,
                functional_nature=func_nature,
                houses_owned=houses_owned,
                house_placed=house_placed,
                sign_placed=sign_name,
                dignity=dignity,
                is_retrograde=is_retro,
                favorability_score=score,
                overall_impact=f"Governing House {house_placed} in {sign_name}. {func_nature} delivering focused karmic results.",
                career_impact=career_text,
                wealth_impact=wealth_text,
                relationship_impact=relationship_text,
                health_impact=health_text,
                gemstone_warning=gemstone_warn,
                recommended_remedy=f"Regular chanting of {lord}'s mantra and charitable donation on its designated weekday.",
            )
        )

    return phala_list


def _calculate_yogini_dasha(
    birth_dt: datetime,
    moon_lon: float,
    current_dt: datetime,
) -> YoginiDashaSystem:
    """Calculates the 36-year Yogini Dasha cycle with 8 Yoginis and Antar-Yoginis."""
    nak_span = 360.0 / 27.0
    nak_idx = int(moon_lon / nak_span) % 27
    offset_in_nak = moon_lon % nak_span
    nak_name = NAKSHATRAS_DATA[nak_idx]["name"]

    elapsed_fraction = offset_in_nak / nak_span
    rem_fraction = 1.0 - elapsed_fraction

    # Parashara Yogini formula: (Nakshatra 1-based + 3) mod 8
    nak_number = nak_idx + 1
    yogini_idx_1based = (nak_number + 3) % 8
    if yogini_idx_1based == 0:
        yogini_idx_1based = 8
    start_yogini_idx = yogini_idx_1based - 1

    first_yogini_name = YOGINI_NAMES[start_yogini_idx]
    first_yogini_total_years = YOGINI_YEARS[first_yogini_name]

    balance_years_float = rem_fraction * first_yogini_total_years
    b_y = int(balance_years_float)
    rem_m = (balance_years_float - b_y) * 12.0
    b_m = int(rem_m)
    b_d = int(round((rem_m - b_m) * 30.0))
    balance_str = f"{b_y} Y {b_m} M {b_d} D"

    # Pre-natal start of first Yogini
    elapsed_days = (elapsed_fraction * first_yogini_total_years) * 365.25
    theo_start = birth_dt - timedelta(days=elapsed_days)

    all_periods: list[YoginiPeriodItem] = []
    current_yogini = first_yogini_name
    current_sub_yogini = first_yogini_name
    current_cycle_num = 1

    y_start = theo_start

    # Generate 3 cycles of 36 years (108 years total)
    for cycle in range(3):
        for idx in range(8):
            y_idx = (start_yogini_idx + idx) % 8
            y_name = YOGINI_NAMES[y_idx]
            y_years = YOGINI_YEARS[y_name]
            y_days = y_years * 365.25
            y_end = y_start + timedelta(days=y_days)

            is_first_period = (cycle == 0 and idx == 0)
            display_start = birth_dt if is_first_period else y_start

            is_curr = display_start <= current_dt <= y_end
            if is_curr:
                current_yogini = y_name
                current_cycle_num = cycle + 1

            # Generate 8 Antar-Yoginis
            sub_periods: list[YoginiPeriodItem] = []
            sub_start = y_start
            for s_idx in range(8):
                sub_y_idx = (y_idx + s_idx) % 8
                sub_name = YOGINI_NAMES[sub_y_idx]
                sub_years = YOGINI_YEARS[sub_name]
                sub_days = (y_years * sub_years * 365.25) / TOTAL_YOGINI_YEARS
                sub_end = sub_start + timedelta(days=sub_days)

                display_sub_start = birth_dt if (is_first_period and sub_start < birth_dt) else sub_start
                if is_first_period and sub_end <= birth_dt:
                    sub_start = sub_end
                    continue

                is_sub_curr = display_sub_start <= current_dt <= sub_end
                if is_sub_curr:
                    current_sub_yogini = sub_name

                sub_periods.append(
                    YoginiPeriodItem(
                        name=sub_name,
                        ruler_planet=YOGINI_RULERS[sub_name],
                        duration_years=sub_years,
                        start_date=_format_date(display_sub_start),
                        end_date=_format_date(sub_end),
                        is_current=is_sub_curr,
                        nature=YOGINI_NATURES[sub_name],
                        significance=f"Sub-period of {sub_name} under {y_name}.",
                        sub_periods=[],
                    )
                )
                sub_start = sub_end

            all_periods.append(
                YoginiPeriodItem(
                    name=y_name,
                    ruler_planet=YOGINI_RULERS[y_name],
                    duration_years=y_years,
                    start_date=_format_date(display_start),
                    end_date=_format_date(y_end),
                    is_current=is_curr,
                    nature=YOGINI_NATURES[y_name],
                    significance=f"{y_name} ({YOGINI_RULERS[y_name]}) - {YOGINI_NATURES[y_name]} vibration.",
                    sub_periods=sub_periods,
                )
            )
            y_start = y_end

    verdict = (
        f"Currently running {current_yogini} Yogini (ruled by {YOGINI_RULERS.get(current_yogini, '')}) "
        f"with {current_sub_yogini} sub-period in Cycle {current_cycle_num}. "
        f"Vibration is {YOGINI_NATURES.get(current_yogini, 'Neutral')}."
    )

    return YoginiDashaSystem(
        birth_nakshatra=nak_name,
        starting_yogini=first_yogini_name,
        balance_str=balance_str,
        current_yogini=current_yogini,
        current_sub_yogini=current_sub_yogini,
        current_cycle_number=current_cycle_num,
        periods=all_periods,
        verdict=verdict,
    )


def _calculate_dasha_transit_synergy(
    natal_moon_sign_idx: int,
    running_info: CurrentRunningDashaInfo,
    current_dt: datetime,
) -> DashaTransitSynergy:
    """Calculates live transit positions of MD/AD lords and detects Sade Sati status."""
    md_lord = running_info.mahadasha
    ad_lord = running_info.antardasha

    # Default fallback positions
    md_transit_sign_idx = 10  # Aquarius
    ad_transit_sign_idx = 1   # Taurus
    saturn_transit_sign_idx = 10  # Saturn in Aquarius/Pisces transit

    if HAS_SWISSEPH and swe is not None:
        try:
            # Calculate Julian Day for current UTC moment
            ut_hour = current_dt.hour + current_dt.minute / 60.0 + current_dt.second / 3600.0
            jd = swe.julday(current_dt.year, current_dt.month, current_dt.day, ut_hour)
            swe.set_sid_mode(swe.SIDM_LAHIRI)

            # Map planet names to swisseph codes
            code_map = {
                "Sun": swe.SUN,
                "Moon": swe.MOON,
                "Mars": swe.MARS,
                "Mercury": swe.MERCURY,
                "Jupiter": swe.JUPITER,
                "Venus": swe.VENUS,
                "Saturn": swe.SATURN,
                "Rahu": swe.MEAN_NODE,
                "Ketu": swe.MEAN_NODE,
            }

            if "Saturn" in code_map:
                res, _ = swe.calc_ut(jd, code_map["Saturn"], swe.FLG_SIDEREAL)
                saturn_transit_sign_idx = int(res[0] / 30.0) % 12

            if md_lord in code_map:
                res, _ = swe.calc_ut(jd, code_map[md_lord], swe.FLG_SIDEREAL)
                if md_lord == "Ketu":
                    md_transit_sign_idx = int((res[0] + 180.0) % 360.0 / 30.0) % 12
                else:
                    md_transit_sign_idx = int(res[0] / 30.0) % 12

            if ad_lord in code_map:
                res, _ = swe.calc_ut(jd, code_map[ad_lord], swe.FLG_SIDEREAL)
                if ad_lord == "Ketu":
                    ad_transit_sign_idx = int((res[0] + 180.0) % 360.0 / 30.0) % 12
                else:
                    ad_transit_sign_idx = int(res[0] / 30.0) % 12
        except Exception as exc:
            logger.warning(f"Live transit calculation error: {exc}")

    # Distance from Natal Moon (1 to 12)
    md_house_from_moon = ((md_transit_sign_idx - natal_moon_sign_idx) % 12) + 1
    ad_house_from_moon = ((ad_transit_sign_idx - natal_moon_sign_idx) % 12) + 1

    md_nature = "Favorable Upachaya House" if md_house_from_moon in [3, 6, 10, 11] else (
        "Challenging Dusthana" if md_house_from_moon in [8, 12] else "Neutral Transit"
    )
    ad_nature = "Favorable Upachaya House" if ad_house_from_moon in [3, 6, 10, 11] else (
        "Challenging Dusthana" if ad_house_from_moon in [8, 12] else "Neutral Transit"
    )

    # Detect Sade Sati / Kantaka Shani
    saturn_diff = (saturn_transit_sign_idx - natal_moon_sign_idx) % 12
    sade_sati_active = False
    sade_sati_phase = "None"
    sade_sati_desc = "No major Saturn Sade Sati obstruction at present."

    if saturn_diff == 11:
        sade_sati_active = True
        sade_sati_phase = "Rising Phase (12th House)"
        sade_sati_desc = "Saturn is transiting the 12th house from your natal Moon sign. Eye strain, sleep patterns, and expenditures require vigilance."
    elif saturn_diff == 0:
        sade_sati_active = True
        sade_sati_phase = "Peak Phase (1st House - Janma Shani)"
        sade_sati_desc = "Saturn is transiting directly over your Janma Rashi. Deep psychological introspection and steady patience bring maturity."
    elif saturn_diff == 1:
        sade_sati_active = True
        sade_sati_phase = "Setting Phase (2nd House)"
        sade_sati_desc = "Saturn is in the 2nd house from your Moon sign. Financial restructuring and family diplomacy are rewarded."
    elif saturn_diff == 3:
        sade_sati_phase = "Kantaka Shani (4th House)"
        sade_sati_desc = "Saturn transits the 4th house from natal Moon. Domestic adjustments and mother's well-being need care."
    elif saturn_diff == 7:
        sade_sati_phase = "Ashtama Shani (8th House)"
        sade_sati_desc = "Saturn transits the 8th house from natal Moon. Avoid reckless adventures and maintain steady discipline."

    # Synergy Score
    syn_score = 50
    if md_house_from_moon in [3, 6, 10, 11]:
        syn_score += 15
    elif md_house_from_moon in [8, 12]:
        syn_score -= 15

    if ad_house_from_moon in [3, 6, 10, 11]:
        syn_score += 15
    elif ad_house_from_moon in [8, 12]:
        syn_score -= 15

    if sade_sati_active:
        syn_score -= 10

    syn_score = min(max(syn_score, 15), 95)

    md_sign_name = _get_rashi_name(md_transit_sign_idx)
    ad_sign_name = _get_rashi_name(ad_transit_sign_idx)

    verdict = (
        f"MD Lord {md_lord} is transiting in {md_sign_name} (House {md_house_from_moon} from Moon - {md_nature}). "
        f"AD Lord {ad_lord} is transiting in {ad_sign_name} (House {ad_house_from_moon} from Moon - {ad_nature}). "
        f"Saturn Transit: {sade_sati_phase}. Overall planetary synergy is {syn_score}% aligned."
    )

    return DashaTransitSynergy(
        md_lord=md_lord,
        md_transit_sign=md_sign_name,
        md_transit_house_from_moon=md_house_from_moon,
        md_transit_nature=md_nature,
        ad_lord=ad_lord,
        ad_transit_sign=ad_sign_name,
        ad_transit_house_from_moon=ad_house_from_moon,
        ad_transit_nature=ad_nature,
        sade_sati_active=sade_sati_active,
        sade_sati_phase=sade_sati_phase,
        sade_sati_description=sade_sati_desc,
        synergy_verdict=verdict,
        synergy_score=syn_score,
    )


def _calculate_dasha_life_timeline(
    dashas: list[KPDashaPeriod],
    phala_map: dict[str, PersonalizedDashaPhalaItem],
    birth_year: int,
) -> list[DashaTimelineSegment]:
    """Generates visual life timeline bar segments for all Mahadashas."""
    segments: list[DashaTimelineSegment] = []
    accum_age = 0

    for md in dashas:
        p_item = phala_map.get(md.lord)
        score = p_item.favorability_score if p_item else 50

        nature = "favorable" if score >= 65 else ("challenging" if score <= 40 else "neutral")

        # Parse years from duration or start/end dates
        dur_years = float(DASHA_YEARS.get(md.lord, 10))
        try:
            s_year = int(md.start_date.split("-")[2])
            e_year = int(md.end_date.split("-")[2])
            dur_years = max(float(e_year - s_year), 1.0)
        except Exception:
            pass

        age_start = accum_age
        age_end = int(accum_age + dur_years)
        accum_age = age_end

        theme_text = (
            f"Period of major empowerment, progress, and fruitful outcomes."
            if score >= 65 else
            (f"Transformative period demanding patience and cautious navigation." if score <= 40 else "Balanced growth through steady perseverance.")
        )

        segments.append(
            DashaTimelineSegment(
                lord=md.lord,
                start_date=md.start_date,
                end_date=md.end_date,
                age_start=age_start,
                age_end=age_end,
                duration_years=dur_years,
                nature=nature,
                favorability_score=score,
                theme=theme_text,
                is_current=md.is_current,
            )
        )

    return segments


def calculate_advanced_dasha(payload: KPCalculateRequest) -> KPCalculateResponse:
    """Master entry point for full-fledged Advanced Dasha calculation.
    
    Delegates to KP calculator core for astronomical coordinates, then enriches with
    uncompressed Vimshottari hierarchy, 5-tier running metrics, Sandhi/Chidra alerts,
    Personalized Kundli-aware Phala, Yogini Dasha, Live Transit synergy, and Life Timeline.
    """
    # 1. Obtain baseline KP astrological output
    res: KPCalculateResponse = calculate_kp(payload)

    # Determine birth moment and current UTC moment
    birth_dt = datetime(
        payload.year, payload.month, payload.day,
        payload.hour, payload.minute, payload.second,
        tzinfo=UTC,
    )
    current_dt = datetime.now(UTC)

    # Locate natal Moon longitude and Ascendant sign
    moon_lon = 0.0
    for p in res.planets:
        if p.name == "Moon":
            moon_lon = p.longitude
            break

    asc_sign_index = 0
    for p in res.planets:
        if p.name == "Asc":
            asc_sign_index = p.sign_index
            break
    if asc_sign_index == 0 and res.cusps:
        asc_sign_index = res.cusps[0].sign_index

    natal_moon_sign_idx = int(moon_lon / 30.0) % 12

    # 2. Authentic Uncompressed Vimshottari Dasha Hierarchy
    balance_str, uncompressed_dashas, running_info = _calculate_uncompressed_vimshottari(
        birth_dt=birth_dt,
        moon_lon=moon_lon,
        current_dt=current_dt,
    )
    res.dashas = uncompressed_dashas
    res.current_running_dasha = running_info

    # 3. Dasha Sandhi & Chidra Alert Detector
    res.dasha_sandhi_chidra = _calculate_dasha_sandhi_and_chidra(
        running_info=running_info,
        dashas=uncompressed_dashas,
        current_dt=current_dt,
    )

    # 4. Personalized Kundli-Aware Dasha Phala
    phala_list = _calculate_personalized_dasha_phala(
        asc_sign_index=asc_sign_index,
        planets=res.planets,
    )
    res.personalized_dasha_phala = phala_list
    phala_map = {item.planet: item for item in phala_list}

    # 5. Yogini Dasha (36-Year Cycle)
    res.yogini_dasha = _calculate_yogini_dasha(
        birth_dt=birth_dt,
        moon_lon=moon_lon,
        current_dt=current_dt,
    )

    # 6. Live Dasha-Transit Synergy & Sade Sati
    res.dasha_transit_synergy = _calculate_dasha_transit_synergy(
        natal_moon_sign_idx=natal_moon_sign_idx,
        running_info=running_info,
        current_dt=current_dt,
    )

    # 7. Life Timeline Bar Segments
    res.dasha_life_timeline = _calculate_dasha_life_timeline(
        dashas=uncompressed_dashas,
        phala_map=phala_map,
        birth_year=payload.year,
    )

    return res
