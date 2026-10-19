"""Face reading: availability, submitting a measurement, and the rule set."""

from typing import Annotated

from beanie import PydanticObjectId
from fastapi import APIRouter, Query, status

from app.api.dependencies import AdminUser, CurrentUser
from app.core.exceptions import NotFoundError
from app.models.face_reading import Condition, FaceReading, FaceRule
from app.schemas.common import ApiResponse
from app.schemas.face_reading import (
    FaceReadingAvailability,
    FaceReadingOut,
    ReadingSectionOut,
    RuleOut,
    RuleUpdate,
    SubmitReadingRequest,
)
from app.services import face_reading as service

router = APIRouter(prefix="/face-reading", tags=["face reading"])


def _out(reading: FaceReading) -> FaceReadingOut:
    return FaceReadingOut(
        id=str(reading.id),
        sections=[ReadingSectionOut(**s.model_dump()) for s in reading.sections],
        coins_charged=reading.coins_charged,
        quality=reading.quality,
        created_at=reading.created_at,
    )


@router.get(
    "/availability",
    response_model=ApiResponse[FaceReadingAvailability],
    summary="What a reading costs, and whether it is on",
)
async def availability(user: CurrentUser) -> ApiResponse[FaceReadingAvailability]:
    """Asked before the camera opens, so nobody is charged by surprise."""
    from app.services import settings as settings_service
    from app.services import wallet as wallet_service

    platform = await settings_service.get_settings()
    wallet = await wallet_service.get_or_create_wallet(user.id)

    return ApiResponse(
        message="Availability fetched.",
        data=FaceReadingAvailability(
            enabled=platform.face_reading_enabled,
            coins=platform.face_reading_coins,
            balance_coins=wallet.balance_coins,
            can_afford=wallet.balance_coins >= platform.face_reading_coins,
            min_quality=service.MIN_QUALITY,
        ),
    )


@router.post(
    "",
    response_model=ApiResponse[FaceReadingOut],
    status_code=status.HTTP_201_CREATED,
    summary="Read a face from its measurements",
)
async def submit(
    payload: SubmitReadingRequest, user: CurrentUser
) -> ApiResponse[FaceReadingOut]:
    """Takes ratios, not a photograph.

    The face is measured on the device and never leaves it. What arrives here
    is about twenty numbers, each already relative to the subject's own face.
    """
    reading = await service.create(
        user=user, measurements=payload.measurements, quality=payload.quality
    )
    return ApiResponse(message="Your reading is ready.", data=_out(reading))


@router.get(
    "/mine",
    response_model=ApiResponse[list[FaceReadingOut]],
    summary="My readings",
)
async def mine(user: CurrentUser) -> ApiResponse[list[FaceReadingOut]]:
    readings = await service.for_user(user.id)
    return ApiResponse(message="Readings fetched.", data=[_out(r) for r in readings])


@router.get(
    "/{reading_id}",
    response_model=ApiResponse[FaceReadingOut],
    summary="One reading",
)
async def one(reading_id: PydanticObjectId, user: CurrentUser) -> ApiResponse[FaceReadingOut]:
    reading = await FaceReading.get(reading_id)
    if reading is None or reading.user_id != user.id:
        raise NotFoundError("Reading not found.", error_code="reading_not_found")
    return ApiResponse(message="Reading fetched.", data=_out(reading))


# -------------------------------------------------------------------- admin
admin_router = APIRouter(prefix="/admin/face-reading", tags=["admin"])


@admin_router.get(
    "/rules",
    response_model=ApiResponse[list[RuleOut]],
    summary="Every rule, including disabled ones",
)
async def list_rules(
    admin: AdminUser,
    feature: Annotated[str | None, Query()] = None,
) -> ApiResponse[list[RuleOut]]:
    """This is the screen the client's corrections land on.

    Editing a row changes how every future reading is decided — no deploy, no
    code change. That is the point of keeping the rules here.
    """
    query = FaceRule.find(FaceRule.feature == feature) if feature else FaceRule.find_all()
    rules = await query.sort(+FaceRule.feature, -FaceRule.priority).to_list()
    return ApiResponse(
        message="Rules fetched.",
        data=[
            RuleOut(
                id=str(r.id),
                feature=r.feature,
                option=r.option,
                label=r.label,
                conditions=[c.model_dump() for c in r.conditions],
                meaning=r.meaning,
                area=r.area,
                priority=r.priority,
                is_default=r.is_default,
                enabled=r.enabled,
                reviewed=r.reviewed,
            )
            for r in rules
        ],
    )


@admin_router.patch(
    "/rules/{rule_id}",
    response_model=ApiResponse[RuleOut],
    summary="Correct a rule — its wording, its thresholds, or both",
)
async def update_rule(
    rule_id: PydanticObjectId, payload: RuleUpdate, admin: AdminUser
) -> ApiResponse[RuleOut]:
    rule = await FaceRule.get(rule_id)
    if rule is None:
        raise NotFoundError("Rule not found.", error_code="rule_not_found")

    changes = payload.model_dump(exclude_unset=True)
    if "conditions" in changes and changes["conditions"] is not None:
        rule.conditions = [Condition(**c) for c in changes.pop("conditions")]
    else:
        changes.pop("conditions", None)

    for field, value in changes.items():
        if value is not None:
            setattr(rule, field, value)

    await rule.save()
    return ApiResponse(
        message="Rule updated.",
        data=RuleOut(
            id=str(rule.id),
            feature=rule.feature,
            option=rule.option,
            label=rule.label,
            conditions=[c.model_dump() for c in rule.conditions],
            meaning=rule.meaning,
            area=rule.area,
            priority=rule.priority,
            is_default=rule.is_default,
            enabled=rule.enabled,
            reviewed=rule.reviewed,
        ),
    )
