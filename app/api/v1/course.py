"""Public and Student Course & LMS Endpoints for Astra Gurukul."""

from typing import Annotated

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import HTMLResponse

from app.api.dependencies import SignedInOrAnonymous, get_current_user
from app.core.exceptions import NotFoundError
from app.models.course import Course, CourseEnrollment
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.course import (
    CourseCertificateOut,
    CourseDetailOut,
    CourseEnrollmentOut,
    CourseListItemOut,
    CourseOrderCreateResponse,
    CoursePaymentSyncRequest,
    CoursePaymentSyncResponse,
    CoursePaymentVerifyRequest,
    CourseQuestionAnswerRequest,
    CourseQuestionAnswerOut,
    CourseQuestionCreateRequest,
    CourseQuestionOut,
    LessonProgressUpdateRequest,
    LessonStreamResponse,
)
from app.services.course_service import CourseService

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("", response_model=ApiResponse[list[CourseListItemOut]])
async def list_courses(
    category: Annotated[str | None, Query(description="Filter by category")] = None,
    level: Annotated[str | None, Query(description="Filter by level")] = None,
    search: Annotated[str | None, Query(description="Keyword search in title/tags")] = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    skip: Annotated[int, Query(ge=0)] = 0,
    user: SignedInOrAnonymous = None,
) -> ApiResponse[list[CourseListItemOut]]:
    """Lists published astrology, tarot, and vastu courses in Astra Gurukul."""
    courses = await CourseService.list_courses(
        category=category,
        level=level,
        search=search,
        limit=limit,
        skip=skip,
    )

    # Fast batch-lookup for enrollment state if user is logged in
    enrollments_map: dict[str, Any] = {}
    if user and courses:
        from app.models.course import CourseEnrollment

        c_ids = [c.id for c in courses]
        user_enrollments = await CourseEnrollment.find(
            CourseEnrollment.user_id == user.id,
            {"course_id": {"$in": c_ids}},
        ).to_list()
        enrollments_map = {str(e.course_id): e for e in user_enrollments}

    items = []
    for c in courses:
        enr = enrollments_map.get(str(c.id))
        is_enrolled = enr is not None
        user_progress_percent = enr.progress_percent if enr else 0.0

        items.append(
            CourseListItemOut(
                id=str(c.id),
                title=c.title,
                slug=c.slug,
                subtitle=c.subtitle,
                category=c.category,
                level=c.level,
                language=c.language,
                instructor_name=c.instructor_name,
                instructor_title=c.instructor_title,
                instructor_avatar=c.instructor_avatar,
                thumbnail_url=c.thumbnail_url,
                price=c.price,
                mrp=c.mrp,
                discount_percent=c.discount_percent,
                currency=c.currency,
                duration_hours=c.duration_hours,
                total_lessons=c.total_lessons,
                total_students=c.total_students,
                average_rating=c.average_rating,
                rating_count=c.rating_count,
                is_featured=c.is_featured,
                certificate_enabled=c.certificate_enabled,
                is_enrolled=is_enrolled,
                user_progress_percent=user_progress_percent,
            )
        )
    return ApiResponse(data=items)


@router.get("/detail/{slug}", response_model=ApiResponse[CourseDetailOut])
async def get_course_detail(
    slug: str,
    user: SignedInOrAnonymous = None,
) -> ApiResponse[CourseDetailOut]:
    """Retrieves full course curriculum, modules, lessons, and enrollment state."""
    course_data = await CourseService.get_course_by_slug(slug=slug, user=user)
    return ApiResponse(data=CourseDetailOut(**course_data))


# -----------------------------------------------------------------------------
# CERTIFICATE VERIFICATION & DOWNLOAD ENDPOINTS
# -----------------------------------------------------------------------------
@router.get("/certificate/verify/{certificate_id}", response_model=ApiResponse[CourseCertificateOut])
async def verify_course_certificate_endpoint(
    certificate_id: str,
    sig: Annotated[str | None, Query(description="Cryptographic HMAC-SHA256 signature verification token")] = None,
) -> ApiResponse[CourseCertificateOut]:
    """Public verification endpoint to validate any Astra Gurukul credential."""
    cert = await CourseService.verify_course_certificate(certificate_id=certificate_id, signature_token=sig)
    return ApiResponse(data=CourseCertificateOut(**cert))


@router.get("/certificate/verify/{certificate_id}/html", response_class=HTMLResponse)
async def verify_course_certificate_html_endpoint(
    certificate_id: str,
    sig: Annotated[str | None, Query(description="Cryptographic HMAC-SHA256 signature verification token")] = None,
) -> HTMLResponse:
    """Renders printable, high-res HTML certificate for public verification."""
    cert = await CourseService.verify_course_certificate(certificate_id=certificate_id, signature_token=sig)
    html_content = CourseService.generate_course_certificate_html(cert)
    return HTMLResponse(content=html_content, status_code=status.HTTP_200_OK)


@router.get("/{course_id}/certificate", response_model=ApiResponse[CourseCertificateOut])
async def get_course_certificate_endpoint(
    course_id: PydanticObjectId,
    user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[CourseCertificateOut]:
    """Retrieves verified certificate data for a completed course."""
    cert = await CourseService.get_course_certificate(user=user, course_id=course_id)
    return ApiResponse(data=CourseCertificateOut(**cert))


@router.get("/{course_id}/certificate/html", response_class=HTMLResponse)
async def get_course_certificate_html_endpoint(
    course_id: PydanticObjectId,
    user: Annotated[User, Depends(get_current_user)],
) -> HTMLResponse:
    """Returns standalone printable HTML certificate for a completed course."""
    cert = await CourseService.get_course_certificate(user=user, course_id=course_id)
    html_content = CourseService.generate_course_certificate_html(cert)
    return HTMLResponse(content=html_content, status_code=status.HTTP_200_OK)


@router.post("/{course_id}/order", response_model=ApiResponse[CourseOrderCreateResponse])
async def create_course_purchase_order(
    course_id: PydanticObjectId,
    user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[CourseOrderCreateResponse]:
    """Creates a Razorpay order for purchasing the course or grants immediate free access."""
    result = await CourseService.create_course_order(user=user, course_id=course_id)
    return ApiResponse(data=CourseOrderCreateResponse(**result))


@router.post("/{course_id}/verify-payment", response_model=ApiResponse[dict])
async def verify_course_payment(
    course_id: PydanticObjectId,
    payload: CoursePaymentVerifyRequest,
    user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[dict]:
    """Verifies Razorpay payment signature and activates instant course enrollment."""
    result = await CourseService.verify_course_payment(
        user=user,
        course_id=course_id,
        razorpay_order_id=payload.razorpay_order_id,
        razorpay_payment_id=payload.razorpay_payment_id,
        razorpay_signature=payload.razorpay_signature,
    )
    return ApiResponse(data=result)


@router.post("/{course_id}/sync-payment", response_model=ApiResponse[CoursePaymentSyncResponse])
async def sync_course_payment(
    course_id: PydanticObjectId,
    user: Annotated[User, Depends(get_current_user)],
    payload: CoursePaymentSyncRequest | None = None,
) -> ApiResponse[CoursePaymentSyncResponse]:
    """Recovers/confirms course enrollment by checking DB enrollment + Razorpay order status."""
    result = await CourseService.sync_course_payment(
        user=user,
        course_id=course_id,
        razorpay_order_id=payload.razorpay_order_id if payload else None,
    )
    return ApiResponse(data=CoursePaymentSyncResponse(**result))


@router.get("/my/enrolled", response_model=ApiResponse[list[CourseEnrollmentOut]])
async def get_my_enrolled_courses(
    user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[list[CourseEnrollmentOut]]:
    """Returns all courses the logged-in student has purchased or enrolled in."""
    enrollments_data = await CourseService.get_user_enrollments_with_details(user=user)
    data = [CourseEnrollmentOut(**e) for e in enrollments_data]
    return ApiResponse(data=data)


@router.get(
    "/{course_id}/lessons/{lesson_id}/stream",
    response_model=ApiResponse[LessonStreamResponse],
)
async def get_lesson_stream(
    course_id: PydanticObjectId,
    lesson_id: PydanticObjectId,
    user: SignedInOrAnonymous = None,
) -> ApiResponse[LessonStreamResponse]:
    """Generates secure, token-authenticated stream details with dynamic anti-piracy watermarking."""
    stream_data = await CourseService.get_lesson_stream(
        course_id=course_id,
        lesson_id=lesson_id,
        user=user,
    )
    return ApiResponse(data=LessonStreamResponse(**stream_data))


@router.post(
    "/{course_id}/lessons/{lesson_id}/progress",
    response_model=ApiResponse[dict],
)
async def update_lesson_progress(
    course_id: PydanticObjectId,
    lesson_id: PydanticObjectId,
    payload: LessonProgressUpdateRequest,
    user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[dict]:
    """Saves student playback position and recalculates overall course completion percentage."""
    result = await CourseService.update_progress(
        user=user,
        course_id=course_id,
        lesson_id=lesson_id,
        watched_seconds=payload.watched_seconds,
        total_seconds=payload.total_seconds,
        mark_completed=payload.mark_completed,
    )
    return ApiResponse(data=result)


@router.post("/{course_id}/sync-payment", response_model=ApiResponse[CoursePaymentSyncResponse])
async def sync_course_payment(
    course_id: PydanticObjectId,
    user: Annotated[User, Depends(get_current_user)],
    payload: CoursePaymentSyncRequest | None = None,
) -> ApiResponse[CoursePaymentSyncResponse]:
    """Recovers/confirms course enrollment by checking DB enrollment + Razorpay order status."""
    result = await CourseService.sync_course_payment(
        user=user,
        course_id=course_id,
        razorpay_order_id=payload.razorpay_order_id if payload else None,
    )
    return ApiResponse(data=CoursePaymentSyncResponse(**result))


# -----------------------------------------------------------------------------
# GURUKUL JIGYASA (TIMESTAMPED Q&A FORUM) ENDPOINTS
# -----------------------------------------------------------------------------
@router.get(
    "/{course_id}/lessons/{lesson_id}/questions",
    response_model=ApiResponse[list[CourseQuestionOut]],
)
async def list_lesson_questions(
    course_id: PydanticObjectId,
    lesson_id: PydanticObjectId,
    sort: Annotated[str, Query(description="Sort order: newest, timestamp, upvotes")] = "newest",
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    skip: Annotated[int, Query(ge=0)] = 0,
    user: SignedInOrAnonymous = None,
) -> ApiResponse[list[CourseQuestionOut]]:
    """Returns timestamped discussion questions for a video lesson."""
    questions = await CourseService.list_lesson_questions(
        course_id=course_id,
        lesson_id=lesson_id,
        current_user=user,
        sort=sort,
        limit=limit,
        skip=skip,
    )
    items = [CourseQuestionOut(**q) for q in questions]
    return ApiResponse(data=items)


@router.post(
    "/{course_id}/lessons/{lesson_id}/questions",
    response_model=ApiResponse[CourseQuestionOut],
    status_code=status.HTTP_201_CREATED,
)
async def create_lesson_question(
    course_id: PydanticObjectId,
    lesson_id: PydanticObjectId,
    payload: CourseQuestionCreateRequest,
    user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[CourseQuestionOut]:
    """Posts a new timestamped question on a video lesson."""
    q = await CourseService.create_lesson_question(
        user=user,
        course_id=course_id,
        lesson_id=lesson_id,
        title=payload.title,
        content=payload.content,
        timestamp_seconds=payload.timestamp_seconds,
    )
    # Return formatted out schema
    out = CourseQuestionOut(
        id=str(q.id),
        course_id=str(q.course_id),
        section_id=str(q.section_id),
        lesson_id=str(q.lesson_id),
        user_id=str(q.user_id),
        user_name=q.user_name,
        user_avatar=q.user_avatar,
        timestamp_seconds=q.timestamp_seconds,
        timestamp_formatted=q.timestamp_formatted,
        title=q.title,
        content=q.content,
        upvote_count=0,
        is_upvoted_by_me=False,
        answer_count=0,
        is_resolved=False,
        has_official_answer=False,
        is_pinned=False,
        answers=[],
        created_at=q.created_at,
    )
    return ApiResponse(data=out, message="Question posted to Gurukul Jigyasa!")


@router.post(
    "/questions/{question_id}/upvote",
    response_model=ApiResponse[dict],
)
async def toggle_question_upvote(
    question_id: PydanticObjectId,
    user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[dict]:
    """Toggles student upvote on a Gurukul Jigyasa question."""
    res = await CourseService.toggle_question_upvote(user=user, question_id=question_id)
    return ApiResponse(data=res)


@router.post(
    "/questions/{question_id}/answers",
    response_model=ApiResponse[CourseQuestionAnswerOut],
    status_code=status.HTTP_201_CREATED,
)
async def answer_question(
    question_id: PydanticObjectId,
    payload: CourseQuestionAnswerRequest,
    user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[CourseQuestionAnswerOut]:
    """Replies to a student question thread."""
    ans = await CourseService.answer_question(
        user=user,
        question_id=question_id,
        content=payload.content,
    )
    out = CourseQuestionAnswerOut(
        id=ans.id,
        user_id=str(ans.user_id),
        user_name=ans.user_name,
        user_role=ans.user_role,
        user_avatar=ans.user_avatar,
        is_official=ans.is_official,
        content=ans.content,
        created_at=ans.created_at,
    )
    return ApiResponse(data=out, message="Answer posted successfully!")

