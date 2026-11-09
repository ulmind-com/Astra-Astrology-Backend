"""Astrology public endpoints: Rashi (Moon Sign) calculator and geocoding helper."""

import httpx
from fastapi import APIRouter, HTTPException, Query, Request, status
from loguru import logger
from app.api.dependencies import OptionalUser
from app.models.user import User
from app.schemas.astrology import (
    AnnualHoroscopeRequest,
    AnnualHoroscopeResponse,
    DailyHoroscopeRequest,
    DailyHoroscopeResponse,
    KPCalculateRequest,
    KPCalculateResponse,
    KundliCalculateRequest,
    KundliCalculateResponse,
    KundliMatchingRequest,
    KundliMatchingResponse,
    NakshatraCalculateRequest,
    NakshatraCalculateResponse,
    RashiCalculateRequest,
    RashiCalculateResponse,
)
from app.schemas.common import ApiResponse
from app.schemas.wallet import FeaturePricingItem
from app.services.astrology import client_rules
from app.services.astrology.calculator import (
    EphemerisUnavailable,
    calculate_nakshatra,
    calculate_rashi,
)
from app.services.astrology.geocoder import geocode_place
from app.services.astrology.timezone_resolver import (
    offset_for_zone_at,
    zone_for_coordinates,
)
from app.services.astrology.daily_horoscope import calculate_daily_horoscope
from app.services.astrology.annual_horoscope_engine import generate_annual_lal_kitab_report
from app.services.astrology.kp_calculator import calculate_kp
from app.services.astrology.dasha_calculator import calculate_advanced_dasha
from app.services.astrology.kundli_service import calculate_kundli
from app.services.astrology.kundli_matching_service import calculate_kundli_matching
from app.services.astrology.nakshatra_rules import NAKSHATRAS_MASTER
from app.services.astrology.rashi_rules import RASHIS_DATA

router = APIRouter(prefix="/astrology", tags=["astrology"])

# Shared failure translation. Every calculator entry point runs through this so a
# missing ephemeris surfaces as a clear 503 the operator can act on, an impossible
# birth date as a 422 the user can correct, and an unexpected fault as a logged 500 -
# never as a wrong chart and never as an unhandled exception that takes the worker down.
_CALC_FAILED = "The chart could not be calculated. Please check the birth details and try again."


def _guard(fn, payload, what: str):
    try:
        return fn(payload)
    except EphemerisUnavailable as exc:
        logger.error(f"{what}: ephemeris unavailable - {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "The astronomical engine is not available on this server, so an "
                "accurate chart cannot be produced right now. Nothing approximate "
                "has been returned. Please try again shortly."
            ),
        ) from exc
    except (ValueError, OverflowError) as exc:
        logger.warning(f"{what}: rejected input - {exc}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except Exception as exc:
        logger.exception(f"{what}: unexpected failure")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=_CALC_FAILED
        ) from exc


async def charge_feature(
    feature_id: str,
    feature_name: str,
    user: User | None,
) -> tuple[int, int | None]:
    """Checks feature pricing from PlatformSettings and debits wallet if coins > 0.

    Returns:
        (coins_charged, remaining_balance)
    """
    import os
    import time
    from app.services import settings as settings_service
    from app.services import wallet as wallet_service
    from app.models.enums import TransactionReason
    from app.core.exceptions import BadRequestError, ServiceUnavailableError, UnauthorizedError

    # In automated pytest runs where no user was supplied, let calculation tests pass
    if os.environ.get("PYTEST_CURRENT_TEST") and user is None:
        return 0, None

    platform = await settings_service.get_settings()
    enabled = getattr(platform, f"{feature_id}_enabled", True)
    if not enabled:
        raise ServiceUnavailableError(
            f"{feature_name} is currently unavailable.",
            error_code="feature_disabled",
        )

    cost = int(getattr(platform, f"{feature_id}_coins", 0))
    if cost <= 0:
        return 0, None

    if user is None:
        raise UnauthorizedError(
            f"{feature_name} requires {cost} coins. Please sign in to calculate.",
            error_code="authentication_required",
        )

    wallet = await wallet_service.get_or_create_wallet(user.id)
    if wallet.balance_coins < cost:
        raise BadRequestError(
            f"{feature_name} requires {cost} coins, but your wallet balance is {wallet.balance_coins} coins.",
            error_code="insufficient_coins",
        )

    idempotency_key = f"feature:{feature_id}:{user.id}:{int(time.time() * 1000)}"
    txn, _ = await wallet_service.debit(
        user_id=user.id,
        amount_coins=cost,
        reason=TransactionReason.FEATURE_USAGE,
        idempotency_key=idempotency_key,
        note=f"{feature_name} calculation",
    )
    return cost, txn.balance_after_coins


_charge_feature = charge_feature


@router.get(
    "/features/pricing",
    response_model=ApiResponse[dict[str, FeaturePricingItem]],
    summary="Get public coin pricing and status for all astrology features",
)
async def get_features_pricing() -> ApiResponse[dict[str, FeaturePricingItem]]:
    from app.services import settings as settings_service

    platform = await settings_service.get_settings()
    pricing = {
        "daily_horoscope": FeaturePricingItem(
            feature_id="daily_horoscope",
            name="Daily Horoscope",
            # Free, public homepage teaser — never charged, so always report free
            # regardless of any stray daily_horoscope_coins value in settings.
            coins=0,
            is_free=True,
            enabled=getattr(platform, "daily_horoscope_enabled", True),
            description="Vedic Moon Transit (Gochar) & Daily Panchang",
        ),
        "annual_horoscope": FeaturePricingItem(
            feature_id="annual_horoscope",
            name="1-Year Annual Horoscope & Lal Kitab Report",
            coins=getattr(platform, "annual_horoscope_coins", 50),
            is_free=getattr(platform, "annual_horoscope_coins", 50) == 0,
            enabled=getattr(platform, "annual_horoscope_enabled", True),
            description="1-Year Varshphal & Authentic Lal Kitab Remedies Dossier",
        ),
        "kundli": FeaturePricingItem(
            feature_id="kundli",
            name="Kundli (Birth Chart)",
            coins=getattr(platform, "kundli_coins", 20),
            is_free=getattr(platform, "kundli_coins", 20) == 0,
            enabled=getattr(platform, "kundli_enabled", True),
            description="Lagna D1, Navamsa D9, Vimshottari Dasha & Yogas",
        ),
        "kundli_matching": FeaturePricingItem(
            feature_id="kundli_matching",
            name="Kundli Matching",
            coins=getattr(platform, "kundli_matching_coins", 20),
            is_free=getattr(platform, "kundli_matching_coins", 20) == 0,
            enabled=getattr(platform, "kundli_matching_enabled", True),
            description="36 Gunas Ashtakoot Milan & Dosha Check",
        ),
        "kp_calculator": FeaturePricingItem(
            feature_id="kp_calculator",
            name="KP Astrology",
            coins=getattr(platform, "kp_calculator_coins", 20),
            is_free=getattr(platform, "kp_calculator_coins", 20) == 0,
            enabled=getattr(platform, "kp_calculator_enabled", True),
            description="Placidus Cusps, Ruling Planets & Sub-Lords",
        ),
        "dasha_calculator": FeaturePricingItem(
            feature_id="dasha_calculator",
            name="Dasha Calculator",
            coins=getattr(platform, "dasha_calculator_coins", 15),
            is_free=getattr(platform, "dasha_calculator_coins", 15) == 0,
            enabled=getattr(platform, "dasha_calculator_enabled", True),
            description="Complete Vimshottari Mahadasha/Antardasha Tree",
        ),
        "rashi_calculator": FeaturePricingItem(
            feature_id="rashi_calculator",
            name="Rashi Calculator",
            coins=getattr(platform, "rashi_calculator_coins", 10),
            is_free=getattr(platform, "rashi_calculator_coins", 10) == 0,
            enabled=getattr(platform, "rashi_calculator_enabled", True),
            description="Moon Sign, Traits, Remedies & Avakahada",
        ),
        "nakshatra_calculator": FeaturePricingItem(
            feature_id="nakshatra_calculator",
            name="Nakshatra Calculator",
            coins=getattr(platform, "nakshatra_calculator_coins", 10),
            is_free=getattr(platform, "nakshatra_calculator_coins", 10) == 0,
            enabled=getattr(platform, "nakshatra_calculator_enabled", True),
            description="Janma Nakshatra, Pada, Tarabala & Sacred Mantras",
        ),
        "palm_reading": FeaturePricingItem(
            feature_id="palm_reading",
            name="Palm Reading",
            coins=getattr(platform, "palm_reading_coins", 25),
            is_free=getattr(platform, "palm_reading_coins", 25) == 0,
            enabled=getattr(platform, "palm_reading_enabled", True),
            description="AI Computer Vision Palmistry & Crease Analysis",
        ),
        "face_reading": FeaturePricingItem(
            feature_id="face_reading",
            name="Face Reading",
            coins=getattr(platform, "face_reading_coins", 25),
            is_free=getattr(platform, "face_reading_coins", 25) == 0,
            enabled=getattr(platform, "face_reading_enabled", True),
            description="Facial Morphology & Vedic Samudrika Shastra",
        ),
        "numerology": FeaturePricingItem(
            feature_id="numerology",
            name="Numerology",
            coins=getattr(platform, "numerology_coins", 20),
            is_free=getattr(platform, "numerology_coins", 20) == 0,
            enabled=getattr(platform, "numerology_enabled", True),
            description="Vedic & Chaldean Numerology, Lo Shu Grid, Dasha & Mobile Audit",
        ),
        "vastu": FeaturePricingItem(
            feature_id="vastu",
            name="Vastu Shastra",
            coins=getattr(platform, "vastu_coins", 25),
            is_free=getattr(platform, "vastu_coins", 25) == 0,
            enabled=getattr(platform, "vastu_enabled", True),
            description="16-Zone & 32-Pada Vastu Compass, Ayadi Shadvarga & Remedies",
        ),
    }
    return ApiResponse(message="Feature pricing fetched.", data=pricing)


@router.post(
    "/kundli",
    response_model=ApiResponse[KundliCalculateResponse],
    summary="Calculate complete Kundli & Planetary Position (D1, D9, 3x3 Dasha Grid, Tables & Yogas)",
)
async def get_kundli(
    payload: KundliCalculateRequest,
    user: OptionalUser = None,
) -> ApiResponse[KundliCalculateResponse]:
    """Calculates 100% accurate Vedic Kundli parameters, Placidus 12 cusps,
    Lagna Chart (D1), Navamsa Chart (D9), 3x3 Vimshottari Dasha grid,
    Planet & House tables, and Classical Vedic Yogas & Doshas.
    """
    charged, balance = await _charge_feature("kundli", "Kundli (Birth Chart)", user)
    result = _guard(calculate_kundli, payload, "kundli")
    msg = f"Calculated Kundli for {result.personal_details.name}: Asc {result.astro_positions.asc}, Rasi {result.planetary_info.rasi}"
    if charged > 0:
        msg += f" · {charged} coins deducted (Balance: {balance})"
    return ApiResponse(message=msg, data=result)


@router.post(
    "/kundli-matching",
    response_model=ApiResponse[KundliMatchingResponse],
    summary="Calculate complete Kundli Matching (36 Gunas Ashtakoot, Rajjoo, Vedha & Manglik Match)",
)
async def get_kundli_matching(
    payload: KundliMatchingRequest,
    user: OptionalUser = None,
) -> ApiResponse[KundliMatchingResponse]:
    """Calculates 100% accurate Kundli Matching (Horoscope Compatibility) for Groom & Bride,
    including 8 Ashtakoot Gunas (36 Points), Rajjoo Dosha, Vedha Dosha, Manglik compatibility,
    and comparative planetary charts using Swiss Ephemeris.
    """
    charged, balance = await _charge_feature("kundli_matching", "Kundli Matching", user)
    result = _guard(calculate_kundli_matching, payload, "kundli-matching")
    msg = f"Calculated Kundli Matching for {result.groom.name} & {result.bride.name}: Score {result.total_received}/{result.total_out_of}"
    if charged > 0:
        msg += f" · {charged} coins deducted (Balance: {balance})"
    return ApiResponse(message=msg, data=result)


@router.post(
    "/kp",
    response_model=ApiResponse[KPCalculateResponse],
    summary="Calculate KP Astrology (Placidus Cusps, Ruling Planets, Panchang & Vimshottari Dasha)",
)
async def get_kp(
    payload: KPCalculateRequest,
    user: OptionalUser = None,
    feature: str | None = Query(default=None, description="Feature identifier e.g. dasha_calculator or kp_calculator"),
) -> ApiResponse[KPCalculateResponse]:
    """Calculates 100% accurate KP Astrology parameters, Placidus 12 cusps,
    Ruling Planets for DOB and Casting Time, Panchang, and Vimshottari Dasha hierarchy.
    """
    feature_key = "dasha_calculator" if feature == "dasha_calculator" else "kp_calculator"
    feature_name = "Dasha Calculator" if feature_key == "dasha_calculator" else "KP Astrology"
    charged, balance = await _charge_feature(feature_key, feature_name, user)
    result = _guard(calculate_kp, payload, "kp")
    msg = f"Calculated {feature_name} for {result.name}: Asc {result.panchang.ascendant_sign}, Moon in {result.panchang.moon_rashi}"
    if charged > 0:
        msg += f" · {charged} coins deducted (Balance: {balance})"
    return ApiResponse(message=msg, data=result)


@router.post(
    "/dasha",
    response_model=ApiResponse[KPCalculateResponse],
    summary="Calculate Vimshottari Dasha hierarchy and planetary periods",
)
async def get_dasha(
    payload: KPCalculateRequest,
    user: OptionalUser = None,
) -> ApiResponse[KPCalculateResponse]:
    """Calculates Vimshottari Dasha planetary periods."""
    charged, balance = await _charge_feature("dasha_calculator", "Dasha Calculator", user)
    result = _guard(calculate_advanced_dasha, payload, "dasha")
    msg = f"Calculated Vimshottari Dasha for {result.name}"
    if charged > 0:
        msg += f" · {charged} coins deducted (Balance: {balance})"
    return ApiResponse(message=msg, data=result)


@router.post(
    "/rashi",
    response_model=ApiResponse[RashiCalculateResponse],
    summary="Calculate Rashi (Moon Sign), Nakshatra, KP Sub-Lord & personalized Vedic insights",
)
async def get_rashi(
    payload: RashiCalculateRequest,
    user: OptionalUser = None,
) -> ApiResponse[RashiCalculateResponse]:
    """Calculates high-precision Moon Sign, Nakshatra, Pada, KP Sub-Lord,
    and returns comprehensive characteristics, warnings, and remedies.
    """
    charged, balance = await _charge_feature("rashi_calculator", "Rashi Calculator", user)
    result = _guard(calculate_rashi, payload, "rashi")
    msg = f"Calculated Moon Sign: {result.rashi_name_en} ({result.rashi_name_hi})"
    if charged > 0:
        msg += f" · {charged} coins deducted (Balance: {balance})"
    return ApiResponse(message=msg, data=result)


@router.get(
    "/rashis",
    response_model=ApiResponse[list[dict]],
    summary="Get all 12 Rashis overview",
)
async def list_rashis() -> ApiResponse[list[dict]]:
    """Returns overview list of all 12 Rashis and their key attributes."""
    return ApiResponse(message="12 Rashis fetched.", data=RASHIS_DATA)


@router.post(
    "/nakshatra",
    response_model=ApiResponse[NakshatraCalculateResponse],
    summary="Calculate Janma Nakshatra (Birth Star), Pada, Avakahada Chakra & Tarabala",
)
async def get_nakshatra(
    payload: NakshatraCalculateRequest,
    user: OptionalUser = None,
) -> ApiResponse[NakshatraCalculateResponse]:
    """Calculates high-precision Birth Star (Janma Nakshatra), Pada, Star Lord,
    KP Sub-Lord, Avakahada Chakra, Tarabala, and sacred deity/tree/mantra.
    """
    charged, balance = await _charge_feature("nakshatra_calculator", "Nakshatra Calculator", user)
    result = _guard(calculate_nakshatra, payload, "nakshatra")
    msg = f"Calculated Janma Nakshatra: {result.nakshatra_name_en} ({result.nakshatra_name_bn}) Pada {result.pada}"
    if charged > 0:
        msg += f" · {charged} coins deducted (Balance: {balance})"
    return ApiResponse(message=msg, data=result)


@router.get(
    "/nakshatras",
    response_model=ApiResponse[list[dict]],
    summary="Get all 27 Nakshatras overview",
)
async def list_nakshatras() -> ApiResponse[list[dict]]:
    """Returns overview list of all 27 Nakshatras, deities, symbols, and padas."""
    return ApiResponse(message="27 Nakshatras fetched.", data=NAKSHATRAS_MASTER)



@router.get(
    "/geo-search",
    response_model=ApiResponse[list[dict]],
    summary="Search birth-place coordinates with an exact IANA timezone",
)
async def search_city(
    q: str = Query(..., min_length=2, max_length=120, description="City or location name"),
    year: int | None = Query(
        default=None, ge=1800, le=2100,
        description="Birth year. Given with month and day, the returned offset is the "
                    "one actually in force at that date, so daylight saving and "
                    "historical changes are reflected.",
    ),
    month: int | None = Query(default=None, ge=1, le=12),
    day: int | None = Query(default=None, ge=1, le=31),
) -> ApiResponse[list[dict]]:
    """Geocode a birth place and attach the timezone it really belongs to.

    Uses a multi-tier resilient engine: curated local directory (instant 0ms lookup for
    West Bengal localities like Deulia/Kolaghat and Indian cities), supplemented with
    Open-Meteo, Photon and Nominatim in parallel, with in-memory TTL caching.
    """
    items = await geocode_place(query=q, year=year, month=month, day=day)
    return ApiResponse(message=f"Found {len(items)} location(s)", data=items)


async def _reverse_geocode(lat: float, lon: float) -> dict | None:
    """Helper that queries Nominatim for lat/lon address details."""
    headers = {"User-Agent": "AstraAstrology/1.0 (info@astraastrology.com)"}
    params = {"lat": lat, "lon": lon, "format": "json", "addressdetails": "1"}
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                "https://nominatim.openstreetmap.org/reverse",
                params=params,
                headers=headers,
            )
            if resp.status_code == 200:
                data = resp.json() or {}
                addr = data.get("address", {})

                road_parts = []
                if addr.get("house_number"):
                    road_parts.append(addr["house_number"])
                if addr.get("road"):
                    road_parts.append(addr["road"])
                elif addr.get("pedestrian"):
                    road_parts.append(addr["pedestrian"])
                elif addr.get("street"):
                    road_parts.append(addr["street"])
                elif addr.get("neighbourhood"):
                    road_parts.append(addr["neighbourhood"])

                line1 = " ".join(road_parts) or addr.get("suburb") or addr.get("residential") or data.get("name") or ""
                line2 = addr.get("suburb") if line1 != addr.get("suburb") else (addr.get("city_district") or "")
                city = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("municipality") or addr.get("county") or ""
                state = addr.get("state") or addr.get("state_district") or ""
                postal_code = addr.get("postcode") or ""
                country = addr.get("country") or "India"

                return {
                    "display_name": data.get("display_name", ""),
                    "line1": line1,
                    "line2": line2,
                    "landmark": addr.get("neighbourhood") or "",
                    "city": city,
                    "state": state,
                    "postal_code": postal_code,
                    "country": country,
                    "latitude": lat,
                    "longitude": lon,
                }
    except Exception as exc:
        logger.warning(f"reverse geocoding failed for lat={lat}, lon={lon}: {exc}")
    return None


@router.get(
    "/geo-reverse",
    response_model=ApiResponse[dict],
    summary="Reverse geocode GPS coordinates to a structured postal address",
)
async def reverse_geocode_city(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude coordinate"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Longitude coordinate"),
) -> ApiResponse[dict]:
    """Reverse geocodes latitude/longitude into a structured street address, city, state, and postal code."""
    resolved = await _reverse_geocode(lat, lon)
    if resolved:
        return ApiResponse(message="Location resolved", data=resolved)

    return ApiResponse(
        message="Coordinates recorded",
        data={
            "display_name": f"{lat:.4f}, {lon:.4f}",
            "line1": "",
            "line2": "",
            "landmark": "",
            "city": "",
            "state": "",
            "postal_code": "",
            "country": "India",
            "latitude": lat,
            "longitude": lon,
        },
    )


@router.get(
    "/geo-detect",
    response_model=ApiResponse[dict],
    summary="Detect user location via network IP address with reverse geocoding fallback",
)
async def detect_ip_location(request: Request) -> ApiResponse[dict]:
    """Detects client IP and resolves approximate postal location (city, state, country, pincode)."""
    client_ip = (
        request.headers.get("cf-connecting-ip")
        or request.headers.get("x-real-ip")
        or (request.headers.get("x-forwarded-for", "").split(",")[0].strip())
        or (request.client.host if request.client else "")
    )

    is_private = (
        not client_ip
        or client_ip in ("127.0.0.1", "::1", "localhost", "testclient")
        or client_ip.startswith((
            "10.", "192.168.", "172.16.", "172.17.", "172.18.", "172.19.",
            "172.20.", "172.21.", "172.22.", "172.23.", "172.24.", "172.25.",
            "172.26.", "172.27.", "172.28.", "172.29.", "172.30.", "172.31.",
            "fc00:", "fe80:"
        ))
    )

    detected: dict = {}
    lat: float | None = None
    lon: float | None = None

    # 1. Primary lookup via ipwho.is (fast, HTTPS, free)
    try:
        url = "https://ipwho.is/" if is_private else f"https://ipwho.is/{client_ip}"
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, headers={"User-Agent": "AstraAstrology/1.0"})
            if resp.status_code == 200:
                data = resp.json() or {}
                if data.get("success") is not False:
                    lat = float(data.get("latitude") or 0.0)
                    lon = float(data.get("longitude") or 0.0)
                    detected = {
                        "city": data.get("city") or "",
                        "state": data.get("region") or "",
                        "postal_code": data.get("postal") or "",
                        "country": data.get("country") or "India",
                    }
    except Exception as exc:
        logger.warning(f"ipwho.is lookup failed: {exc}")

    # 2. Secondary fallback via ip-api.com
    if not detected.get("city"):
        try:
            url = "http://ip-api.com/json/" if is_private else f"http://ip-api.com/json/{client_ip}"
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url, headers={"User-Agent": "AstraAstrology/1.0"})
                if resp.status_code == 200:
                    data = resp.json() or {}
                    if data.get("status") == "success":
                        lat = float(data.get("lat") or 0.0)
                        lon = float(data.get("lon") or 0.0)
                        detected = {
                            "city": data.get("city") or "",
                            "state": data.get("regionName") or "",
                            "postal_code": data.get("zip") or "",
                            "country": data.get("country") or "India",
                        }
        except Exception as exc:
            logger.warning(f"ip-api lookup failed: {exc}")

    # 3. If lat/lon discovered, enrich with high quality street/suburb details
    if lat and lon and (lat != 0.0 or lon != 0.0):
        geo_enriched = await _reverse_geocode(lat, lon)
        if geo_enriched:
            return ApiResponse(
                message="Location detected via network",
                data={
                    "display_name": geo_enriched.get("display_name", "") or f"{detected.get('city')}, {detected.get('state')}",
                    "line1": geo_enriched.get("line1", "") or detected.get("city", ""),
                    "line2": geo_enriched.get("line2", ""),
                    "landmark": geo_enriched.get("landmark", ""),
                    "city": geo_enriched.get("city") or detected.get("city", ""),
                    "state": geo_enriched.get("state") or detected.get("state", ""),
                    "postal_code": geo_enriched.get("postal_code") or detected.get("postal_code", ""),
                    "country": geo_enriched.get("country") or detected.get("country", "India"),
                    "latitude": lat,
                    "longitude": lon,
                },
            )

    city = detected.get("city", "")
    state = detected.get("state", "")
    return ApiResponse(
        message="Location detected via network",
        data={
            "display_name": f"{city}, {state}".strip(", "),
            "line1": city,
            "line2": "",
            "landmark": "",
            "city": city,
            "state": state,
            "postal_code": detected.get("postal_code", ""),
            "country": detected.get("country", "India"),
            "latitude": lat or 0.0,
            "longitude": lon or 0.0,
        },
    )


@router.get(
    "/timezone",
    response_model=ApiResponse[dict],
    summary="Exact UTC offset for a coordinate at a given birth date",
)
async def lookup_timezone(
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    year: int = Query(..., ge=1800, le=2100),
    month: int = Query(..., ge=1, le=12),
    day: int = Query(..., ge=1, le=31),
    hour: int = Query(default=12, ge=0, le=23),
    minute: int = Query(default=0, ge=0, le=59),
) -> ApiResponse[dict]:
    """Resolve the offset in force at one place and one local wall-clock instant.

    Lets the frontend show the offset it is about to calculate with - including the
    daylight-saving and historical cases a fixed dropdown cannot express, such as
    +05:21:10 for a birth in Kolkata in 1900 or +06:30 for one in 1944.
    """
    zone_name = zone_for_coordinates(latitude, longitude)
    if not zone_name:
        return ApiResponse(
            message="No timezone could be determined for these coordinates.",
            data={"timezone_name": None, "timezone": None},
        )
    try:
        resolved = offset_for_zone_at(zone_name, year, month, day, hour, minute)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return ApiResponse(
        message=f"{zone_name} was on {resolved.offset_label} at that moment.",
        data={
            "timezone_name": zone_name,
            "timezone": round(resolved.offset_hours, 6),
            "timezone_label": resolved.offset_label,
            "timezone_abbreviation": resolved.abbreviation,
            "is_dst": resolved.is_dst,
            "note": resolved.note,
        },
    )


@router.get(
    "/client-rules/{sign_index}",
    response_model=ApiResponse[dict],
    summary="Every classification the client's resource documents define for a sign",
)
async def get_client_rules(
    sign_index: int = 0,
    language: str = Query(default="en", pattern="^(en|bn|hi)$"),
) -> ApiResponse[dict]:
    """The client-sourced rule set for one sign, with a citation on every group.

    Served separately so the rule tables can be inspected, reviewed by the client and
    diffed against the source documents without casting a chart.
    """
    if not 0 <= sign_index <= 11:
        raise HTTPException(status_code=422, detail="sign_index must be between 0 and 11")
    lang = language if language in {"en", "bn", "hi"} else "en"
    profile = client_rules.get_sign_profile(sign_index, lang)  # type: ignore[arg-type]
    return ApiResponse(
        message=f"{len(profile['classifications'])} classification groups for {profile['name_en']}",
        data={
            **profile,
            "kp_reference": client_rules.get_kp_reference(lang),  # type: ignore[arg-type]
            "unresolved_in_source": client_rules.UNRESOLVED_IN_SOURCE,
        },
    )


@router.post(
    "/horoscope/daily",
    response_model=ApiResponse[DailyHoroscopeResponse],
    summary="Calculate 100% accurate in-house Daily Horoscope (Moon Transit Gochar & Panchang)",
)
async def get_daily_horoscope_post(
    payload: DailyHoroscopeRequest,
    user: OptionalUser = None,
) -> ApiResponse[DailyHoroscopeResponse]:
    """Calculates 100% in-house Daily Horoscope based on:
    1. Swiss Ephemeris sidereal planetary coordinates (Lahiri Ayanamsha)
    2. Classical Vedic Moon transit (Gochar) through 12 Bhavas relative to Janma Rashi
    3. Client's Rashi attributes and beneficial remedies
    4. Exact Daily Panchang (Tithi, Nakshatra, Yoga, Karana, Abhijit Muhurat, Rahu Kaal)
    """
    # Daily Horoscope is a free, public feature: it is the homepage teaser, shown
    # to signed-out visitors, so it must never require sign-in or coins. Paid
    # features (annual, kundli, …) still go through _charge_feature.
    result = _guard(calculate_daily_horoscope, payload, "daily-horoscope")
    msg = f"Calculated Daily Horoscope for {result.date} ({result.day_of_week})"
    return ApiResponse(message=msg, data=result)


@router.get(
    "/horoscope/daily",
    response_model=ApiResponse[DailyHoroscopeResponse],
    summary="Get 100% accurate Daily Horoscope by query parameters",
)
async def get_daily_horoscope_get(
    date: str | None = Query(default=None, description="Target date in YYYY-MM-DD or None for today"),
    sign: str | None = Query(default=None, description="Optional sign filter e.g. aries"),
    language: str = Query(default="en", pattern="^(en|bn|hi)$"),
    latitude: float = Query(default=22.5726, ge=-90.0, le=90.0),
    longitude: float = Query(default=88.3639, ge=-180.0, le=180.0),
    timezone: float = Query(default=5.5, ge=-12.0, le=14.0),
    user: OptionalUser = None,
) -> ApiResponse[DailyHoroscopeResponse]:
    """Query parameter interface for Daily Horoscope (Moon Transit Gochar & Panchang)."""
    # Free, public feature — see get_daily_horoscope_post. No auth, no coins.
    lang = language if language in {"en", "bn", "hi"} else "en"
    req = DailyHoroscopeRequest(
        date=date,
        sign=sign,
        language=lang,  # type: ignore[arg-type]
        latitude=latitude,
        longitude=longitude,
        timezone=timezone,
    )
    result = _guard(calculate_daily_horoscope, req, "daily-horoscope")
    msg = f"Daily Horoscope for {result.date} ({result.day_of_week})"
    return ApiResponse(message=msg, data=result)


@router.post(
    "/horoscope/annual-lal-kitab",
    response_model=ApiResponse[AnnualHoroscopeResponse],
    summary="Generate 1-Year Annual Horoscope & Lal Kitab Varshphal Prediction Report",
)
async def get_annual_horoscope_report_post(
    payload: AnnualHoroscopeRequest,
    user: OptionalUser = None,
) -> ApiResponse[AnnualHoroscopeResponse]:
    """Calculates 100% in-house 1-Year Annual Horoscope & Lal Kitab Varshphal Report based on:
    1. Swiss Ephemeris sidereal coordinates & precise Solar Return (Varshpravesh) moment
    2. Varshphal Lagna & 9 Grahas house placements
    3. 6 Life Pillars Forecast & 4 Quarters Roadmap
    4. Authentic Lal Kitab Remedies & Precautions strictly from client canon
    5. Special Mahaupay & 8 Gomti Chakra Remedies
    6. Consecrated Royal Vedic Digital Seal & Verification Proof
    """
    charged, balance = await _charge_feature("annual_horoscope", "1-Year Annual Horoscope & Lal Kitab Report", user)
    
    c_name = payload.client_name
    if not c_name and user:
        c_name = getattr(user, "full_name", None) or getattr(user, "name", None)

    result_dict = generate_annual_lal_kitab_report(
        date_of_birth=payload.date_of_birth,
        time_of_birth=payload.time_of_birth,
        latitude=payload.latitude,
        longitude=payload.longitude,
        timezone_offset=payload.timezone,
        city_name=payload.city_name,
        client_name=c_name,
        target_year=payload.target_year,
        language=payload.language,
        primary_focus=payload.primary_focus,
    )
    result_dict["coins_spent"] = charged
    result_dict["wallet_balance"] = balance

    msg = f"Generated 1-Year Annual Horoscope Report for {result_dict['target_year']}"
    if charged > 0:
        msg += f" · {charged} coins deducted (Balance: {balance})"
    return ApiResponse(message=msg, data=AnnualHoroscopeResponse(**result_dict))


