"""Palm reading endpoints for availability, scanning, and readings history."""

import base64
from typing import Annotated

from beanie import PydanticObjectId
from fastapi import APIRouter, Query, Request, status
from loguru import logger

from app.api.dependencies import AdminUser, CurrentUser
from app.core.exceptions import BadRequestError, NotFoundError, ServiceUnavailableError
from app.models.enums import TransactionReason
from app.models.palm_reading import Condition, PalmReading, PalmRule
from app.schemas.common import ApiResponse
from app.schemas.palm_reading import (
    PalmMeasurementDetailOut,
    PalmQualityChecksOut,
    PalmReadingAvailability,
    PalmReadingOut,
    PalmRuleOut,
    PalmRuleUpdate,
    PalmScanBase64Request,
    PalmScanResponse,
    ReadingSectionOut,
    SubmitPalmReadingRequest,
)
from app.services import palm_reading as service
from app.services.palm_cv import QualityStatus, execute_palm_scan_pipeline

router = APIRouter(prefix="/palm-reading", tags=["palm reading"])


def _out(reading: PalmReading) -> PalmReadingOut:
    return PalmReadingOut(
        id=str(reading.id),
        hand_scanned=reading.hand_scanned,
        gender=reading.gender,
        sections=[ReadingSectionOut(**s.model_dump()) for s in reading.sections],
        coins_charged=reading.coins_charged,
        quality=reading.quality,
        visualization_image=reading.visualization_image,
        created_at=reading.created_at,
    )


@router.get(
    "/availability",
    response_model=ApiResponse[PalmReadingAvailability],
    summary="Check palm reading availability and pricing",
)
async def availability(user: CurrentUser) -> ApiResponse[PalmReadingAvailability]:
    from app.services import settings as settings_service
    from app.services import wallet as wallet_service

    platform = await settings_service.get_settings()
    wallet = await wallet_service.get_or_create_wallet(user.id)

    return ApiResponse(
        message="Palm reading availability fetched.",
        data=PalmReadingAvailability(
            enabled=platform.palm_reading_enabled,
            coins=platform.palm_reading_coins,
            balance_coins=wallet.balance_coins,
            can_afford=wallet.balance_coins >= platform.palm_reading_coins,
            min_quality=service.MIN_QUALITY,
            recommended_hand_male="left",
            recommended_hand_female="right",
        ),
    )


@router.post(
    "",
    response_model=ApiResponse[PalmReadingOut],
    status_code=status.HTTP_201_CREATED,
    summary="Create palm reading from on-device biometric measurements",
)
async def submit(
    payload: SubmitPalmReadingRequest, user: CurrentUser
) -> ApiResponse[PalmReadingOut]:
    reading = await service.create(
        user=user,
        hand_scanned=payload.hand_scanned,
        gender=payload.gender,
        measurements=payload.measurements,
        quality=payload.quality,
    )
    return ApiResponse(message="Your palm reading is ready.", data=_out(reading))


@router.post(
    "/scan",
    response_model=ApiResponse[PalmScanResponse],
    summary="MediaPipe + OpenCV biometric palm scan and Vedic Samudrik Shastra reading",
)
async def scan(user: CurrentUser, request: Request) -> ApiResponse[PalmScanResponse]:
    """Processes a palm image through the MediaPipe Hand Landmarker + OpenCV ridge pipeline."""
    from app.services import settings as settings_service
    from app.services import wallet as wallet_service

    platform = await settings_service.get_settings()
    if not platform.palm_reading_enabled:
        raise ServiceUnavailableError(
            "Palm reading is currently disabled.", error_code="palm_reading_disabled"
        )

    wallet = await wallet_service.get_or_create_wallet(user.id)
    if platform.palm_reading_coins > 0 and wallet.balance_coins < platform.palm_reading_coins:
        raise BadRequestError(
            f"Insufficient coins. You have {wallet.balance_coins} coins, but palm reading requires {platform.palm_reading_coins} coins.",
            error_code="insufficient_coins",
        )

    content_type = request.headers.get("content-type", "")
    raw_bytes: bytes = b""
    user_gender: str = getattr(user, "gender", "male") or "male"
    user_hand: str = "auto"

    if "application/json" in content_type:
        body = await request.json()
        img_b64 = body.get("image", "")
        user_gender = body.get("gender", user_gender)
        user_hand = body.get("hand", "auto")
        if not img_b64:
            raise BadRequestError("Missing 'image' in payload.", error_code="empty_image")
        if "," in img_b64:
            img_b64 = img_b64.split(",", 1)[1]
        try:
            raw_bytes = base64.b64decode(img_b64)
        except Exception:
            raise BadRequestError("Invalid base64 image data.", error_code="bad_image_data")
    elif "multipart/form-data" in content_type:
        form = await request.form()
        file_obj = form.get("file") or form.get("image")
        if file_obj is None or not hasattr(file_obj, "read"):
            raise BadRequestError("No image file provided.", error_code="missing_file")
        raw_bytes = await file_obj.read()
        user_gender = str(form.get("gender", user_gender))
        user_hand = str(form.get("hand", "auto"))
    else:
        raw_bytes = await request.body()

    if not raw_bytes:
        raise BadRequestError("Empty image payload received.", error_code="empty_payload")

    # Execute OpenCV & MediaPipe Palm Pipeline
    try:
        cv_result = execute_palm_scan_pipeline(
            raw_image_bytes=raw_bytes,
            gender=user_gender,
            hand=user_hand,
        )
    except Exception as exc:
        logger.exception("Palm CV scanning pipeline failed: {}", exc)
        raise BadRequestError(f"Palm scanning failed: {str(exc)}", error_code="cv_pipeline_error")

    qc = cv_result.quality_checks
    checks_out = PalmQualityChecksOut(
        is_valid=bool(qc.get("is_valid", True)),
        status=str(qc.get("status", "ACCEPTED")),
        hand_count=int(qc.get("hand_count", 1)),
        detected_hand=qc.get("detected_hand"),
        expected_hand=str(qc.get("expected_hand", "left")),
        is_hand_matched=bool(qc.get("is_hand_matched", True)),
        hand_coverage_pct=round(float(qc.get("hand_coverage_pct", 0.0)), 2),
        blur_score=round(float(qc.get("blur_score", 0.0)), 2),
        brightness_mean=round(float(qc.get("brightness_mean", 0.0)), 2),
        contrast_std=round(float(qc.get("contrast_std", 0.0)), 2),
        fingers_extended=bool(qc.get("fingers_extended", True)),
        issues=list(qc.get("issues", [])),
        recommendations=list(qc.get("recommendations", [])),
    )

    # If rejected: do NOT charge and do NOT generate reading
    if cv_result.status == QualityStatus.REJECTED:
        return ApiResponse(
            message=cv_result.error_message or "Palm capture did not meet requirements.",
            data=PalmScanResponse(
                scan_id=cv_result.scan_id,
                status=QualityStatus.REJECTED.value,
                quality_score=cv_result.quality_score,
                quality_checks=checks_out,
                detected_hand=cv_result.detected_hand,
                expected_hand=cv_result.expected_hand,
                is_hand_matched=cv_result.is_hand_matched,
                measurements={},
                measurement_details={},
                visualization_image=None,
                reading=None,
                coins_charged=0,
                processing_duration_ms=cv_result.processing_duration_ms,
                warnings=cv_result.warnings,
                error_message=cv_result.error_message,
            ),
        )

    # Compose Vedic reading
    sections = await service.compose(cv_result.measurements)
    if not sections:
        raise ServiceUnavailableError(
            "Palm reading rules are currently unavailable. Please try again shortly.",
            error_code="rules_unavailable",
        )

    reading = PalmReading(
        user_id=user.id,
        hand_scanned=cv_result.detected_hand.lower() if cv_result.detected_hand else cv_result.expected_hand,
        gender=user_gender,
        measurements=cv_result.measurements,
        sections=sections,
        coins_charged=platform.palm_reading_coins,
        quality=round(cv_result.quality_score, 3),
        visualization_image=cv_result.visualization_image,
    )
    await reading.insert()

    if platform.palm_reading_coins > 0:
        try:
            await wallet_service.debit(
                user_id=user.id,
                amount_coins=platform.palm_reading_coins,
                reason=TransactionReason.CONSULTATION,
                idempotency_key=f"palm-reading:{reading.id}",
                note="Palm reading scan",
            )
        except Exception:
            await reading.delete()
            raise

    details_out = {
        k: PalmMeasurementDetailOut(
            name=v.get("name", k),
            value=v.get("value", 0.0),
            description=v.get("description", ""),
            status=v.get("status", "available"),
        )
        for k, v in cv_result.measurement_details.items()
    }

    return ApiResponse(
        message="Palm scanning complete and reading generated.",
        data=PalmScanResponse(
            scan_id=cv_result.scan_id,
            status=cv_result.status.value,
            quality_score=cv_result.quality_score,
            quality_checks=checks_out,
            detected_hand=cv_result.detected_hand,
            expected_hand=cv_result.expected_hand,
            is_hand_matched=cv_result.is_hand_matched,
            measurements=cv_result.measurements,
            measurement_details=details_out,
            visualization_image=cv_result.visualization_image,
            reading=_out(reading),
            coins_charged=reading.coins_charged,
            processing_duration_ms=cv_result.processing_duration_ms,
            warnings=cv_result.warnings,
            error_message=None,
        ),
    )


@router.get(
    "/mine",
    response_model=ApiResponse[list[PalmReadingOut]],
    summary="User's past palm readings",
)
async def mine(user: CurrentUser) -> ApiResponse[list[PalmReadingOut]]:
    readings = await service.for_user(user.id)
    return ApiResponse(message="Readings fetched.", data=[_out(r) for r in readings])


@router.get(
    "/{reading_id}",
    response_model=ApiResponse[PalmReadingOut],
    summary="Get one specific palm reading",
)
async def one(reading_id: PydanticObjectId, user: CurrentUser) -> ApiResponse[PalmReadingOut]:
    reading = await PalmReading.get(reading_id)
    if reading is None or reading.user_id != user.id:
        raise NotFoundError("Palm reading not found.", error_code="reading_not_found")
    return ApiResponse(message="Reading fetched.", data=_out(reading))


# -------------------------------------------------------------------- admin
admin_router = APIRouter(prefix="/admin/palm-reading", tags=["admin"])


@admin_router.get(
    "/rules",
    response_model=ApiResponse[list[PalmRuleOut]],
    summary="List all palm reading rules",
)
async def list_rules(
    admin: AdminUser,
    feature: Annotated[str | None, Query()] = None,
) -> ApiResponse[list[PalmRuleOut]]:
    query = PalmRule.find(PalmRule.feature == feature) if feature else PalmRule.find_all()
    rules = await query.sort(+PalmRule.feature, -PalmRule.priority).to_list()
    return ApiResponse(
        message="Rules fetched.",
        data=[
            PalmRuleOut(
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
    response_model=ApiResponse[PalmRuleOut],
    summary="Update palm reading rule thresholds or interpretation",
)
async def update_rule(
    rule_id: PydanticObjectId, payload: PalmRuleUpdate, admin: AdminUser
) -> ApiResponse[PalmRuleOut]:
    rule = await PalmRule.get(rule_id)
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
        message="Palm rule updated.",
        data=PalmRuleOut(
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
