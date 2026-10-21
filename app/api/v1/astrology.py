"""Astrology public endpoints: Rashi (Moon Sign) calculator and geocoding helper."""

import httpx
from fastapi import APIRouter, Query
from app.schemas.astrology import RashiCalculateRequest, RashiCalculateResponse
from app.schemas.common import ApiResponse
from app.services.astrology.calculator import calculate_rashi
from app.services.astrology.rashi_rules import RASHIS_DATA

router = APIRouter(prefix="/astrology", tags=["astrology"])


@router.post(
    "/rashi",
    response_model=ApiResponse[RashiCalculateResponse],
    summary="Calculate Rashi (Moon Sign), Nakshatra, KP Sub-Lord & personalized Vedic insights",
)
async def get_rashi(payload: RashiCalculateRequest) -> ApiResponse[RashiCalculateResponse]:
    """Calculates high-precision Moon Sign, Nakshatra, Pada, KP Sub-Lord,
    and returns comprehensive characteristics, warnings, and remedies.
    """
    result = calculate_rashi(payload)
    return ApiResponse(
        message=f"Calculated Moon Sign: {result.rashi_name_en} ({result.rashi_name_hi})",
        data=result,
    )


@router.get(
    "/rashis",
    response_model=ApiResponse[list[dict]],
    summary="Get all 12 Rashis overview",
)
async def list_rashis() -> ApiResponse[list[dict]]:
    """Returns overview list of all 12 Rashis and their key attributes."""
    return ApiResponse(message="12 Rashis fetched.", data=RASHIS_DATA)


@router.get(
    "/geo-search",
    response_model=ApiResponse[list[dict]],
    summary="Search city coordinates and timezone",
)
async def search_city(
    q: str = Query(..., min_length=2, max_length=100, description="City or location name"),
) -> ApiResponse[list[dict]]:
    """Free geocoding search for birth place input using OpenStreetMap Nominatim / Photon."""
    headers = {"User-Agent": "AstraAstrology/1.0 (info@astraastrology.com)"}
    url = f"https://nominatim.openstreetmap.org/search?q={q}&format=json&addressdetails=1&limit=6"

    items: list[dict] = []
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                raw_data = resp.json()
                for d in raw_data:
                    lat = float(d.get("lat", 0.0))
                    lon = float(d.get("lon", 0.0))

                    # Approximate timezone offset based on longitude (+5.5 for India ~68E to 97E)
                    approx_tz = 5.5
                    if lon >= 68.0 and lon <= 97.5 and lat >= 6.0 and lat <= 37.0:
                        approx_tz = 5.5
                    else:
                        # rough offset from longitude (15 degrees = 1 hour)
                        approx_tz = round(lon / 15.0 * 2) / 2.0

                    items.append(
                        {
                            "display_name": d.get("display_name", ""),
                            "latitude": lat,
                            "longitude": lon,
                            "timezone": approx_tz,
                            "country": d.get("address", {}).get("country", ""),
                            "state": d.get("address", {}).get("state", ""),
                            "city": (
                                d.get("address", {}).get("city")
                                or d.get("address", {}).get("town")
                                or d.get("address", {}).get("village")
                                or ""
                            ),
                        }
                    )
    except Exception:
        # Graceful fallback if external geocoding network times out
        pass

    return ApiResponse(message=f"Found {len(items)} location(s)", data=items)
