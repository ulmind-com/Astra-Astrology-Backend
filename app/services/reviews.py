"""Reviews, and the average they add up to.

Two rules decide whether a review may be written, and both are checked here
rather than in the browser:

  * **You were in it.** Only the user side of a consultation may review it —
    not the astrologer, not anybody else holding the id.
  * **It actually happened.** A call nobody answered, a chat that was declined,
    an appointment that was cancelled — none of those are an opinion of the
    astrologer, and letting them be reviewed would turn the rating into a
    record of scheduling accidents.

A second review of the same session is stopped by the unique index, not by a
check-then-write, so two taps on a slow connection cannot both land.

The astrologer's average is recomputed from the rows every time, in one
aggregation. It is a handful of documents per astrologer and the alternative —
nudging a stored average up and down — drifts the first time anything is
hidden or retried.
"""

from beanie import PydanticObjectId
from beanie.operators import And, In
from loguru import logger
from pymongo.errors import DuplicateKeyError

from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.models.appointment import Appointment
from app.models.astrologer import Astrologer
from app.models.base import utcnow
from app.models.call import CallSession
from app.models.chat import ChatSession
from app.models.enums import (
    AppointmentStatus,
    CallStatus,
    ChatStatus,
    ConsultationMode,
    ReviewKind,
)
from app.models.review import Review
from app.models.user import User


class Consultation:
    """The few facts a review needs, whatever kind of session it came from."""

    def __init__(self, *, user_id, astrologer_id, happened: bool, reviewable_reason: str = ""):
        self.user_id = user_id
        self.astrologer_id = astrologer_id
        self.happened = happened
        self.reviewable_reason = reviewable_reason


async def _load(kind: ReviewKind, session_id: PydanticObjectId) -> Consultation:
    """Finds the session and says whether it is the kind of thing one reviews."""
    if kind is ReviewKind.CHAT:
        chat = await ChatSession.get(session_id)
        if chat is None:
            raise NotFoundError("Chat not found.", error_code="chat_not_found")
        # Only a chat that was actually accepted and then finished.
        return Consultation(
            user_id=chat.user_id,
            astrologer_id=chat.astrologer_id,
            happened=chat.status is ChatStatus.ENDED and chat.started_at is not None,
            reviewable_reason="This chat never took place.",
        )

    if kind in (ReviewKind.CALL, ReviewKind.VIDEO):
        call = await CallSession.get(session_id)
        if call is None:
            raise NotFoundError("Call not found.", error_code="call_not_found")
        expected = ConsultationMode.VIDEO if kind is ReviewKind.VIDEO else ConsultationMode.CALL
        if call.mode is not expected:
            raise BadRequestError("That is not this kind of call.", error_code="wrong_kind")
        return Consultation(
            user_id=call.user_id,
            astrologer_id=call.astrologer_id,
            happened=call.status is CallStatus.ENDED and call.started_at is not None,
            reviewable_reason="This call was never answered.",
        )

    appointment = await Appointment.get(session_id)
    if appointment is None:
        raise NotFoundError("Appointment not found.", error_code="appointment_not_found")
    # An appointment is reviewable once its time has passed and it was not
    # called off — there is no "ended" moment to wait for.
    return Consultation(
        user_id=appointment.user_id,
        astrologer_id=appointment.astrologer_id,
        happened=(
            appointment.status in (AppointmentStatus.BOOKED, AppointmentStatus.COMPLETED)
            and appointment.ends_at <= utcnow()
        ),
        reviewable_reason="This appointment has not happened yet.",
    )


async def leave(
    *, user: User, kind: ReviewKind, session_id: PydanticObjectId, stars: int, text: str | None
) -> Review:
    """Writes one review and refreshes the astrologer's average."""
    if not 1 <= stars <= 5:
        raise BadRequestError("Give between one and five stars.", error_code="bad_rating")

    consultation = await _load(kind, session_id)

    if consultation.user_id != user.id:
        raise ForbiddenError(
            "Only the person who had the consultation can review it.",
            error_code="not_your_consultation",
        )
    if not consultation.happened:
        raise BadRequestError(
            consultation.reviewable_reason, error_code="nothing_to_review"
        )

    cleaned = (text or "").strip() or None

    review = Review(
        astrologer_id=consultation.astrologer_id,
        user_id=user.id,
        kind=kind,
        session_id=session_id,
        stars=stars,
        text=cleaned,
        author_name=user.full_name,
    )
    try:
        await review.insert()
    except DuplicateKeyError:
        raise ConflictError(
            "You have already reviewed this consultation.", error_code="already_reviewed"
        )

    await recalculate(consultation.astrologer_id)
    logger.info(
        "Review left: {} stars for astrologer {} ({} {})",
        stars,
        consultation.astrologer_id,
        kind.value,
        session_id,
    )
    return review


async def recalculate(astrologer_id: PydanticObjectId) -> dict[str, float | int]:
    """Rebuilds one astrologer's average from the reviews that still count."""
    pipeline = [
        {"$match": {"astrologer_id": astrologer_id, "is_hidden": {"$ne": True}}},
        {"$group": {"_id": None, "average": {"$avg": "$stars"}, "count": {"$sum": 1}}},
    ]
    cursor = await Review.get_pymongo_collection().aggregate(pipeline)
    rows = [row async for row in cursor]

    average = round(rows[0]["average"], 2) if rows else 0.0
    count = rows[0]["count"] if rows else 0

    profile = await Astrologer.get(astrologer_id)
    if profile is not None:
        profile.rating.average = average
        profile.rating.count = count
        await profile.save()

        # The card people are looking at should move with it.
        try:
            from app.services import realtime

            await realtime.publish_astrologer(profile)
        except Exception as exc:  # noqa: BLE001 - a stale card is not a failed review
            logger.debug("Rating push skipped: {}", exc)

    return {"average": average, "count": count}


# ------------------------------------------------------------------ reading
async def for_astrologer(
    astrologer_id: PydanticObjectId, *, skip: int = 0, limit: int = 20
) -> tuple[list[Review], int]:
    """The public list: newest first, hidden ones left out."""
    query = Review.find(
        And(Review.astrologer_id == astrologer_id, Review.is_hidden != True)  # noqa: E712
    )
    total = await query.count()
    items = await query.sort(-Review.created_at).skip(skip).limit(limit).to_list()
    return items, total


async def breakdown(astrologer_id: PydanticObjectId) -> dict[int, int]:
    """How many of each star count, for the bar chart on a profile."""
    pipeline = [
        {"$match": {"astrologer_id": astrologer_id, "is_hidden": {"$ne": True}}},
        {"$group": {"_id": "$stars", "count": {"$sum": 1}}},
    ]
    cursor = await Review.get_pymongo_collection().aggregate(pipeline)
    counts = dict.fromkeys(range(1, 6), 0)
    async for row in cursor:
        counts[int(row["_id"])] = row["count"]
    return counts


async def mine(user_id: PydanticObjectId) -> list[Review]:
    return await Review.find(Review.user_id == user_id).sort(-Review.created_at).to_list()


async def existing_for(
    user_id: PydanticObjectId, kind: ReviewKind, session_id: PydanticObjectId
) -> Review | None:
    return await Review.find_one(
        And(
            Review.user_id == user_id,
            Review.kind == kind,
            Review.session_id == session_id,
        )
    )


async def pending_for(user: User) -> list[dict]:
    """Consultations this user finished but has not reviewed yet.

    This is what the prompt is built from. Looked up rather than remembered on
    the session, so a review written on one device stops the prompt appearing
    on another.
    """
    done: list[tuple[ReviewKind, PydanticObjectId, object, str]] = []

    chats = await ChatSession.find(
        And(ChatSession.user_id == user.id, ChatSession.status == ChatStatus.ENDED)
    ).sort(-ChatSession.ended_at).limit(10).to_list()
    for chat in chats:
        if chat.started_at and chat.id:
            done.append((ReviewKind.CHAT, chat.id, chat.astrologer_id, "chat"))

    calls = await CallSession.find(
        And(CallSession.user_id == user.id, CallSession.status == CallStatus.ENDED)
    ).sort(-CallSession.ended_at).limit(10).to_list()
    for call in calls:
        if call.started_at and call.id:
            kind = ReviewKind.VIDEO if call.mode is ConsultationMode.VIDEO else ReviewKind.CALL
            done.append((kind, call.id, call.astrologer_id, kind.value))

    appointments = await Appointment.find(
        And(
            Appointment.user_id == user.id,
            In(Appointment.status, [AppointmentStatus.BOOKED, AppointmentStatus.COMPLETED]),
        )
    ).sort(-Appointment.starts_at).limit(10).to_list()
    now = utcnow()
    for appointment in appointments:
        if appointment.ends_at <= now and appointment.id:
            done.append(
                (ReviewKind.APPOINTMENT, appointment.id, appointment.astrologer_id, "appointment")
            )

    if not done:
        return []

    # One query for everything already reviewed, rather than one per session.
    reviewed = {
        (r.kind, r.session_id)
        for r in await Review.find(
            And(
                Review.user_id == user.id,
                In(Review.session_id, [session_id for _, session_id, _, _ in done]),
            )
        ).to_list()
    }

    pending = []
    for kind, session_id, astrologer_id, label in done:
        if (kind, session_id) in reviewed:
            continue
        profile = await Astrologer.get(astrologer_id)
        if profile is None:
            continue
        pending.append(
            {
                "kind": kind,
                "session_id": str(session_id),
                "astrologer_id": str(astrologer_id),
                "astrologer_name": profile.display_name,
                "astrologer_avatar_url": profile.profile_image_url,
                "label": label,
            }
        )
    return pending


# -------------------------------------------------------------------- admin
async def set_hidden(
    *, review_id: PydanticObjectId, hidden: bool, reason: str | None = None
) -> Review:
    """Takes a review down, or puts it back. The row is never deleted."""
    review = await Review.get(review_id)
    if review is None:
        raise NotFoundError("Review not found.", error_code="review_not_found")

    review.is_hidden = hidden
    review.hidden_reason = reason if hidden else None
    review.hidden_at = utcnow() if hidden else None
    await review.save()

    await recalculate(review.astrologer_id)
    return review
