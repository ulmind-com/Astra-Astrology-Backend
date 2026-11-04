"""FastAPI router for Tarot Card Reading and Chrono-Astrological Resonance Engine."""

from typing import Any
from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencies import OptionalUser
from app.schemas.common import ApiResponse
from app.schemas.tarot import (
    DailyTarotRequest,
    SpreadConfig,
    TarotCardSchema,
    TarotDrawRequest,
    TarotDrawResponse,
)
from app.services.tarot import (
    draw_tarot_spread,
    get_all_cards,
    get_all_spreads,
    get_card_by_id,
    get_daily_tarot_card,
    get_spread_by_id,
)

router = APIRouter(prefix="/tarot", tags=["Tarot"])


@router.get(
    "/deck",
    response_model=ApiResponse[list[TarotCardSchema]],
    summary="Get complete Tarot deck with optional filtering",
)
async def get_deck_endpoint(
    arcana: str | None = Query(default=None, description="Filter by arcana: 'major' or 'minor'"),
    suit: str | None = Query(default=None, description="Filter by suit: 'wands', 'cups', 'swords', 'pentacles'"),
) -> ApiResponse[list[TarotCardSchema]]:
    """Return canonical 78-card Tarot deck."""
    cards = get_all_cards(arcana=arcana, suit=suit)
    return ApiResponse(
        success=True,
        message=f"Retrieved {len(cards)} tarot cards.",
        data=cards,
    )


@router.get(
    "/cards/{card_id}",
    response_model=ApiResponse[TarotCardSchema],
    summary="Get details of a specific Tarot card",
)
async def get_card_endpoint(card_id: str) -> ApiResponse[TarotCardSchema]:
    """Return card details by unique ID."""
    card = get_card_by_id(card_id)
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tarot card with ID '{card_id}' not found.",
        )
    return ApiResponse(
        success=True,
        message="Card retrieved successfully.",
        data=card,
    )


@router.get(
    "/spreads",
    response_model=ApiResponse[list[SpreadConfig]],
    summary="Get all available Tarot spread archetypes",
)
async def get_spreads_endpoint() -> ApiResponse[list[SpreadConfig]]:
    """Return all spread layouts (Daily, Past-Present-Future, Love, Career, Celtic Cross, etc.)."""
    spreads = get_all_spreads()
    return ApiResponse(
        success=True,
        message=f"Retrieved {len(spreads)} tarot spreads.",
        data=spreads,
    )


@router.get(
    "/spreads/{spread_id}",
    response_model=ApiResponse[SpreadConfig],
    summary="Get specific spread configuration by ID",
)
async def get_spread_details_endpoint(spread_id: str) -> ApiResponse[SpreadConfig]:
    """Return detailed spread architecture and position descriptions."""
    spread = get_spread_by_id(spread_id)
    if not spread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tarot spread with ID '{spread_id}' not found.",
        )
    return ApiResponse(
        success=True,
        message="Spread details retrieved successfully.",
        data=spread,
    )


@router.post(
    "/draw",
    response_model=ApiResponse[TarotDrawResponse],
    summary="Perform a Chrono-Astrological Tarot draw",
)
async def perform_tarot_draw_endpoint(
    payload: TarotDrawRequest,
    user: OptionalUser = None,
) -> ApiResponse[TarotDrawResponse]:
    """Perform an authentic Tarot reading with astrological harmony, elemental dignities, and Vedic remedy."""
    try:
        reading = draw_tarot_spread(payload)
        return ApiResponse(
            success=True,
            message="Tarot draw completed with cosmic harmonic resonance.",
            data=reading,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tarot draw failed: {str(exc)}",
        )


@router.post(
    "/daily",
    response_model=ApiResponse[TarotDrawResponse],
    summary="Get daily guidance Tarot card",
)
async def get_daily_tarot_endpoint(
    payload: DailyTarotRequest,
    user: OptionalUser = None,
) -> ApiResponse[TarotDrawResponse]:
    """Get the daily divine Tarot guidance card for today or specified date."""
    try:
        daily_reading = get_daily_tarot_card(payload)
        return ApiResponse(
            success=True,
            message="Daily Tarot guidance calculated successfully.",
            data=daily_reading,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Daily tarot calculation failed: {str(exc)}",
        )

