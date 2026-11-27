"""Purohit endpoints: Public directory, Purohit self-management dashboard, and devotee puja booking."""

import asyncio
from typing import Annotated

from fastapi import APIRouter, File, Header, Query, UploadFile, status

from app.api.dependencies import CurrentUser
from app.core.config import settings
from app.core.exceptions import UnauthorizedError
from app.core.security import create_application_upload_token, verify_application_upload_token
from app.models.enums import PujaBookingStatus, PujaPaymentStatus
from app.models.purohit import PujaBooking
from app.models.purohit_application import PurohitApplication
from app.models.user import User
from app.schemas.common import ApiResponse, MessageResponse
from app.schemas.purohit import (
    PujaBookingCreate,
    PujaBookingOut,
    PujaDeclineRequest,
    PujaPaymentVerifyRequest,
    PurohitAvailabilityUpdate,
    PurohitOut,
    PurohitPujaItemCreate,
    PurohitPujaItemOut,
    PurohitPujaItemUpdate,
)
from app.schemas.purohit_application import (
    PurohitApplicationCreateIn,
    PurohitApplicationOut,
    PurohitApplicationSendOtpIn,
    PurohitApplicationVerifyOtpIn,
)
from app.services import purohit_application_service, purohit_service
from app.services.storage import (
    ALLOWED_DOC_TYPES,
    ALLOWED_IMAGE_TYPES,
    safe_delete_cloudinary_image,
    upload_file,
)

router = APIRouter(prefix="/purohits", tags=["purohits"])


def _app_to_out(app: PurohitApplication) -> PurohitApplicationOut:
    return PurohitApplicationOut(
        id=str(app.id),
        application_number=app.application_number,
        full_name=app.full_name,
        email=app.email,
        phone=app.phone,
        age=app.age,
        address=app.address,
        city=app.city,
        state=app.state,
        pincode=app.pincode,
        vedic_shakha=app.vedic_shakha,
        specializations=app.specializations,
        experience_years=app.experience_years,
        languages=app.languages,
        bio=app.bio,
        avatar_url=app.avatar_url,
        identity_proof_url=app.identity_proof_url,
        bank_account_number=app.bank_account_number,
        bank_ifsc=app.bank_ifsc,
        bank_account_holder=app.bank_account_holder,
        upi_id=app.upi_id,
        status=app.status,
        rejection_reason=app.rejection_reason,
        reviewed_at=app.reviewed_at,
        approved_user_id=str(app.approved_user_id) if app.approved_user_id else None,
        approved_purohit_id=str(app.approved_purohit_id) if app.approved_purohit_id else None,
        created_at=app.created_at,
        updated_at=app.updated_at,
    )


# ---------------------------------------------------------------------------
# Purohit Self-Application & Onboarding (Public)
# ---------------------------------------------------------------------------
@router.post(
    "/applications/send-otp",
    response_model=ApiResponse[dict[str, str]],
    summary="Send an email OTP to verify applicant email before onboarding submission",
)
async def send_application_otp(payload: PurohitApplicationSendOtpIn) -> ApiResponse[dict[str, str]]:
    await purohit_application_service.send_application_otp(payload.email)
    return ApiResponse.ok(
        data={"email": payload.email},
        message="A verification OTP has been sent to your email address.",
    )


@router.post(
    "/applications/verify-otp",
    response_model=ApiResponse[dict[str, bool | str]],
    summary="Verify applicant email OTP",
)
async def verify_application_otp(
    payload: PurohitApplicationVerifyOtpIn,
) -> ApiResponse[dict[str, bool | str]]:
    await purohit_application_service.verify_application_otp(payload.email, payload.code)
    upload_token = create_application_upload_token(payload.email)
    return ApiResponse.ok(
        data={"verified": True, "upload_token": upload_token},
        message="Email OTP verified successfully.",
    )


@router.post(
    "/applications/upload-document",
    response_model=ApiResponse[dict[str, str]],
    summary="Upload avatar photo or verification document for Purohit application",
)
async def upload_application_document(
    file: UploadFile = File(...),
    x_upload_token: Annotated[str | None, Header(alias="X-Upload-Token")] = None,
) -> ApiResponse[dict[str, str]]:
    if not x_upload_token:
        raise UnauthorizedError(
            "Email OTP verification is required before uploading application documents.",
            error_code="upload_token_required",
        )
    verify_application_upload_token(x_upload_token)
    result = await upload_file(
        file,
        folder="purohit_applications",
        allowed_types=ALLOWED_IMAGE_TYPES | ALLOWED_DOC_TYPES,
        image_format="webp",
    )
    return ApiResponse.ok(
        data={
            "url": result.secure_url,
            "public_id": result.public_id,
            "format": result.format or "file",
        },
        message="Document uploaded successfully.",
    )


@router.post(
    "/applications/submit",
    response_model=ApiResponse[PurohitApplicationOut],
    status_code=status.HTTP_201_CREATED,
    summary="Submit a verified Purohit self-application",
)
async def submit_purohit_application(
    payload: PurohitApplicationCreateIn,
) -> ApiResponse[PurohitApplicationOut]:
    app = await purohit_application_service.submit_application(payload)
    return ApiResponse(
        data=_app_to_out(app),
        message="Your Purohit application has been submitted successfully for verification.",
    )


# ---------------------------------------------------------------------------
# Public Directory & Profile
# ---------------------------------------------------------------------------
@router.get(
    "",
    response_model=ApiResponse[list[PurohitOut]],
    summary="List live available Purohits with optional search by puja name",
)
async def list_purohits(
    online_only: Annotated[bool, Query(description="Only show currently online and free Purohits")] = True,
    exclude_busy: Annotated[bool, Query(description="Exclude Purohits currently in another live puja")] = True,
    search_puja: Annotated[str | None, Query(description="Search by specific Puja name (e.g. Lakshmi, Durga)")] = None,
    language: Annotated[str | None, Query(description="Filter by language, e.g. Bengali")] = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[list[PurohitOut]]:
    items, _ = await purohit_service.list_purohits(
        is_online_only=online_only,
        exclude_busy=exclude_busy,
        search_puja=search_puja,
        language=language,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(data=[PurohitOut(**it) for it in items])


@router.get(
    "/{identifier}",
    response_model=ApiResponse[PurohitOut],
    summary="Get public profile and puja catalog of a Purohit by ID or slug",
)
async def get_purohit_profile(identifier: str) -> ApiResponse[PurohitOut]:
    data = await purohit_service.get_purohit_by_id_or_slug(identifier)
    return ApiResponse(data=PurohitOut(**data))


@router.get(
    "/{identifier}/catalog",
    response_model=ApiResponse[list[PurohitPujaItemOut]],
    summary="Get the dedicated puja catalog of a specific Purohit by ID or slug",
)
async def get_purohit_catalog(identifier: str) -> ApiResponse[list[PurohitPujaItemOut]]:
    """Retrieves verified pujas offered by the given Purohit."""
    data = await purohit_service.get_purohit_by_id_or_slug(identifier)
    pujas = data.get("pujas") or []
    out = [PurohitPujaItemOut(**p) for p in pujas if p.get("is_active", True)]
    return ApiResponse(data=out)


# ---------------------------------------------------------------------------
# Purohit Dashboard (Protected: Purohit role)
# ---------------------------------------------------------------------------
@router.get(
    "/me/profile",
    response_model=ApiResponse[PurohitOut],
    summary="Fetch current logged-in Purohit's profile",
)
async def get_my_purohit_profile(user: CurrentUser) -> ApiResponse[PurohitOut]:
    profile = await purohit_service.get_purohit_by_user_id(user.id)
    return ApiResponse(data=PurohitOut(**purohit_service.serialize_purohit(profile)))


@router.post(
    "/me/avatar",
    response_model=ApiResponse[PurohitOut],
    summary="Upload or update current Purohit's avatar image",
)
async def upload_my_purohit_avatar(
    file: UploadFile = File(...),
    user: CurrentUser = None,
) -> ApiResponse[PurohitOut]:
    profile = await purohit_service.get_purohit_by_user_id(user.id)
    old_avatar = profile.avatar_url

    result = await upload_file(
        file,
        folder="purohits",
        allowed_types=ALLOWED_IMAGE_TYPES,
        transformation=[
            {"width": 800, "height": 800, "crop": "fill", "gravity": "face"},
            {"quality": "auto:good"},
            {"fetch_format": "auto"},
        ],
        image_format="webp",
    )

    profile.avatar_url = result.secure_url
    await profile.save()

    # Sync User document
    db_user = await User.get(user.id)
    if db_user:
        db_user.avatar_url = result.secure_url
        await db_user.save()

    # Clean up old Cloudinary asset
    if old_avatar and old_avatar != result.secure_url and "cloudinary.com" in old_avatar:
        asyncio.create_task(safe_delete_cloudinary_image(old_avatar))

    data = profile.model_dump()
    data["id"] = str(profile.id)
    data["user_id"] = str(profile.user_id)
    data["starting_price_inr"] = purohit_service._get_starting_price(profile)
    return ApiResponse(message="প্রোফাইল ছবি সফলভাবে আপডেট করা হয়েছে।", data=PurohitOut(**data))


@router.put(
    "/me/availability",
    response_model=ApiResponse[PurohitOut],
    summary="Toggle live online/offline presence for immediate puja calls",
)
async def update_my_availability(
    payload: PurohitAvailabilityUpdate, user: CurrentUser
) -> ApiResponse[PurohitOut]:
    profile = await purohit_service.get_purohit_by_user_id(user.id)
    updated = await purohit_service.update_purohit_availability(
        profile,
        is_online=payload.is_online,
        available_days=payload.available_days,
        available_slots=payload.available_slots,
        weekly_schedule=payload.weekly_schedule,
    )
    status_str = "অনলাইন (লাইভ পূজার জন্য উপলব্ধ)" if payload.is_online else "অফলাইন"
    return ApiResponse(
        message=f"আপনার উপস্থিতি স্ট্যাটাস সফলভাবে {status_str} করা হয়েছে।",
        data=PurohitOut(**purohit_service.serialize_purohit(updated)),
    )


@router.get(
    "/me/availability",
    response_model=ApiResponse[PurohitOut],
    summary="Get current Purohit live availability and busy status",
)
async def get_my_availability(user: CurrentUser) -> ApiResponse[PurohitOut]:
    profile = await purohit_service.get_purohit_by_user_id(user.id)
    return ApiResponse(data=PurohitOut(**purohit_service.serialize_purohit(profile)))


@router.post(
    "/me/presence/offline",
    response_model=MessageResponse,
    summary="Explicitly mark Purohit offline (for logout / tab close)",
)
async def mark_my_presence_offline(user: CurrentUser) -> MessageResponse:
    from app.services import purohit_presence

    profile = await purohit_service.get_purohit_by_user_id(user.id)
    await purohit_presence.go_offline(profile, reason="explicit offline")
    return MessageResponse(message="Marked offline.")


@router.get(
    "/me/bookings/active",
    response_model=ApiResponse[PujaBookingOut | None],
    summary="Get any currently ringing or in-progress live puja for this Purohit",
)
async def get_my_active_purohit_booking(user: CurrentUser) -> ApiResponse[PujaBookingOut | None]:
    booking = await purohit_service.get_active_purohit_booking(user.id)
    return ApiResponse(data=_booking_to_out(booking) if booking else None)


@router.post(
    "/me/pujas",
    response_model=ApiResponse[PurohitPujaItemOut],
    status_code=status.HTTP_201_CREATED,
    summary="Add a new puja with custom pricing to Purohit's personal price catalog",
)
async def add_puja_to_my_catalog(
    payload: PurohitPujaItemCreate, user: CurrentUser
) -> ApiResponse[PurohitPujaItemOut]:
    profile = await purohit_service.get_purohit_by_user_id(user.id)
    item = await purohit_service.add_puja_to_catalog(profile, payload)
    return ApiResponse(message="পূজাটি আপনার ক্যাটালগে সফলভাবে যুক্ত করা হয়েছে।", data=PurohitPujaItemOut.model_validate(item))


@router.put(
    "/me/pujas/{puja_id}",
    response_model=ApiResponse[PurohitPujaItemOut],
    summary="Update an existing puja offering in Purohit's price catalog",
)
async def update_puja_in_my_catalog(
    puja_id: str, payload: PurohitPujaItemUpdate, user: CurrentUser
) -> ApiResponse[PurohitPujaItemOut]:
    profile = await purohit_service.get_purohit_by_user_id(user.id)
    item = await purohit_service.update_puja_in_catalog(profile, puja_id, payload)
    return ApiResponse(message="পূজার বিবরণ ও দক্ষিণা আপডেট করা হয়েছে।", data=PurohitPujaItemOut.model_validate(item))


@router.delete(
    "/me/pujas/{puja_id}",
    response_model=MessageResponse,
    summary="Delete a puja from Purohit's catalog",
)
async def delete_puja_from_my_catalog(puja_id: str, user: CurrentUser) -> MessageResponse:
    profile = await purohit_service.get_purohit_by_user_id(user.id)
    await purohit_service.delete_puja_from_catalog(profile, puja_id)
    return MessageResponse(message="পূজাটি সফলভাবে ক্যাটালগ থেকে মুছে ফেলা হয়েছে।")


@router.get(
    "/me/bookings",
    response_model=ApiResponse[list[PujaBookingOut]],
    summary="Fetch all puja bookings for the logged-in Purohit",
)
async def get_my_purohit_bookings(user: CurrentUser) -> ApiResponse[list[PujaBookingOut]]:
    bookings = await purohit_service.list_purohit_bookings(user.id)
    return ApiResponse(data=[_booking_to_out(b) for b in bookings])


@router.post(
    "/bookings/{booking_id}/accept",
    response_model=ApiResponse[PujaBookingOut],
    summary="Purohit accepts an incoming live puja request and starts the timed room",
)
async def accept_puja(booking_id: str, user: CurrentUser) -> ApiResponse[PujaBookingOut]:
    booking, token = await purohit_service.accept_puja_booking(booking_id, user)
    return ApiResponse(
        message=f"পূজা অনুরোধ গ্রহণ করা হয়েছে! লাইভ রুম {booking.puja_duration_minutes} মিনিটের জন্য চালু হয়েছে।",
        data=_booking_to_out(booking, token=token),
    )


@router.post(
    "/bookings/{booking_id}/decline",
    response_model=ApiResponse[PujaBookingOut],
    summary="Purohit declines a live puja request (triggers automatic 100% refund)",
)
async def decline_puja(
    booking_id: str,
    user: CurrentUser,
    payload: PujaDeclineRequest | None = None,
) -> ApiResponse[PujaBookingOut]:
    booking = await purohit_service.decline_puja_booking(
        booking_id, user, reason=payload.reason if payload else None
    )
    return ApiResponse(
        message="পূজা অনুরোধ প্রত্যাখ্যান করা হয়েছে এবং ভক্তকে সম্পূর্ণ অর্থ ফেরত পাঠানো হয়েছে।",
        data=_booking_to_out(booking),
    )


@router.post(
    "/bookings/{booking_id}/complete",
    response_model=ApiResponse[PujaBookingOut],
    summary="Mark a live puja session as completed",
)
async def complete_puja(booking_id: str, user: CurrentUser) -> ApiResponse[PujaBookingOut]:
    b = await purohit_service.complete_puja_session(booking_id, user)
    return ApiResponse(
        message="পূজা সম্পন্ন হিসেবে চিহ্নিত করা হয়েছে। আশীর্বাদ সর্বত্র বর্ষিত হোক!",
        data=_booking_to_out(b),
    )


def _booking_to_out(booking: PujaBooking, *, token: str | None = None) -> PujaBookingOut:
    """Serialize PujaBooking into PujaBookingOut with Razorpay metadata when pending."""
    amount_paise = max(100, int(round(booking.amount_inr * 100)))
    is_pending_rzp = booking.payment_status != PujaPaymentStatus.PAID and bool(booking.razorpay_order_id)
    return PujaBookingOut(
        id=str(booking.id),
        booking_number=booking.booking_number,
        user_id=str(booking.user_id),
        user_name=booking.user_name,
        user_phone=booking.user_phone,
        purohit_id=str(booking.purohit_id),
        purohit_user_id=str(booking.purohit_user_id),
        purohit_name=booking.purohit_name,
        puja_item_id=booking.puja_item_id,
        puja_name=booking.puja_name,
        puja_duration_minutes=booking.puja_duration_minutes,
        amount_inr=booking.amount_inr,
        amount_paise=amount_paise,
        sankalpa_name=booking.sankalpa_name,
        sankalpa_gotra=booking.sankalpa_gotra,
        sankalpa_nakshatra=booking.sankalpa_nakshatra,
        sankalpa_wish=booking.sankalpa_wish,
        room_id=booking.room_id,
        zego_token=token,
        razorpay_key_id=settings.RAZORPAY_KEY_ID if is_pending_rzp else None,
        razorpay_order_id=booking.razorpay_order_id if is_pending_rzp else None,
        status=booking.status,
        payment_status=booking.payment_status,
        started_at=booking.started_at,
        accepted_at=getattr(booking, "accepted_at", None),
        expires_at=getattr(booking, "expires_at", None),
        completed_at=booking.completed_at,
        declined_at=getattr(booking, "declined_at", None),
        cancel_reason=getattr(booking, "cancel_reason", None),
        refund_id=getattr(booking, "refund_id", None),
        refunded_at=getattr(booking, "refunded_at", None),
        created_at=booking.created_at,
    )


# ---------------------------------------------------------------------------
# Devotee Puja Booking & Video Room
# ---------------------------------------------------------------------------
@router.post(
    "/bookings",
    response_model=ApiResponse[PujaBookingOut],
    status_code=status.HTTP_201_CREATED,
    summary="Book a live online puja with a verified Purohit",
)
async def book_puja_session(
    payload: PujaBookingCreate, user: CurrentUser
) -> ApiResponse[PujaBookingOut]:
    booking, token = await purohit_service.book_puja(user, payload)
    out = _booking_to_out(booking, token=token)
    msg = (
        f"পূজা সফলভাবে বুক করা হয়েছে (#{booking.booking_number})। পুরোহিতজীর সাথে এখনই যুক্ত হতে রুম ওপেন করুন।"
        if booking.payment_status == PujaPaymentStatus.PAID
        else f"বুকিং (#{booking.booking_number}) শুরু হয়েছে। অনুগ্রহ করে পেমেন্ট সম্পন্ন করুন।"
    )
    return ApiResponse(message=msg, data=out)


@router.post(
    "/bookings/{booking_id}/verify-payment",
    response_model=ApiResponse[PujaBookingOut],
    summary="Verify Razorpay payment to confirm a pending puja booking",
)
async def verify_puja_booking_payment(
    booking_id: str,
    payload: PujaPaymentVerifyRequest,
    user: CurrentUser,
) -> ApiResponse[PujaBookingOut]:
    booking, token = await purohit_service.verify_puja_payment(booking_id, user, payload)
    if booking.status == PujaBookingStatus.CANCELLED or booking.payment_status == PujaPaymentStatus.REFUNDED:
        return ApiResponse(
            message=booking.cancel_reason or "Purohit became busy before payment finished — 100% refund initiated.",
            data=_booking_to_out(booking),
        )
    return ApiResponse(
        message=f"পেমেন্ট সফল হয়েছে! পূজা বুকিং (#{booking.booking_number}) নিশ্চিত করা হয়েছে।",
        data=_booking_to_out(booking, token=token),
    )


@router.get(
    "/bookings/mine",
    response_model=ApiResponse[list[PujaBookingOut]],
    summary="List all pujas booked by the devotee",
)
async def get_my_devotee_bookings(user: CurrentUser) -> ApiResponse[list[PujaBookingOut]]:
    bookings = await purohit_service.list_user_bookings(user.id)
    return ApiResponse(data=[_booking_to_out(b) for b in bookings])


@router.get(
    "/bookings/{booking_id}",
    response_model=ApiResponse[PujaBookingOut],
    summary="Fetch full details for a single puja booking by ID or booking number",
)
async def get_single_booking_endpoint(booking_id: str, user: CurrentUser) -> ApiResponse[PujaBookingOut]:
    """Retrieves full details for a single puja booking for the devotee or the Purohit."""
    booking = await purohit_service.get_booking(booking_id, user)
    return ApiResponse(data=_booking_to_out(booking))


@router.get(
    "/bookings/{booking_id}/token",
    response_model=ApiResponse[PujaBookingOut],
    summary="Get fresh ZEGOCLOUD video room token for entering live puja",
)
async def get_puja_room_token(booking_id: str, user: CurrentUser) -> ApiResponse[PujaBookingOut]:
    booking, token = await purohit_service.get_booking_token(booking_id, user)
    return ApiResponse(data=_booking_to_out(booking, token=token))
