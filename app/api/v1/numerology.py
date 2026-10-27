"""FastAPI router for Vedic, Chaldean, Name, and Mobile Numerology endpoints."""

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.schemas.common import ApiResponse
from app.schemas.numerology import (
    MobileAnalysisResponse,
    MulankProfile,
    NameAnalysisResponse,
    NumerologyCalculateRequest,
    NumerologyCalculateResponse,
)
from app.services.astrology.numerology_engine import (
    MULANK_MASTER,
    calculate_full_numerology,
    calculate_mobile_numerology,
    calculate_name_numerology,
)

router = APIRouter(prefix="/numerology", tags=["Numerology"])


class NameOnlyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    mulank: int = Field(default=1, ge=1, le=9)
    bhagyank: int = Field(default=1, ge=1, le=9)


class MobileOnlyRequest(BaseModel):
    mobile_number: str = Field(..., min_length=10, max_length=20)
    mulank: int = Field(default=1, ge=1, le=9)
    bhagyank: int = Field(default=1, ge=1, le=9)
    birth_date: str = Field(default="", description="Optional birth date YYYY-MM-DD for resonance")


@router.post(
    "/calculate",
    response_model=ApiResponse[NumerologyCalculateResponse],
    summary="Calculate complete Vedic & Chaldean Numerology (Lo Shu Grid, Dasha, Name, Mobile)",
)
def calculate_numerology_endpoint(payload: NumerologyCalculateRequest) -> ApiResponse[NumerologyCalculateResponse]:
    """Calculates end-to-end Numerology report based strictly on client's authoritative resource documents."""
    try:
        data = calculate_full_numerology(
            full_name=payload.full_name,
            birth_date_str=payload.birth_date,
            gender=payload.gender,
            mobile_number=payload.mobile_number,
            prediction_year=payload.prediction_year,
        )
        return ApiResponse(success=True, data=data, message="Numerology analysis generated successfully.")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Numerology calculation failed: {str(exc)}",
        ) from exc


@router.post(
    "/name",
    response_model=ApiResponse[NameAnalysisResponse],
    summary="Analyze Name Numerology (Chaldean compound 1-100, syllables, letter sound vibrations)",
)
def analyze_name_endpoint(payload: NameOnlyRequest) -> ApiResponse[NameAnalysisResponse]:
    """Analyzes a name using Chaldean letter vibrations, negative syllable detection, and 4-tier harmony."""
    try:
        data = calculate_name_numerology(payload.name, payload.mulank, payload.bhagyank)
        return ApiResponse(success=True, data=data, message="Name numerology analyzed successfully.")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Name analysis failed: {str(exc)}",
        ) from exc


@router.post(
    "/mobile",
    response_model=ApiResponse[MobileAnalysisResponse],
    summary="Analyze Mobile Number (King Number, 60%/40% pairs, Sepharial grid & 16 L-shapes)",
)
def analyze_mobile_endpoint(payload: MobileOnlyRequest) -> ApiResponse[MobileAnalysisResponse]:
    """Audits a 10-digit mobile number using consecutive conjunctions, 60%/40% rule, and Sepharial grid."""
    try:
        data = calculate_mobile_numerology(payload.mobile_number, payload.mulank, payload.bhagyank, payload.birth_date)
        return ApiResponse(success=True, data=data, message="Mobile numerology audited successfully.")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Mobile analysis failed: {str(exc)}",
        ) from exc


@router.get(
    "/profile/{number}",
    response_model=ApiResponse[MulankProfile],
    summary="Get 20-field master profile for a Mulank (1-9)",
)
def get_mulank_profile_endpoint(number: int) -> ApiResponse[MulankProfile]:
    """Retrieves full 20-field master profile for Mulank number from client document NEW NUMRO.docx."""
    if number not in MULANK_MASTER:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Number must be between 1 and 9.")
    raw = MULANK_MASTER[number]
    profile = MulankProfile(
        number=number,
        planet=raw["planet"],
        planet_hi=raw["planet_hi"],
        deity=raw["deity"],
        metal=raw["metal"],
        colors=raw["colors"],
        unlucky_colors=raw["unlucky_colors"],
        direction=raw["direction"],
        lucky_numbers=raw["lucky_numbers"],
        unlucky_numbers=raw["unlucky_numbers"],
        beej_mantra=raw["beej_mantra"],
        jap_count=raw["jap_count"],
        gemstone=raw["gemstone"],
        lucky_days=raw["lucky_days"],
        lucky_months=raw["lucky_months"],
        grains_daan=raw["grains_daan"],
        health_traits=raw["health_traits"],
        profession=raw["profession"],
    )
    return ApiResponse(success=True, data=profile, message="Profile retrieved successfully.")
