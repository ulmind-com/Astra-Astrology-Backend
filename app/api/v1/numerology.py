"""FastAPI router for Vedic, Chaldean, Name, and Mobile Numerology endpoints."""

from functools import lru_cache

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.dependencies import OptionalUser
from app.api.v1.astrology import charge_feature
from app.schemas.common import ApiResponse
from app.schemas.numerology import (
    BusinessNumerologyRequest,
    BusinessNumerologyResponse,
    MobileAnalysisResponse,
    MobileCompareRequest,
    MobileCompareResponse,
    MulankProfile,
    NameAnalysisResponse,
    NameCorrectionRequest,
    NameCorrectionResponse,
    NumerologyCalculateRequest,
    NumerologyCalculateResponse,
    VehicleBankAuditRequest,
    VehicleBankAuditResponse,
)
from app.services.astrology.numerology_engine import (
    MULANK_MASTER,
    audit_vehicle_bank_numerology,
    calculate_full_numerology,
    calculate_mobile_numerology,
    calculate_name_numerology,
    compare_mobile_numbers,
    correct_name_spelling,
    evaluate_business_numerology,
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
async def calculate_numerology_endpoint(
    payload: NumerologyCalculateRequest,
    user: OptionalUser = None,
) -> ApiResponse[NumerologyCalculateResponse]:
    """Calculates end-to-end Numerology report based strictly on client's authoritative resource documents."""
    charged, balance = await charge_feature("numerology", "Numerology", user)
    try:
        data = calculate_full_numerology(
            full_name=payload.full_name,
            birth_date_str=payload.birth_date,
            gender=payload.gender,
            mobile_number=payload.mobile_number,
            prediction_year=payload.prediction_year,
        )
        msg = "Numerology analysis generated successfully."
        if charged > 0:
            msg += f" · {charged} coins deducted (Balance: {balance})"
        return ApiResponse(success=True, data=data, message=msg)
    except HTTPException:
        raise
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


@lru_cache(maxsize=16)
def _build_cached_mulank_profile(number: int) -> MulankProfile:
    raw = MULANK_MASTER[number]
    return MulankProfile(
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


@router.get(
    "/profile/{number}",
    response_model=ApiResponse[MulankProfile],
    summary="Get 20-field master profile for a Mulank (1-9)",
)
def get_mulank_profile_endpoint(number: int) -> ApiResponse[MulankProfile]:
    """Retrieves full 20-field master profile for Mulank number from client document NEW NUMRO.docx."""
    if number not in MULANK_MASTER:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Number must be between 1 and 9.")
    profile = _build_cached_mulank_profile(number)
    return ApiResponse(success=True, data=profile, message="Profile retrieved successfully.")


@router.post(
    "/name/correct",
    response_model=ApiResponse[NameCorrectionResponse],
    summary="Harmonize and correct name spelling to royal Chaldean compounds (19, 23, 37, 41, 46, 55)",
)
def correct_name_endpoint(payload: NameCorrectionRequest) -> ApiResponse[NameCorrectionResponse]:
    """Generates 1-click auspicious spelling alternatives and filters negative syllables."""
    try:
        data = correct_name_spelling(payload.name, payload.mulank, payload.bhagyank, payload.target_compound)
        return ApiResponse(success=True, data=data, message="Name spelling harmonized successfully.")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Name correction failed: {str(exc)}",
        ) from exc


@router.post(
    "/mobile/compare",
    response_model=ApiResponse[MobileCompareResponse],
    summary="Compare 2 to 6 mobile SIM numbers under 60%/40% dominance pair evaluation",
)
def compare_mobile_endpoint(payload: MobileCompareRequest) -> ApiResponse[MobileCompareResponse]:
    """Audits multiple mobile numbers, identifies best number and assigns grades (A+, A, B, C, D)."""
    try:
        data = compare_mobile_numbers(payload.numbers, payload.mulank, payload.bhagyank, payload.profession, payload.birth_date)
        return ApiResponse(success=True, data=data, message="Mobile numbers compared successfully.")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Mobile comparison failed: {str(exc)}",
        ) from exc


@router.post(
    "/business",
    response_model=ApiResponse[BusinessNumerologyResponse],
    summary="Evaluate Business / Brand Name Numerology (Industry suitability score & Founder harmony)",
)
def evaluate_business_endpoint(payload: BusinessNumerologyRequest) -> ApiResponse[BusinessNumerologyResponse]:
    """Evaluates business brand name Chaldean compound, industry fit, and founder birth harmony."""
    try:
        data = evaluate_business_numerology(payload.brand_name, payload.industry, payload.owner_mulank, payload.owner_bhagyank)
        return ApiResponse(success=True, data=data, message="Business numerology evaluated successfully.")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Business evaluation failed: {str(exc)}",
        ) from exc


@router.post(
    "/vehicle-bank",
    response_model=ApiResponse[VehicleBankAuditResponse],
    summary="Audit Vehicle License Plate or Bank Account Numerology for safety and wealth retention",
)
def audit_vehicle_bank_endpoint(payload: VehicleBankAuditRequest) -> ApiResponse[VehicleBankAuditResponse]:
    """Performs accident risk and wealth retention audit on vehicle plate or bank account digits."""
    try:
        data = audit_vehicle_bank_numerology(payload.input_string, payload.audit_type, payload.mulank, payload.bhagyank)
        return ApiResponse(success=True, data=data, message=f"{payload.audit_type.title()} audited successfully.")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vehicle/Bank audit failed: {str(exc)}",
        ) from exc

