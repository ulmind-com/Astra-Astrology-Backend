"""Purohit endpoints: Public directory, Purohit self-management dashboard, and devotee puja booking."""

from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.dependencies import CurrentUser
from app.core.exceptions import ForbiddenError
from app.models.enums import UserRole
from app.schemas.common import ApiResponse, MessageResponse
from app.schemas.purohit import (
    PujaBookingCreate,
    PujaBookingOut,
    PurohitAvailabilityUpdate,
    PurohitOut,
    PurohitPujaItemCreate,
    PurohitPujaItemOut,
    PurohitPujaItemUpdate,
)
from app.services import purohit_service

router = APIRouter(prefix="/purohits", tags=["purohits"])


# ---------------------------------------------------------------------------
# Public Directory & Profile
# ---------------------------------------------------------------------------
@router.get(
    "",
    response_model=ApiResponse[list[PurohitOut]],
    summary="List verified Purohits with optional online filter and search by puja name",
)
async def list_purohits(
    online_only: Annotated[bool, Query(description="Only show Purohits currently online and available")] = False,
    search_puja: Annotated[str | None, Query(description="Search by specific Puja name (e.g. Lakshmi, Satyanarayan)")] = None,
    language: Annotated[str | None, Query(description="Filter by language, e.g. Bengali")] = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[list[PurohitOut]]:
    items, total = await purohit_service.list_purohits(
        is_online_only=online_only,
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
    data = profile.model_dump()
    data["id"] = str(profile.id)
    data["user_id"] = str(profile.user_id)
    data["starting_price_inr"] = purohit_service._get_starting_price(profile)
    return ApiResponse(data=PurohitOut(**data))


@router.put(
    "/me/availability",
    response_model=ApiResponse[PurohitOut],
    summary="Toggle online/offline presence for live puja calls",
)
async def update_my_availability(
    payload: PurohitAvailabilityUpdate, user: CurrentUser
) -> ApiResponse[PurohitOut]:
    profile = await purohit_service.get_purohit_by_user_id(user.id)
    updated = await purohit_service.update_purohit_availability(profile, payload.is_online)
    data = updated.model_dump()
    data["id"] = str(updated.id)
    data["user_id"] = str(updated.user_id)
    data["starting_price_inr"] = purohit_service._get_starting_price(updated)

    status_str = "অনলাইন (পূজার জন্য উপলব্ধ)" if payload.is_online else "অফলাইন"
    return ApiResponse(message=f"আপনার উপস্থিতি স্ট্যাটাস সফলভাবে {status_str} করা হয়েছে।", data=PurohitOut(**data))


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
    out = [
        PujaBookingOut(
            id=str(b.id),
            booking_number=b.booking_number,
            user_id=str(b.user_id),
            user_name=b.user_name,
            user_phone=b.user_phone,
            purohit_id=str(b.purohit_id),
            purohit_name=b.purohit_name,
            puja_item_id=b.puja_item_id,
            puja_name=b.puja_name,
            puja_duration_minutes=b.puja_duration_minutes,
            amount_inr=b.amount_inr,
            sankalpa_name=b.sankalpa_name,
            sankalpa_gotra=b.sankalpa_gotra,
            sankalpa_wish=b.sankalpa_wish,
            room_id=b.room_id,
            status=b.status,
            payment_status=b.payment_status,
            started_at=b.started_at,
            completed_at=b.completed_at,
            created_at=b.created_at,
        )
        for b in bookings
    ]
    return ApiResponse(data=out)


@router.post(
    "/bookings/{booking_id}/complete",
    response_model=ApiResponse[PujaBookingOut],
    summary="Mark a live puja session as completed",
)
async def complete_puja(booking_id: str, user: CurrentUser) -> ApiResponse[PujaBookingOut]:
    b = await purohit_service.complete_puja_session(booking_id, user)
    out = PujaBookingOut(
        id=str(b.id),
        booking_number=b.booking_number,
        user_id=str(b.user_id),
        user_name=b.user_name,
        user_phone=b.user_phone,
        purohit_id=str(b.purohit_id),
        purohit_name=b.purohit_name,
        puja_item_id=b.puja_item_id,
        puja_name=b.puja_name,
        puja_duration_minutes=b.puja_duration_minutes,
        amount_inr=b.amount_inr,
        sankalpa_name=b.sankalpa_name,
        sankalpa_gotra=b.sankalpa_gotra,
        sankalpa_wish=b.sankalpa_wish,
        room_id=b.room_id,
        status=b.status,
        payment_status=b.payment_status,
        started_at=b.started_at,
        completed_at=b.completed_at,
        created_at=b.created_at,
    )
    return ApiResponse(message="পূজা সম্পন্ন হিসেবে চিহ্নিত করা হয়েছে। আশীর্বাদ সর্বত্র বর্ষিত হোক!", data=out)


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
    out = PujaBookingOut(
        id=str(booking.id),
        booking_number=booking.booking_number,
        user_id=str(booking.user_id),
        user_name=booking.user_name,
        user_phone=booking.user_phone,
        purohit_id=str(booking.purohit_id),
        purohit_name=booking.purohit_name,
        puja_item_id=booking.puja_item_id,
        puja_name=booking.puja_name,
        puja_duration_minutes=booking.puja_duration_minutes,
        amount_inr=booking.amount_inr,
        sankalpa_name=booking.sankalpa_name,
        sankalpa_gotra=booking.sankalpa_gotra,
        sankalpa_wish=booking.sankalpa_wish,
        room_id=booking.room_id,
        zego_token=token,
        status=booking.status,
        payment_status=booking.payment_status,
        started_at=booking.started_at,
        completed_at=booking.completed_at,
        created_at=booking.created_at,
    )
    return ApiResponse(
        message=f"পূজা সফলভাবে বুক করা হয়েছে (#{booking.booking_number})। পুরোহিতজীর সাথে এখনই যুক্ত হতে রুম ওপেন করুন।",
        data=out,
    )


@router.get(
    "/bookings/mine",
    response_model=ApiResponse[list[PujaBookingOut]],
    summary="List all pujas booked by the devotee",
)
async def get_my_devotee_bookings(user: CurrentUser) -> ApiResponse[list[PujaBookingOut]]:
    bookings = await purohit_service.list_user_bookings(user.id)
    out = [
        PujaBookingOut(
            id=str(b.id),
            booking_number=b.booking_number,
            user_id=str(b.user_id),
            user_name=b.user_name,
            user_phone=b.user_phone,
            purohit_id=str(b.purohit_id),
            purohit_name=b.purohit_name,
            puja_item_id=b.puja_item_id,
            puja_name=b.puja_name,
            puja_duration_minutes=b.puja_duration_minutes,
            amount_inr=b.amount_inr,
            sankalpa_name=b.sankalpa_name,
            sankalpa_gotra=b.sankalpa_gotra,
            sankalpa_wish=b.sankalpa_wish,
            room_id=b.room_id,
            status=b.status,
            payment_status=b.payment_status,
            started_at=b.started_at,
            completed_at=b.completed_at,
            created_at=b.created_at,
        )
        for b in bookings
    ]
    return ApiResponse(data=out)


@router.get(
    "/bookings/{booking_id}/token",
    response_model=ApiResponse[PujaBookingOut],
    summary="Get fresh ZEGOCLOUD video room token for entering live puja",
)
async def get_puja_room_token(booking_id: str, user: CurrentUser) -> ApiResponse[PujaBookingOut]:
    booking, token = await purohit_service.get_booking_token(booking_id, user)
    out = PujaBookingOut(
        id=str(booking.id),
        booking_number=booking.booking_number,
        user_id=str(booking.user_id),
        user_name=booking.user_name,
        user_phone=booking.user_phone,
        purohit_id=str(booking.purohit_id),
        purohit_name=booking.purohit_name,
        puja_item_id=booking.puja_item_id,
        puja_name=booking.puja_name,
        puja_duration_minutes=booking.puja_duration_minutes,
        amount_inr=booking.amount_inr,
        sankalpa_name=booking.sankalpa_name,
        sankalpa_gotra=booking.sankalpa_gotra,
        sankalpa_wish=booking.sankalpa_wish,
        room_id=booking.room_id,
        zego_token=token,
        status=booking.status,
        payment_status=booking.payment_status,
        started_at=booking.started_at,
        completed_at=booking.completed_at,
        created_at=booking.created_at,
    )
    return ApiResponse(data=out)
