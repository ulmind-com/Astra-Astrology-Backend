"""The astrologer's live Co-Pilot.

During a session the astrologer should not have to leave the call to look up
where the client stands. This builds that one-glance summary: the running
Vimshottari Mahadasha and Antardasha, Saturn's Sade Sati phase, and the single
planet whose remedy is most worth prescribing right now.

Two rules shape everything below.

Nothing is invented. The summary is built only from birth details the client
actually saved, and only when those details can produce a chart. A placeholder
birth date would give the astrologer a confident, wrong dasha to read aloud,
which is worse than an empty panel.

Nothing is stored. The whole calculation takes about ten milliseconds, so it
runs per request. There is no cache to go stale and no copy of the client's
chart sitting in another collection.
"""

from datetime import UTC, datetime, timedelta

from loguru import logger

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.call import CallSession
from app.models.enums import CallStatus
from app.models.profile import BirthDetails
from app.models.user import User
from app.schemas.astrology import RashiCalculateRequest
from app.schemas.copilot import (
    CoPilotDashaPeriod,
    CoPilotRemedyFocus,
    CoPilotSadeSati,
    CoPilotSummary,
)
from app.services.astrology.calculator import calculate_rashi
from app.services.astrology.dasha_calculator import running_vimshottari
from app.services.astrology.kp_calculator import DASHA_INSIGHTS
from app.services.astrology.kundli_service import GEMSTONES_MASTER, PLANET_NAMES_LOCALIZED

SUPPORTED_LANGUAGES = ("en", "bn", "hi")

# The panel is for a session in progress. Ringing is included so the summary is
# already on screen the moment the astrologer answers.
LIVE_STATUSES = (CallStatus.RINGING, CallStatus.ACTIVE)

_NO_BIRTH_DETAILS = {
    "en": (
        "This client has not saved their birth details yet, so no chart can be drawn. "
        "Ask for the date, exact time and place of birth, and they can add it under "
        "their profile."
    ),
    "bn": (
        "এই ক্লায়েন্ট এখনো জন্মবিবরণ সংরক্ষণ করেননি, তাই কোনো চার্ট তৈরি করা যাচ্ছে না। "
        "জন্মতারিখ, সঠিক সময় ও স্থান জিজ্ঞেস করুন — তিনি প্রোফাইল থেকে যোগ করতে পারবেন।"
    ),
    "hi": (
        "इस क्लाइंट ने अभी जन्म विवरण सहेजा नहीं है, इसलिए कुंडली नहीं बन सकती। "
        "जन्म तिथि, सटीक समय और स्थान पूछें — वे अपनी प्रोफ़ाइल में जोड़ सकते हैं।"
    ),
}

_TIME_UNKNOWN = {
    "en": (
        "The client did not give a birth time, so noon was assumed. The Moon moves "
        "about half a degree an hour, so the Mahadasha and Antardasha below are "
        "indicative only — confirm the birth time before relying on them."
    ),
    "bn": (
        "ক্লায়েন্ট জন্মসময় দেননি, তাই দুপুর ১২টা ধরা হয়েছে। চন্দ্র ঘণ্টায় প্রায় আধ ডিগ্রি সরে, "
        "তাই নিচের মহাদশা ও অন্তর্দশা কেবল আনুমানিক — নির্ভর করার আগে জন্মসময় যাচাই করুন।"
    ),
    "hi": (
        "क्लाइंट ने जन्म समय नहीं दिया, इसलिए दोपहर १२ बजे मान लिया गया है। चंद्रमा प्रति घंटे "
        "लगभग आधा अंश चलता है, अतः नीचे दी गई महादशा और अंतर्दशा केवल अनुमानित है — "
        "भरोसा करने से पहले जन्म समय की पुष्टि करें।"
    ),
}

_CALCULATION_FAILED = {
    "en": "The chart could not be calculated from the saved birth details.",
    "bn": "সংরক্ষিত জন্মবিবরণ থেকে চার্ট গণনা করা যায়নি।",
    "hi": "सहेजे गए जन्म विवरण से कुंडली की गणना नहीं हो सकी।",
}

_REASON_SADE_SATI = {
    "en": "Saturn is in {phase}, which outweighs the running dasha right now.",
    "bn": "শনি এখন {phase}-এ, যা চলতি দশার চেয়েও বেশি গুরুত্বপূর্ণ।",
    "hi": "शनि इस समय {phase} में है, जो चल रही दशा से अधिक महत्वपूर्ण है।",
}

_REASON_ANTARDASHA = {
    "en": "{planet} rules the running Antardasha, so it shapes day-to-day results now.",
    "bn": "চলতি অন্তর্দশার অধিপতি {planet}, তাই এখন দৈনন্দিন ফলাফল এটিই নিয়ন্ত্রণ করছে।",
    "hi": "चल रही अंतर्दशा के स्वामी {planet} हैं, अतः दैनिक फल अब यही निर्धारित करते हैं।",
}


def _normalise_language(language: str | None) -> str:
    code = (language or "en").strip().lower()[:2]
    return code if code in SUPPORTED_LANGUAGES else "en"


def _planet_label(planet: str, language: str) -> str:
    """A dasha lord's name in the requested language, falling back to English."""
    names = PLANET_NAMES_LOCALIZED.get(planet)
    if not names:
        return planet
    if language == "en":
        return planet
    return names.get(language) or planet


def _parse_birth_time(raw: str | None) -> tuple[int, int, bool]:
    """Hour and minute from a stored 'HH:MM', and whether it was usable.

    A stored time that will not parse is treated exactly like a missing one:
    noon, and the panel says the dasha is indicative. Guessing at a malformed
    value would be the same mistake as inventing one.
    """
    if not raw:
        return 12, 0, False
    parts = str(raw).strip().split(":")
    try:
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
    except (ValueError, IndexError):
        return 12, 0, False
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return 12, 0, False
    return hour, minute, True


def _remedy_focus(
    *,
    sade_sati: CoPilotSadeSati | None,
    antardasha_lord: str,
    language: str,
) -> CoPilotRemedyFocus:
    """The one planet to prescribe for.

    An active Sade Sati or Dhaiya takes precedence: Saturn's pressure is what
    the client has come about. Otherwise the Antardasha lord governs the
    day-to-day and is the useful thing to speak to.
    """
    if sade_sati is not None and sade_sati.is_active:
        planet = "Saturn"
        reason = _REASON_SADE_SATI[language].format(phase=sade_sati.phase_title)
    else:
        planet = antardasha_lord
        reason = _REASON_ANTARDASHA[language].format(
            planet=_planet_label(antardasha_lord, language)
        )

    insight = DASHA_INSIGHTS.get(planet)
    # Rahu and Ketu rule dashas but have no gemstone, so these stay empty.
    stone = GEMSTONES_MASTER.get(planet, {})
    suffix = "" if language == "en" else f"_{language}"

    return CoPilotRemedyFocus(
        planet=planet,
        planet_label=_planet_label(planet, language),
        reason=reason,
        remedies=list(insight.remedies) if insight else [],
        beej_mantra=insight.beej_mantra if insight else "",
        deity=insight.deity if insight else "",
        lucky_day=insight.lucky_day if insight else "",
        gemstone=stone.get(f"stone_name{suffix}") or stone.get("stone_name", ""),
        gemstone_metal=stone.get(f"metal{suffix}") or stone.get("metal", ""),
        gemstone_finger=stone.get(f"finger{suffix}") or stone.get("finger", ""),
        gemstone_day=stone.get(f"wearing_day{suffix}") or stone.get("wearing_day", ""),
    )


def build_summary(
    *,
    session_id: str,
    client_name: str,
    birth: BirthDetails | None,
    language: str = "en",
    now: datetime | None = None,
) -> CoPilotSummary:
    """The summary for one client, from their saved birth details alone.

    Separated from the session lookup so it can be calculated — and tested —
    without a call in progress.
    """
    language = _normalise_language(language)
    moment = now or datetime.now(UTC)
    base = CoPilotSummary(
        session_id=session_id,
        client_name=client_name or "Client",
        language=language,
        is_ready=False,
        computed_at=moment.isoformat(),
    )

    if birth is None or not birth.is_chart_ready or birth.date_of_birth is None:
        base.unavailable_reason = _NO_BIRTH_DETAILS[language]
        return base

    hour, minute, time_parsed = _parse_birth_time(birth.time_of_birth)
    time_known = bool(birth.is_time_known) and time_parsed

    try:
        rashi = calculate_rashi(
            RashiCalculateRequest(
                name=client_name or "Client",
                gender="other",
                day=birth.date_of_birth.day,
                month=birth.date_of_birth.month,
                year=birth.date_of_birth.year,
                hour=hour,
                minute=minute,
                second=0,
                # The stored time is already on a 24-hour clock. Without this the
                # request schema's default would read 09:00 as 21:00.
                period="24H",
                place=birth.place or "",
                latitude=birth.latitude,
                longitude=birth.longitude,
                timezone=birth.timezone_offset if birth.timezone_offset is not None else 5.5,
                # Preferred over the stored offset: this resolves the true offset
                # at the birth instant, including daylight saving.
                timezone_name=birth.timezone,
                language=language,
            )
        )

        # The offset the engine actually used, which is what turns the local
        # birth time into the UTC instant the dasha is measured from. The field
        # is optional on the response, so the stored offset stands in.
        offset_hours = (
            rashi.timezone_resolution.offset_hours
            if rashi.timezone_resolution is not None
            else (birth.timezone_offset if birth.timezone_offset is not None else 5.5)
        )
        midnight_utc = datetime(
            birth.date_of_birth.year,
            birth.date_of_birth.month,
            birth.date_of_birth.day,
            tzinfo=UTC,
        )
        birth_utc = midnight_utc + timedelta(hours=(hour + minute / 60.0) - offset_hours)

        running = running_vimshottari(
            birth_dt=birth_utc,
            moon_longitude=rashi.moon_sidereal_longitude,
            current_dt=moment,
        )
    except Exception as exc:
        logger.warning("Co-Pilot could not calculate a chart: {}", exc)
        base.unavailable_reason = _CALCULATION_FAILED[language]
        return base

    # Also optional on the response. Without it the panel shows the dasha and
    # falls back to the Antardasha lord for the remedy, rather than claiming
    # Saturn is quiet when it was simply not calculated.
    status = rashi.sade_sati_status
    sade_sati = (
        CoPilotSadeSati(
            is_active=status.is_active,
            phase_code=status.phase_code,
            phase_title=status.phase_title,
            impact_level=status.impact_level,
            saturn_sign=status.saturn_sign_name,
            saturn_house_from_moon=status.saturn_house_from_moon,
            description=status.description,
            remedy_summary=status.remedy_summary,
        )
        if status is not None
        else None
    )

    moon_sign = {
        "bn": rashi.rashi_name_bn,
        "hi": rashi.rashi_name_hi,
    }.get(language) or rashi.rashi_name_en

    base.is_ready = True
    base.is_birth_time_known = time_known
    base.accuracy_note = "" if time_known else _TIME_UNKNOWN[language]
    base.moon_sign = moon_sign
    base.nakshatra = rashi.nakshatra_name
    base.mahadasha = CoPilotDashaPeriod(
        lord=running.mahadasha,
        lord_label=_planet_label(running.mahadasha, language),
        starts_on=running.md_start,
        ends_on=running.md_end,
        percent_complete=round(running.percentage_completed_md, 1),
        days_remaining=max(running.remaining_days_md, 0),
    )
    base.antardasha = CoPilotDashaPeriod(
        lord=running.antardasha,
        lord_label=_planet_label(running.antardasha, language),
        starts_on=running.ad_start,
        ends_on=running.ad_end,
        percent_complete=round(running.percentage_completed_ad, 1),
        days_remaining=max(running.remaining_days_ad, 0),
    )
    base.sade_sati = sade_sati
    base.remedy_focus = _remedy_focus(
        sade_sati=sade_sati,
        antardasha_lord=running.antardasha,
        language=language,
    )
    return base


async def summary_for_call(
    *,
    session_id,
    viewer: User,
    language: str | None = None,
) -> CoPilotSummary:
    """The Co-Pilot summary for a live call, for that call's astrologer only."""
    session = await CallSession.get(session_id)
    if session is None:
        raise NotFoundError("Call not found.", error_code="call_not_found")

    # The client's chart is theirs. Only the astrologer they are speaking to
    # sees it, and only for as long as the call is live.
    if viewer.id != session.astrologer_user_id:
        raise ForbiddenError(
            "Only this call's astrologer can open the Co-Pilot.",
            error_code="not_your_call",
        )
    if session.status not in LIVE_STATUSES:
        raise ForbiddenError(
            "The Co-Pilot is only available while the session is live.",
            error_code="call_not_live",
        )

    client = await User.get(session.user_id)
    if client is None:
        raise NotFoundError("Client not found.", error_code="client_not_found")

    return build_summary(
        session_id=str(session.id),
        client_name=client.full_name,
        birth=client.birth,
        language=language or viewer.language,
    )
