"""Platform settings an admin controls at runtime.

Right now that is the coin rate. It decides how many coins people get for their
money, so every change is recorded against the admin who made it.
"""

from typing import Annotated

from fastapi import APIRouter, Query

from app.api.dependencies import AdminUser
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.wallet import (
    CoinRateChangeOut,
    CoinRateUpdate,
    ConsultationDefaultsUpdate,
    FeaturePricingUpdate,
    PlatformSettingsOut,
    RechargeLimitsUpdate,
)
from app.services import settings as settings_service

router = APIRouter(prefix="/admin/settings", tags=["admin: settings"])


def _out(doc) -> PlatformSettingsOut:
    return PlatformSettingsOut(
        coins_per_rupee=doc.coins_per_rupee,
        min_recharge_paise=doc.min_recharge_paise,
        max_recharge_paise=doc.max_recharge_paise,
        default_chat_coins_per_minute=doc.default_chat_coins_per_minute,
        default_call_coins_per_minute=doc.default_call_coins_per_minute,
        default_video_coins_per_minute=doc.default_video_coins_per_minute,
        default_commission_percent=doc.default_commission_percent,
        min_session_minutes=doc.min_session_minutes,
        max_session_minutes=doc.max_session_minutes,
        chat_retention_days=doc.chat_retention_days,
        appointment_commission_percent=doc.appointment_commission_percent,
        min_appointment_minutes=doc.min_appointment_minutes,
        max_appointment_minutes=doc.max_appointment_minutes,
        appointment_booking_days_ahead=doc.appointment_booking_days_ahead,
        face_reading_coins=getattr(doc, "face_reading_coins", 25),
        face_reading_enabled=getattr(doc, "face_reading_enabled", True),
        palm_reading_coins=getattr(doc, "palm_reading_coins", 25),
        palm_reading_enabled=getattr(doc, "palm_reading_enabled", True),
        daily_horoscope_coins=getattr(doc, "daily_horoscope_coins", 0),
        daily_horoscope_enabled=getattr(doc, "daily_horoscope_enabled", True),
        kundli_coins=getattr(doc, "kundli_coins", 20),
        kundli_enabled=getattr(doc, "kundli_enabled", True),
        kundli_matching_coins=getattr(doc, "kundli_matching_coins", 20),
        kundli_matching_enabled=getattr(doc, "kundli_matching_enabled", True),
        kp_calculator_coins=getattr(doc, "kp_calculator_coins", 20),
        kp_calculator_enabled=getattr(doc, "kp_calculator_enabled", True),
        dasha_calculator_coins=getattr(doc, "dasha_calculator_coins", 15),
        dasha_calculator_enabled=getattr(doc, "dasha_calculator_enabled", True),
        rashi_calculator_coins=getattr(doc, "rashi_calculator_coins", 10),
        rashi_calculator_enabled=getattr(doc, "rashi_calculator_enabled", True),
        nakshatra_calculator_coins=getattr(doc, "nakshatra_calculator_coins", 10),
        nakshatra_calculator_enabled=getattr(doc, "nakshatra_calculator_enabled", True),
        numerology_coins=getattr(doc, "numerology_coins", 20),
        numerology_enabled=getattr(doc, "numerology_enabled", True),
        vastu_coins=getattr(doc, "vastu_coins", 25),
        vastu_enabled=getattr(doc, "vastu_enabled", True),
        updated_at=doc.updated_at,
    )


@router.get("", response_model=ApiResponse[PlatformSettingsOut], summary="Platform settings")
async def read_settings(_: AdminUser) -> ApiResponse[PlatformSettingsOut]:
    doc = await settings_service.get_settings()
    return ApiResponse(
        message="Settings fetched.",
        data=_out(doc),
    )


@router.patch(
    "",
    response_model=ApiResponse[PlatformSettingsOut],
    summary="Change how many coins a rupee buys",
)
async def update_settings(
    payload: CoinRateUpdate, admin: AdminUser
) -> ApiResponse[PlatformSettingsOut]:
    doc = await settings_service.set_coins_per_rupee(
        rate=payload.coins_per_rupee, admin_id=admin.id, note=payload.note
    )
    return ApiResponse(
        message=(
            f"₹1 now buys {doc.coins_per_rupee} coin"
            f"{'s' if doc.coins_per_rupee != 1 else ''}. "
            "Coins already bought keep the rate they were bought at."
        ),
        data=_out(doc),
    )


@router.patch(
    "/recharge-limits",
    response_model=ApiResponse[PlatformSettingsOut],
    summary="Set the smallest and largest recharge",
)
async def update_recharge_limits(
    payload: RechargeLimitsUpdate, admin: AdminUser
) -> ApiResponse[PlatformSettingsOut]:
    doc = await settings_service.set_recharge_limits(
        min_paise=payload.min_recharge_paise,
        max_paise=payload.max_recharge_paise,
        admin_id=admin.id,
    )
    return ApiResponse(
        message=(
            f"Recharges are now ₹{doc.min_recharge_paise // 100} to "
            f"₹{doc.max_recharge_paise // 100}."
        ),
        data=_out(doc),
    )


@router.patch(
    "/consultation",
    response_model=ApiResponse[PlatformSettingsOut],
    summary="Set the default per-minute prices and commission",
)
async def update_consultation_defaults(
    payload: ConsultationDefaultsUpdate, admin: AdminUser
) -> ApiResponse[PlatformSettingsOut]:
    doc = await settings_service.set_consultation_defaults(
        changes=payload.model_dump(exclude_unset=True), admin_id=admin.id
    )
    return ApiResponse(
        message=(
            f"Chat {doc.default_chat_coins_per_minute}, call "
            f"{doc.default_call_coins_per_minute}, video "
            f"{doc.default_video_coins_per_minute} coins a minute · "
            f"{doc.default_commission_percent:g}% commission."
        ),
        data=_out(doc),
    )


@router.patch(
    "/feature-pricing",
    response_model=ApiResponse[PlatformSettingsOut],
    summary="Update coin pricing and enabled states for astrology features",
)
async def update_feature_pricing(
    payload: FeaturePricingUpdate, admin: AdminUser
) -> ApiResponse[PlatformSettingsOut]:
    doc = await settings_service.set_feature_pricing(
        changes=payload.model_dump(exclude_unset=True), admin_id=admin.id
    )
    return ApiResponse(
        message="Feature coin pricing updated successfully.",
        data=_out(doc),
    )


@router.get(
    "/coin-rate-history",
    response_model=ApiResponse[list[CoinRateChangeOut]],
    summary="Every change to the coin rate",
)
async def coin_rate_history(
    _: AdminUser, limit: Annotated[int, Query(ge=1, le=200)] = 50
) -> ApiResponse[list[CoinRateChangeOut]]:
    changes = await settings_service.rate_history(limit)
    admins = {
        u.id: u
        for u in await User.find(
            {"_id": {"$in": [c.changed_by for c in changes if c.changed_by]}}
        ).to_list()
    }
    return ApiResponse(
        message=f"{len(changes)} change(s).",
        data=[
            CoinRateChangeOut(
                from_rate=c.from_rate,
                to_rate=c.to_rate,
                changed_by=str(c.changed_by) if c.changed_by else None,
                changed_by_email=(
                    admins[c.changed_by].email if c.changed_by in admins else None
                ),
                note=c.note,
                created_at=c.created_at,
            )
            for c in changes
        ],
    )
