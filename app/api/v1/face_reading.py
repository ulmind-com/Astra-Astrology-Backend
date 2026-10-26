import base64
import json
from typing import Annotated

from beanie import PydanticObjectId
from fastapi import APIRouter, Query, Request, status
from loguru import logger

from app.api.dependencies import AdminUser, CurrentUser
from app.core.exceptions import BadRequestError, NotFoundError, ServiceUnavailableError
from app.models.enums import TransactionReason
from app.models.face_reading import Condition, FaceReading, FaceRule
from app.schemas.common import ApiResponse
from app.schemas.face_reading import (
    FaceReadingAvailability,
    FaceReadingOut,
    FaceScanResponse,
    HeadPoseOut,
    HouseZoneCorrelation,
    KundliFaceSyncOut,
    MeasurementDetailOut,
    PanchaMahabhutaOut,
    QualityChecksOut,
    ReadingSectionOut,
    RuleOut,
    RuleUpdate,
    SubmitReadingRequest,
    TriZoneAnalysisOut,
    TriZoneEraDetail,
)
from app.services import face_reading as service
from app.services.face_reading_kundli import synchronize_face_with_kundli

router = APIRouter(prefix="/face-reading", tags=["face reading"])




def _out(reading: FaceReading) -> FaceReadingOut:
    return FaceReadingOut(
        id=str(reading.id),
        sections=[ReadingSectionOut(**s.model_dump()) for s in reading.sections],
        coins_charged=reading.coins_charged,
        quality=reading.quality,
        created_at=reading.created_at,
        tri_zone_analysis=reading.tri_zone_analysis,
        pancha_mahabhuta=reading.pancha_mahabhuta,
        kundli_sync=reading.kundli_sync,
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
        user=user,
        measurements=payload.measurements,
        quality=payload.quality,
        birth_details=payload.birth_details,
    )
    return ApiResponse(message="Your reading is ready.", data=_out(reading))


@router.post(
    "/scan",
    response_model=ApiResponse[FaceScanResponse],
    summary="Robust MediaPipe + OpenCV facial scanning and Samudrik Shastra reading",
)
async def scan(user: CurrentUser, request: Request) -> ApiResponse[FaceScanResponse]:
    """Processes an image through the production MediaPipe + OpenCV 3D scanning pipeline.

    Stages:
        A - Image validation, orientation correction, OpenCV decoding
        B & D - Face detection, quality checks, pose estimation (yaw/pitch/roll)
        E - 23 geometric biometric ratios strictly bounded in [0.0, 10.0]
        G - Visualization overlay generation with biometric mesh
        H - Samudrik Shastra interpretation & coin debit (only when quality is acceptable)
    """
    from app.services import settings as settings_service
    from app.services import wallet as wallet_service

    content_type = request.headers.get("content-type", "")
    raw_bytes: bytes = b""
    birth_details: dict[str, Any] | None = None

    if "multipart/form-data" in content_type:
        form = await request.form()
        file_field = form.get("file")
        if file_field and hasattr(file_field, "read"):
            raw_bytes = await file_field.read()
        elif "image" in form and isinstance(form["image"], str):
            val = form["image"]
            if "," in val:
                val = val.split(",", 1)[1]
            try:
                raw_bytes = base64.b64decode(val)
            except Exception:
                raise BadRequestError("Invalid base64 payload.", error_code="invalid_base64")
        bd_raw = form.get("birth_details")
        if bd_raw and isinstance(bd_raw, str):
            try:
                birth_details = json.loads(bd_raw)
            except Exception:
                pass
    elif "application/json" in content_type:
        try:
            body = await request.json()
        except Exception:
            raise BadRequestError("Invalid JSON body.", error_code="invalid_json")
        val = body.get("image") or body.get("image_base64")
        if not val or not isinstance(val, str):
            raise BadRequestError(
                "Missing 'image' or 'image_base64' string in JSON body.",
                error_code="missing_image",
            )
        if "," in val:
            val = val.split(",", 1)[1]
        try:
            raw_bytes = base64.b64decode(val)
        except Exception:
            raise BadRequestError("Invalid base64 string.", error_code="invalid_base64")
        birth_details = body.get("birth_details")
    else:
        raw_bytes = await request.body()

    if not raw_bytes:
        raise BadRequestError("Empty image payload received.", error_code="empty_image")

    # Preliminary setting & wallet verification
    platform = await settings_service.get_settings()
    if not platform.face_reading_enabled:
        raise ServiceUnavailableError(
            "Face reading is not available right now.",
            error_code="face_reading_disabled",
        )

    wallet = await wallet_service.get_or_create_wallet(user.id)
    if platform.face_reading_coins > 0 and wallet.balance_coins < platform.face_reading_coins:
        raise BadRequestError(
            f"You need {platform.face_reading_coins} coins for a face reading, "
            f"but your balance is {wallet.balance_coins}.",
            error_code="insufficient_coins",
        )

    # Execute Computer Vision Pipeline
    try:
        from app.services.face_cv import QualityStatus, execute_scan_pipeline
    except ImportError as e:
        logger.exception("Face CV dependencies failed to import: {}", e)
        raise ServiceUnavailableError(
            "Facial scanning service is missing system runtime libraries (libGL). "
            "Please contact support.",
            error_code="cv_dependencies_missing",
        )

    try:
        cv_result = execute_scan_pipeline(raw_bytes)
    except ValueError as e:
        raise BadRequestError(str(e), error_code="invalid_image")
    except Exception as e:
        logger.exception("Face CV scan failed unexpectedly")
        raise BadRequestError(f"Facial scanning failed: {str(e)}", error_code="scan_failed")


    pose_out = None
    if cv_result.head_pose:
        hp = cv_result.head_pose
        pose_out = HeadPoseOut(
            yaw=round(float(hp.get("yaw", hp.get("yaw_deg", 0.0))), 2),
            pitch=round(float(hp.get("pitch", hp.get("pitch_deg", 0.0))), 2),
            roll=round(float(hp.get("roll", hp.get("roll_deg", 0.0))), 2),
            is_frontal=bool(hp.get("is_frontal", True)),
        )

    qc = cv_result.quality_checks or {}
    cov_ratio = float(qc.get("face_coverage_pct", qc.get("face_coverage_ratio", 0.0) * 100.0))
    checks_out = QualityChecksOut(
        is_valid=bool(qc.get("is_valid", cv_result.status != QualityStatus.REJECTED)),
        status=str(qc.get("status", cv_result.status.value)),
        face_count=int(qc.get("face_count", 1)),
        face_coverage_pct=round(cov_ratio, 2),
        blur_score=round(float(qc.get("blur_score", qc.get("sharpness_score", 0.0))), 2),
        brightness_mean=round(float(qc.get("brightness_mean", 0.0)), 2),
        contrast_std=round(float(qc.get("contrast_std", 0.0)), 2),
        lighting_symmetry_ratio=round(float(qc.get("lighting_symmetry_ratio", 1.0)), 3),
        head_pose=pose_out,
        issues=list(qc.get("issues", [])),
        recommendations=list(qc.get("recommendations", [])),
    )

    # When image is rejected, do NOT charge and do NOT generate a reading
    if cv_result.status == QualityStatus.REJECTED:
        return ApiResponse(
            message=cv_result.error_message or "Image quality did not meet scanning requirements.",
            data=FaceScanResponse(
                scan_id=cv_result.scan_id,
                status=QualityStatus.REJECTED.value,
                quality_score=cv_result.quality_score,
                quality_checks=checks_out,
                head_pose=pose_out,
                measurements={},
                measurement_details={},
                measurement_status="rejected",
                visualization_image=None,
                reading=None,
                coins_charged=0,
                landmark_mapping_version=cv_result.landmark_mapping_version,
                model_version=cv_result.model_version,
                processing_duration_ms=cv_result.processing_duration_ms,
                warnings=cv_result.warnings,
                error_message=cv_result.error_message,
            ),
        )

    # For ACCEPTED or RETAKE_RECOMMENDED: Compose astrology reading and debit coins
    sections = await service.compose(cv_result.measurements)
    if not sections:
        raise ServiceUnavailableError(
            "Face reading rules are currently unavailable. Please try again shortly.",
            error_code="rules_unavailable",
        )

    kundli_sync_dict = None
    if birth_details:
        kundli_sync_dict = synchronize_face_with_kundli(
            birth_data=birth_details,
            measurements=cv_result.measurements,
            tri_zone=cv_result.tri_zone_analysis,
            mahabhuta=cv_result.pancha_mahabhuta,
        )

    reading = FaceReading(
        user_id=user.id,
        measurements=cv_result.measurements,
        sections=sections,
        coins_charged=platform.face_reading_coins,
        quality=round(cv_result.quality_score, 3),
        tri_zone_analysis=cv_result.tri_zone_analysis,
        pancha_mahabhuta=cv_result.pancha_mahabhuta,
        kundli_sync=kundli_sync_dict,
    )
    await reading.insert()

    if platform.face_reading_coins > 0:
        try:
            await wallet_service.debit(
                user_id=user.id,
                amount_coins=platform.face_reading_coins,
                reason=TransactionReason.CONSULTATION,
                idempotency_key=f"face-reading:{reading.id}",
                note="Face reading scan",
            )
        except Exception:
            await reading.delete()
            raise

    details_out = {
        k: MeasurementDetailOut(
            name=v.get("name", k),
            value=v.get("value", 0.0),
            description=v.get("description", ""),
            formula=v.get("formula", ""),
            landmarks_used=v.get("landmarks_used", []),
            status=v.get("status", "available"),
        )
        for k, v in cv_result.measurement_details.items()
    }

    tri_zone_out = TriZoneAnalysisOut(**cv_result.tri_zone_analysis) if cv_result.tri_zone_analysis else None
    mahabhuta_out = PanchaMahabhutaOut(**cv_result.pancha_mahabhuta) if cv_result.pancha_mahabhuta else None
    kundli_sync_out = KundliFaceSyncOut(**kundli_sync_dict) if kundli_sync_dict else None

    return ApiResponse(
        message="Face scanning complete and reading generated.",
        data=FaceScanResponse(
            scan_id=cv_result.scan_id,
            status=cv_result.status.value,
            quality_score=cv_result.quality_score,
            quality_checks=checks_out,
            head_pose=pose_out,
            measurements=cv_result.measurements,
            measurement_details=details_out,
            measurement_status=(
                "valid" if cv_result.status == QualityStatus.ACCEPTED else "retake_recommended"
            ),
            visualization_image=cv_result.visualization_image,
            reading=_out(reading),
            coins_charged=reading.coins_charged,
            forehead_lines_count=cv_result.forehead_lines_count,
            forehead_lines_data=cv_result.forehead_lines_data,
            forehead_lines_shastra=cv_result.forehead_lines_shastra,
            tri_zone_analysis=tri_zone_out,
            pancha_mahabhuta=mahabhuta_out,
            kundli_sync=kundli_sync_out,
            landmark_mapping_version=cv_result.landmark_mapping_version,
            model_version=cv_result.model_version,
            processing_duration_ms=cv_result.processing_duration_ms,
            warnings=cv_result.warnings,
            error_message=None,
        ),
    )



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
