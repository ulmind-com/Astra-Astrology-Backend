"""Palm reading endpoints.

The order of operations is deliberate and matters for fairness: the photo is
scanned *before* any coins are taken, and a scan that fails the quality gates costs
nothing. Charging for a reading the system then refuses to give would be the
easiest way to lose a user's trust, and the hardest to argue with.
"""

from __future__ import annotations

import base64

from beanie import PydanticObjectId
from fastapi import APIRouter, Request
from loguru import logger

from app.api.dependencies import CurrentUser
from app.core.exceptions import BadRequestError, NotFoundError, ServiceUnavailableError
from app.models.palm_reading import PalmReading, PalmRule
from app.schemas.common import ApiResponse
from app.schemas.palm_reading import (
    CreaseOut,
    PalmReadingAvailability,
    PalmReadingOut,
    PalmRuleOut,
    PalmRuleUpdate,
    PalmScanResponse,
    QualityCheckOut,
    ReadingSectionOut,
    SkippedFeatureOut,
)
from app.services import palm_reading as palm_service

router = APIRouter(prefix="/palm-reading", tags=["palm-reading"])

#: Stated on the availability endpoint so the app can tell the user what makes a
#: readable photo before they take one, rather than after it is rejected.
PHOTO_GUIDANCE = [
    "Open your palm fully and hold it flat, facing the camera.",
    "Point your fingers towards the top of the frame.",
    "Fill most of the frame with your palm.",
    "Use even, indirect light. Avoid direct sun and camera flash, which flatten the lines.",
    "Hold steady until the camera has focused.",
]


def _reading_out(reading: PalmReading) -> PalmReadingOut:
    return PalmReadingOut(
        id=str(reading.id),
        hand=reading.hand,
        hand_type=reading.hand_type,
        sections=[ReadingSectionOut(**s.model_dump()) for s in reading.sections],
        skipped=[SkippedFeatureOut(**s.model_dump()) for s in reading.skipped],
        landmarks_3d=reading.landmarks_3d,
        world_landmarks_mm=reading.world_landmarks_mm,
        mount_elevations_3d=reading.mount_elevations_3d,
        palm_cup_depth_mm=reading.palm_cup_depth_mm,
        finger_flexibility_3d=reading.finger_flexibility_3d,
        finger_inclinations_3d=reading.finger_inclinations_3d,
        secondary_lines=getattr(reading, "secondary_lines", {}),
        sacred_marks=getattr(reading, "sacred_marks", []),
        timeline=getattr(reading, "timeline", []),
        skin_vitality=getattr(reading, "skin_vitality", {}),
        karmic_summary=getattr(reading, "karmic_summary", {}),
        dermatoglyphic_loops=getattr(reading, "dermatoglyphic_loops", []),
        marriage_patterns=getattr(reading, "marriage_patterns", []),
        temperament_archetype=getattr(reading, "temperament_archetype", {}),
        medical_constitution=getattr(reading, "medical_constitution", {}),
        kundli_palm_sync=getattr(reading, "kundli_palm_sync", {}),
        overlay_image=reading.overlay_image,
        coins_charged=reading.coins_charged,
        quality_score=reading.quality_score,
        warnings=reading.warnings,
        created_at=reading.created_at,
    )


async def _read_image_payload(request: Request) -> tuple[bytes, dict | None]:
    """Accept the image and optional birth details as multipart, JSON base64, or raw body."""
    content_type = request.headers.get("content-type", "")
    birth_details: dict | None = None

    if "multipart/form-data" in content_type:
        form = await request.form()
        field = form.get("file") or form.get("image")
        if form.get("birth_date"):
            birth_details = {
                "birth_date": str(form.get("birth_date")),
                "birth_time": str(form.get("birth_time") or "12:00"),
                "latitude": float(form.get("latitude") or 22.5726),
                "longitude": float(form.get("longitude") or 88.3639),
                "timezone_offset": float(form.get("timezone_offset") or 5.5),
            }
        if field is not None and hasattr(field, "read"):
            data = await field.read()  # type: ignore[union-attr]
            return data, birth_details
        if isinstance(field, str):
            value = field.split(",", 1)[1] if "," in field else field
            try:
                return base64.b64decode(value), birth_details
            except Exception:
                raise BadRequestError("That image could not be decoded.", error_code="invalid_base64")
        raise BadRequestError("No image was included.", error_code="missing_image")

    if "application/json" in content_type:
        try:
            body = await request.json()
        except Exception:
            raise BadRequestError("The request body was not valid JSON.", error_code="invalid_json")
        value = body.get("image") or body.get("image_base64")
        if body.get("birth_details") and isinstance(body.get("birth_details"), dict):
            birth_details = body.get("birth_details")
        elif body.get("birth_date"):
            birth_details = {
                "birth_date": str(body.get("birth_date")),
                "birth_time": str(body.get("birth_time", "12:00")),
                "latitude": float(body.get("latitude", 22.5726)),
                "longitude": float(body.get("longitude", 88.3639)),
                "timezone_offset": float(body.get("timezone_offset", 5.5)),
            }
        if not isinstance(value, str) or not value:
            raise BadRequestError(
                "Send the photo as 'image' in the JSON body.", error_code="missing_image"
            )
        if "," in value:
            value = value.split(",", 1)[1]
        try:
            return base64.b64decode(value), birth_details
        except Exception:
            raise BadRequestError("That image could not be decoded.", error_code="invalid_base64")

    raw = await request.body()
    return raw, None


@router.get(
    "/availability",
    response_model=ApiResponse[PalmReadingAvailability],
    summary="Whether palm reading is available, and what it costs",
)
async def availability(user: CurrentUser) -> ApiResponse[PalmReadingAvailability]:
    from app.services import settings as settings_service
    from app.services import wallet as wallet_service

    platform = await settings_service.get_settings()
    wallet = await wallet_service.get_or_create_wallet(user.id)
    cost = platform.palm_reading_coins

    return ApiResponse(
        message="Palm reading availability",
        data=PalmReadingAvailability(
            enabled=platform.palm_reading_enabled,
            coins_required=cost,
            wallet_balance=wallet.balance_coins,
            can_afford=wallet.balance_coins >= cost,
            requires=PHOTO_GUIDANCE,
        ),
    )


@router.post(
    "/scan",
    response_model=ApiResponse[PalmScanResponse],
    summary="Scan a palm photo and produce a reading",
)
async def scan(user: CurrentUser, request: Request) -> ApiResponse[PalmScanResponse]:
    """Scan a palm and read it.

    Nothing is charged unless a reading is actually produced. A photo that cannot
    be read comes back with the reason and the balance untouched.
    """
    from app.services import settings as settings_service
    from app.services import wallet as wallet_service

    raw, birth_details = await _read_image_payload(request)
    if not raw:
        raise BadRequestError("No photo was received.", error_code="empty_image")

    platform = await settings_service.get_settings()
    if not platform.palm_reading_enabled:
        raise ServiceUnavailableError(
            "Palm reading is not available right now.", error_code="palm_reading_disabled"
        )

    wallet = await wallet_service.get_or_create_wallet(user.id)
    cost = platform.palm_reading_coins
    if cost > 0 and wallet.balance_coins < cost:
        raise BadRequestError(
            f"A palm reading costs {cost} coins and your balance is {wallet.balance_coins}.",
            error_code="insufficient_coins",
        )

    try:
        from app.services.palm_cv import execute_scan
    except ImportError as exc:
        logger.exception("palm CV dependencies missing")
        raise ServiceUnavailableError(
            "The palm scanning service is missing a system library. Please contact support.",
            error_code="cv_dependencies_missing",
        ) from exc

    result = execute_scan(raw, birth_details=birth_details)

    # A rejected photo is a normal outcome, not an error, and it is free.
    if result.status != "ok":
        return ApiResponse(
            message=result.message or "That photo could not be read.",
            data=PalmScanResponse(
                scan_id=result.scan_id,
                status=result.status,
                message=result.message,
                hand_detected=result.hand_detected,
                handedness=result.handedness,
                quality_score=float((result.quality or {}).get("score", 0.0)),
                quality_checks=[
                    QualityCheckOut(**c) for c in (result.quality or {}).get("checks", [])
                ],
                processing_ms=result.processing_ms,
                warnings=result.warnings,
                wallet_balance=wallet.balance_coins,
            ),
        )

    scan_dict = result.as_dict()
    rules = await palm_service.load_rules()
    sections, skipped = palm_service.build_reading(scan_dict, rules)

    if not sections:
        # A scan that passes the gates but matches no rule is a fault on our side,
        # not the user's, so it is not charged for either.
        return ApiResponse(
            message=(
                "The photo was readable but no reading could be produced from it. "
                "You have not been charged."
            ),
            data=PalmScanResponse(
                scan_id=result.scan_id,
                status="rejected",
                message="No rule matched this hand.",
                hand_detected=True,
                handedness=result.handedness,
                quality_score=float(result.quality.get("score", 0.0)),
                overlay_image=result.overlay_image,
                processing_ms=result.processing_ms,
                wallet_balance=wallet.balance_coins,
                warnings=result.warnings,
            ),
        )

    charged = 0
    if cost > 0:
        from app.models.enums import TransactionReason

        await wallet_service.debit(
            user_id=user.id,
            amount_coins=cost,
            reason=TransactionReason.CONSULTATION,
            # Keyed on the scan, so a retried request cannot charge twice.
            idempotency_key=f"palm-reading:{result.scan_id}",
            note="Palm reading scan",
        )
        charged = cost
        wallet = await wallet_service.get_or_create_wallet(user.id)

    reading = PalmReading(
        user_id=user.id,
        hand=result.handedness or "unknown",
        measurements=result.measurements,
        hand_type=result.hand_type,
        creases=result.creases,
        crease_relationships=result.crease_relationships,
        landmarks_3d=result.landmarks_3d,
        world_landmarks_mm=result.world_landmarks_mm,
        mount_elevations_3d=result.mount_elevations_3d,
        palm_cup_depth_mm=result.palm_cup_depth_mm,
        finger_flexibility_3d=result.finger_flexibility_3d,
        finger_inclinations_3d=result.finger_inclinations_3d,
        secondary_lines=result.secondary_lines,
        sacred_marks=result.sacred_marks,
        timeline=result.timeline,
        skin_vitality=result.skin_vitality,
        karmic_summary=result.karmic_summary,
        dermatoglyphic_loops=result.dermatoglyphic_loops,
        marriage_patterns=result.marriage_patterns,
        temperament_archetype=result.temperament_archetype,
        medical_constitution=result.medical_constitution,
        kundli_palm_sync=result.kundli_palm_sync,
        sections=sections,
        skipped=skipped,
        overlay_image=result.overlay_image,
        coins_charged=charged,
        quality_score=float(result.quality.get("score", 1.0)),
        warnings=result.warnings,
        pipeline_version=result.pipeline_version,
    )
    await reading.insert()

    return ApiResponse(
        message=f"Palm read: {len(sections)} findings from your {result.handedness or ''} hand.",
        data=PalmScanResponse(
            scan_id=result.scan_id,
            status="ok",
            hand_detected=True,
            handedness=result.handedness,
            quality_score=float(result.quality.get("score", 1.0)),
            quality_checks=[QualityCheckOut(**c) for c in result.quality.get("checks", [])],
            hand_type=result.hand_type,
            measurements=result.measurements,
            measurement_details=result.measurement_details,
            creases=[CreaseOut(**c) for c in result.creases.values()],
            crease_relationships=result.crease_relationships,
            sections=[ReadingSectionOut(**s.model_dump()) for s in sections],
            skipped=[SkippedFeatureOut(**s.model_dump()) for s in skipped],
            landmarks_3d=result.landmarks_3d,
            world_landmarks_mm=result.world_landmarks_mm,
            mount_elevations_3d=result.mount_elevations_3d,
            palm_cup_depth_mm=result.palm_cup_depth_mm,
            finger_flexibility_3d=result.finger_flexibility_3d,
            finger_inclinations_3d=result.finger_inclinations_3d,
            secondary_lines=result.secondary_lines,
            sacred_marks=result.sacred_marks,
            timeline=result.timeline,
            skin_vitality=result.skin_vitality,
            karmic_summary=result.karmic_summary,
            dermatoglyphic_loops=result.dermatoglyphic_loops,
            marriage_patterns=result.marriage_patterns,
            temperament_archetype=result.temperament_archetype,
            medical_constitution=result.medical_constitution,
            kundli_palm_sync=result.kundli_palm_sync,
            overlay_image=result.overlay_image,
            response_image=result.response_image,
            coins_charged=charged,
            wallet_balance=wallet.balance_coins,
            processing_ms=result.processing_ms,
            warnings=result.warnings,
            reading_id=str(reading.id),
        ),
    )


@router.get(
    "/mine",
    response_model=ApiResponse[list[PalmReadingOut]],
    summary="Your past palm readings",
)
async def mine(user: CurrentUser) -> ApiResponse[list[PalmReadingOut]]:
    readings = (
        await PalmReading.find(PalmReading.user_id == user.id)
        .sort(-PalmReading.created_at)
        .limit(50)
        .to_list()
    )
    return ApiResponse(
        message=f"{len(readings)} reading(s)",
        data=[_reading_out(r) for r in readings],
    )


@router.get(
    "/mine/{reading_id}",
    response_model=ApiResponse[PalmReadingOut],
    summary="One past palm reading",
)
async def one(reading_id: PydanticObjectId, user: CurrentUser) -> ApiResponse[PalmReadingOut]:
    reading = await PalmReading.get(reading_id)
    if reading is None or reading.user_id != user.id:
        raise NotFoundError("That reading could not be found.", error_code="reading_not_found")
    return ApiResponse(message="Palm reading", data=_reading_out(reading))
