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

from datetime import UTC, date, datetime, timedelta

from loguru import logger

from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.models.call import CallSession
from app.models.enums import CallStatus, UserRole
from app.models.profile import BirthDetails
from app.models.user import User
from app.schemas.astrology import RashiCalculateRequest
from app.schemas.copilot import (
    CoPilotBirthDetailsInput,
    CoPilotDashaPeriod,
    CoPilotPlanetPosition,
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


RASHI_LOCALIZED: dict[str, dict[str, str]] = {
    "Aries": {"bn": "মেষ", "hi": "मेष"},
    "Taurus": {"bn": "বৃষ", "hi": "वृषभ"},
    "Gemini": {"bn": "মিথুন", "hi": "मिथुन"},
    "Cancer": {"bn": "কর্কট", "hi": "कर्क"},
    "Leo": {"bn": "সিংহ", "hi": "सिंह"},
    "Virgo": {"bn": "কন্যা", "hi": "कन्या"},
    "Libra": {"bn": "তুলা", "hi": "तुला"},
    "Scorpio": {"bn": "বৃশ্চিক", "hi": "वृश्चिक"},
    "Sagittarius": {"bn": "ধনু", "hi": "धनु"},
    "Capricorn": {"bn": "মকর", "hi": "मकर"},
    "Aquarius": {"bn": "কুম্ভ", "hi": "कुंभ"},
    "Pisces": {"bn": "মীন", "hi": "मीन"},
}


def _sign_label(sign: str, language: str) -> str:
    names = RASHI_LOCALIZED.get(sign)
    if not names:
        return sign
    if language == "en":
        return sign
    return names.get(language) or sign


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

    if birth is None or birth.date_of_birth is None:
        base.unavailable_reason = _NO_BIRTH_DETAILS[language]
        return base

    hour, minute, time_parsed = _parse_birth_time(birth.time_of_birth)
    time_known = bool(birth.is_time_known) and time_parsed

    lat = birth.latitude if birth.latitude is not None else 22.5726
    lon = birth.longitude if birth.longitude is not None else 88.3639
    tz_offset = birth.timezone_offset if birth.timezone_offset is not None else 5.5
    tz_name = birth.timezone or "Asia/Kolkata"

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
                place=birth.place or "Kolkata, India",
                latitude=lat,
                longitude=lon,
                timezone=tz_offset,
                timezone_name=tz_name,
                language=language,
            )
        )

        # The offset the engine actually used, which is what turns the local
        # birth time into the UTC instant the dasha is measured from. The field
        # is optional on the response, so the stored offset stands in.
        offset_hours = (
            rashi.timezone_resolution.offset_hours
            if rashi.timezone_resolution is not None
            else tz_offset
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
    base.ascendant = _sign_label(rashi.ascendant_rashi_name_en, language)
    base.ascendant_degree = rashi.ascendant_degree_formatted
    base.birth_date_str = birth.date_of_birth.strftime("%d-%m-%Y")
    base.birth_time_str = birth.time_of_birth or ("12:00 (Indicative)" if not time_known else "12:00")
    base.birth_place_str = birth.place or birth.city or "Kolkata, India"
    base.moon_sign = moon_sign
    base.nakshatra = rashi.nakshatra_name

    # Planetary placements cheat-sheet for live chamber consultation
    planets_list: list[CoPilotPlanetPosition] = []
    for p in (rashi.planets or []):
        planets_list.append(
            CoPilotPlanetPosition(
                name=p.name,
                label=_planet_label(p.name, language),
                sign=p.sign,
                sign_label=_sign_label(p.sign, language),
                house=p.house,
                degree_formatted=p.degree_formatted,
                is_retrograde=p.is_retrograde,
            )
        )
    base.planets = planets_list

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


async def resolve_effective_birth(
    session: CallSession,
    client: User,
) -> BirthDetails | None:
    """Finds, auto-geocodes, and enriches birth details for this call's client."""
    birth = client.birth
    has_dob = birth is not None and birth.date_of_birth is not None

    if not has_dob and session.appointment_id:
        from app.models.appointment import Appointment

        appt = await Appointment.get(session.appointment_id)
        if appt and appt.birth_details:
            bd = appt.birth_details
            raw_dob = bd.get("date_of_birth") or bd.get("dob") or bd.get("birth_date")
            dob_parsed = None
            if raw_dob:
                if isinstance(raw_dob, date):
                    dob_parsed = raw_dob
                elif isinstance(raw_dob, str):
                    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
                        try:
                            dob_parsed = datetime.strptime(raw_dob.strip(), fmt).date()
                            break
                        except ValueError:
                            pass
            if dob_parsed:
                tob = bd.get("time_of_birth") or bd.get("tob") or bd.get("birth_time")
                place = bd.get("place") or bd.get("city") or bd.get("pob") or ""
                lat = bd.get("latitude") or bd.get("lat")
                lon = bd.get("longitude") or bd.get("lon") or bd.get("lng")
                tz = bd.get("timezone")
                tz_off = bd.get("timezone_offset")
                is_time_known = bool(bd.get("is_time_known", bool(tob)))

                birth = BirthDetails(
                    date_of_birth=dob_parsed,
                    time_of_birth=str(tob) if tob else None,
                    is_time_known=is_time_known,
                    place=str(place) if place else None,
                    latitude=float(lat) if lat is not None else None,
                    longitude=float(lon) if lon is not None else None,
                    timezone=str(tz) if tz else None,
                    timezone_offset=float(tz_off) if tz_off is not None else None,
                )
                has_dob = True

    if not has_dob or birth is None or birth.date_of_birth is None:
        return None

    # Auto-resolve coordinates if missing
    needs_geocode = (
        birth.latitude is None
        or birth.longitude is None
        or birth.timezone is None
    )

    if needs_geocode:
        target_query = (birth.place or birth.city or birth.state or "India").strip()
        matched = False
        try:
            from app.services.astrology.geocoder import geocode_place

            results = await geocode_place(target_query)
            if results and len(results) > 0:
                best = results[0]
                birth.latitude = float(best["latitude"])
                birth.longitude = float(best["longitude"])
                birth.timezone = best.get("timezone_name") or "Asia/Kolkata"
                birth.timezone_offset = float(best.get("timezone") or 5.5)
                if not birth.place:
                    birth.place = best.get("display_name") or target_query
                matched = True
        except Exception as exc:
            logger.warning("Auto-geocoding for birth place '{}' failed: {}", target_query, exc)

        if not matched and (birth.latitude is None or birth.longitude is None):
            birth.latitude = 22.5726
            birth.longitude = 88.3639
            birth.timezone = birth.timezone or "Asia/Kolkata"
            birth.timezone_offset = birth.timezone_offset if birth.timezone_offset is not None else 5.5

        try:
            client.birth = birth
            await client.save()
        except Exception as exc:
            logger.warning("Could not persist auto-resolved birth coordinates to user: {}", exc)

    return birth


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
    # (or platform admin) sees it, and only for as long as the call is live.
    is_authorized = (
        viewer.id == session.astrologer_user_id
        or viewer.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN)
    )
    if not is_authorized:
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

    effective_birth = await resolve_effective_birth(session, client)

    return build_summary(
        session_id=str(session.id),
        client_name=client.full_name,
        birth=effective_birth,
        language=language or viewer.language,
    )


async def update_client_birth_details(
    *,
    session_id,
    viewer: User,
    payload: CoPilotBirthDetailsInput,
    language: str | None = None,
) -> CoPilotSummary:
    """Updates client birth details directly from the live chamber.

    Geocodes the place, saves coordinates to client.birth, syncs to appointment
    if linked, and recalculates the live chart summary immediately.
    """
    session = await CallSession.get(session_id)
    if session is None:
        raise NotFoundError("Call not found.", error_code="call_not_found")

    is_authorized = (
        viewer.id == session.astrologer_user_id
        or viewer.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN)
    )
    if not is_authorized:
        raise ForbiddenError(
            "Only this call's astrologer can update client birth details.",
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

    raw_dob = payload.date_of_birth.strip()
    dob_parsed = None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            dob_parsed = datetime.strptime(raw_dob, fmt).date()
            break
        except ValueError:
            pass
    if dob_parsed is None:
        raise BadRequestError(
            "Invalid date of birth format. Please use YYYY-MM-DD or DD-MM-YYYY.",
            error_code="invalid_dob",
        )

    lat = payload.latitude
    lon = payload.longitude
    tz_name = payload.timezone
    tz_offset = payload.timezone_offset
    clean_place = payload.place.strip()

    if lat is None or lon is None or not tz_name:
        try:
            from app.services.astrology.geocoder import geocode_place

            results = await geocode_place(clean_place)
            if results and len(results) > 0:
                best = results[0]
                lat = float(best["latitude"])
                lon = float(best["longitude"])
                tz_name = best.get("timezone_name") or "Asia/Kolkata"
                tz_offset = float(best.get("timezone") or 5.5)
                if not clean_place:
                    clean_place = best.get("display_name") or clean_place
        except Exception as exc:
            logger.warning("Geocoding during in-session birth update failed: {}", exc)

    if lat is None or lon is None:
        lat = 22.5726
        lon = 88.3639
        tz_name = tz_name or "Asia/Kolkata"
        tz_offset = tz_offset if tz_offset is not None else 5.5

    client.birth = BirthDetails(
        date_of_birth=dob_parsed,
        time_of_birth=payload.time_of_birth.strip() if payload.time_of_birth else None,
        is_time_known=payload.is_time_known,
        place=clean_place,
        latitude=lat,
        longitude=lon,
        timezone=tz_name,
        timezone_offset=tz_offset,
    )
    await client.save()

    if session.appointment_id:
        from app.models.appointment import Appointment

        appt = await Appointment.get(session.appointment_id)
        if appt:
            appt.birth_details = {
                "date_of_birth": dob_parsed.isoformat(),
                "time_of_birth": payload.time_of_birth,
                "is_time_known": payload.is_time_known,
                "place": clean_place,
                "latitude": lat,
                "longitude": lon,
                "timezone": tz_name,
                "timezone_offset": tz_offset,
            }
            await appt.save()

    return build_summary(
        session_id=str(session.id),
        client_name=client.full_name,
        birth=client.birth,
        language=language or viewer.language,
    )
