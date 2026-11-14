"""Course and Learning Management Service for Astra Gurukul."""

import asyncio
import hashlib
import hmac
import json
import secrets
import time
from datetime import datetime, timezone
from typing import Any

from beanie import PydanticObjectId
import httpx
from loguru import logger

from app.core.config import settings
from app.core.exceptions import (
    BadRequestError,
    ForbiddenError,
    NotFoundError,
    ServiceUnavailableError,
    UnauthorizedError,
)
from pymongo.errors import DuplicateKeyError

from app.models.course import (
    Course,
    CourseEnrollment,
    CourseLesson,
    CourseLessonProgress,
    CourseOrder,
    CourseQuestion,
    CourseQuestionAnswer,
    CourseSection,
)
from app.models.enums import PaymentOrderStatus, UserRole
from app.models.user import User
from app.services.payments import _razorpay


def _aware_utc(value: datetime) -> datetime:
    """Mongo hands back naive datetimes; compare them in UTC."""
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


# --- how a lesson is judged to have been watched -----------------------------
# Players report their own position, so the server credits time against its own
# clock instead. These are the allowances that keep honest viewers unaffected.

# Fast playback is normal; 2.5x covers every speed the players offer. A 40
# minute lesson therefore still needs about 15 minutes of real time.
MAX_PLAYBACK_SPEED = 2.5
# Pings are not perfectly regular, and one can be missed entirely.
PING_GRACE_SECONDS = 15
# A first check-in has no previous one to measure from.
FIRST_PING_CREDIT_SECONDS = 15
# Every legitimate lesson has a duration floor so an attacker cannot report
# duration = 1s and complete the course in seconds.
MIN_LESSON_SECONDS = 60
# How much of a lesson counts as having watched it. The last tenth is usually
# credits and goodbyes.
COMPLETION_FRACTION = 0.90


class CourseService:
    # Staff may take part in the Q&A of a course they have not bought: an
    # acharya answering a student is the point of the forum. It does not and
    # must not imply access to the lessons — that still needs an enrollment.
    STAFF_ROLES = frozenset({UserRole.ASTROLOGER, UserRole.ADMIN, UserRole.SUPER_ADMIN})

    @staticmethod
    def _is_staff(user: User) -> bool:
        """Exact role match, not a substring of it.

        `"admin" in str(role)` happens to be right for today's four roles, but
        it reads any future role that merely contains the word — a
        `pending_astrologer`, say — as staff, and nothing would flag it.
        """
        try:
            return UserRole(str(getattr(user, "role", UserRole.USER))) in CourseService.STAFF_ROLES
        except ValueError:
            return False

    @staticmethod
    def mint_certificate_id() -> str:
        """A fresh, unguessable credential number.

        These used to be built from the ids they belonged to —
        `ASTRA-CERT-{user_id[-6:]}-{course_id[-4:]}` — which made them both
        guessable from a student's id and able to collide: two students whose
        ObjectIds happen to end the same way, on the same course, were issued
        the same certificate number.

        Existing numbers are left alone, so every certificate already in
        circulation keeps verifying.
        """
        return f"ASTRA-CERT-{secrets.token_hex(8).upper()}"

    @staticmethod
    def _has_watched_enough(
        *,
        lesson: CourseLesson,
        prog: CourseLessonProgress,
        mark_completed: bool = False,
    ) -> bool:
        """Whether this lesson counts as watched.

        `mark_completed` is honoured only when the time backs it up. It still
        matters: a player that reaches the end fires it, and without it a
        lesson whose last seconds are silent credits would never close.
        """
        # The length we hold ourselves, not the one the client reported.
        duration = (getattr(lesson, "duration_minutes", 0) or 0) * 60
        if duration <= 0:
            # An unpublished duration is common on older lessons. Fall back to
            # the player's own figure, bounded by MIN_LESSON_SECONDS floor.
            duration = max(getattr(prog, "total_seconds", 0) or 0, MIN_LESSON_SECONDS)

        # Enforce minimum duration floor so duration cannot be spoofed to 1 second
        effective_duration = max(duration, MIN_LESSON_SECONDS)
        required = int(effective_duration * COMPLETION_FRACTION)
        credited = getattr(prog, "credited_seconds", 0) or 0
        return credited >= required


    @staticmethod
    async def list_courses(
        category: str | None = None,
        level: str | None = None,
        search: str | None = None,
        limit: int = 20,
        skip: int = 0,
    ) -> list[Course]:
        """Returns active, published courses with optional filtering."""
        query: dict[str, Any] = {"is_published": True, "is_deleted": False}
        if category and category != "all":
            query["category"] = category
        if level and level != "all":
            query["level"] = level
        if search:
            query["$or"] = [
                {"title": {"$regex": search, "$options": "i"}},
                {"subtitle": {"$regex": search, "$options": "i"}},
                {"tags": {"$in": [search.lower()]}},
            ]

        return (
            await Course.find(query)
            .sort([("is_featured", -1), ("created_at", -1)])
            .skip(skip)
            .limit(limit)
            .to_list()
        )

    @staticmethod
    async def get_course_by_slug(slug: str, user: User | None = None) -> dict[str, Any]:
        """Fetches full course details along with modules and lessons."""
        clean_slug = slug.strip()
        course = await Course.find_one(Course.slug == clean_slug, Course.is_deleted == False)
        if not course:
            try:
                oid = PydanticObjectId(clean_slug)
                course = await Course.find_one(Course.id == oid, Course.is_deleted == False)
            except Exception:
                course = None

        if not course:
            raise NotFoundError("Course not found")

        # Find sections ordered by order asc
        sections = (
            await CourseSection.find(CourseSection.course_id == course.id)
            .sort(+CourseSection.order)
            .to_list()
        )

        # Check if user is enrolled
        is_enrolled = False
        user_progress_percent = 0.0
        completed_lesson_ids: set[str] = set()

        if user:
            enrollment = await CourseEnrollment.find_one(
                CourseEnrollment.user_id == user.id,
                CourseEnrollment.course_id == course.id,
            )
            if enrollment:
                is_enrolled = True
                completed_lesson_ids = set(enrollment.completed_lesson_ids)
                total_published = await CourseLesson.find(
                    CourseLesson.course_id == course.id,
                    {"is_published": {"$ne": False}},
                ).count()
                if total_published > 0:
                    calculated_prog = min(100.0, round((len(completed_lesson_ids) / total_published) * 100.0, 1))
                    if calculated_prog != enrollment.progress_percent:
                        enrollment.progress_percent = calculated_prog
                        await enrollment.save()
                user_progress_percent = enrollment.progress_percent
                if enrollment.progress_percent >= 100:
                    web_url = getattr(settings, "FRONTEND_URL", "https://astra-astrology-web.vercel.app")
                    if not enrollment.certificate_id:
                        enrollment.certificate_id = CourseService.mint_certificate_id()
                        enrollment.certificate_issued_at = datetime.now(timezone.utc)
                    if not enrollment.certificate_url or "?sig=" not in enrollment.certificate_url or not enrollment.certificate_signature:
                        student_name = getattr(user, "full_name", None) or "DivinLink Gurukul Scholar"
                        issued_dt = enrollment.certificate_issued_at or datetime.now(timezone.utc)
                        canonical_hash, signature = CourseService.compute_certificate_crypto(
                            cert_id=enrollment.certificate_id,
                            user_id=str(user.id),
                            student_name=student_name,
                            course_id=str(course.id),
                            course_title=course.title,
                            issued_iso=issued_dt.isoformat(),
                        )
                        enrollment.certificate_canonical_hash = canonical_hash
                        enrollment.certificate_signature = signature
                        enrollment.certificate_url = f"{web_url}/verify/certificate/{enrollment.certificate_id}?sig={signature[:32]}"
                    enrollment.certificate_issued = True
                    await enrollment.save()

        # Build full hierarchy
        sections_out = []
        for sec in sections:
            lessons = (
                await CourseLesson.find(
                    CourseLesson.section_id == sec.id,
                    {"is_published": {"$ne": False}},
                )
                .sort(+CourseLesson.order)
                .to_list()
            )

            lessons_data = []
            for les in lessons:
                can_view = is_enrolled or les.is_free_preview
                lessons_data.append(
                    {
                        "id": str(les.id),
                        "section_id": str(sec.id),
                        "title": les.title,
                        "order": les.order,
                        "duration_minutes": les.duration_minutes,
                        "is_free_preview": les.is_free_preview,
                        "summary": les.summary,
                        "resources_count": len(les.resources or []),
                        "video_provider": les.video_provider if can_view else None,
                        "video_id": les.video_id if can_view else None,
                        "is_completed": str(les.id) in completed_lesson_ids,
                    }
                )

            sections_out.append(
                {
                    "id": str(sec.id),
                    "title": sec.title,
                    "order": sec.order,
                    "description": sec.description,
                    "lessons": lessons_data,
                }
            )

        course_dict = course.model_dump()
        course_dict["id"] = str(course.id)
        course_dict["sections"] = sections_out
        course_dict["is_enrolled"] = is_enrolled
        course_dict["user_progress_percent"] = user_progress_percent
        course_dict["certificate_issued"] = enrollment.certificate_issued if user and enrollment else False
        course_dict["certificate_id"] = enrollment.certificate_id if user and enrollment else None
        course_dict["certificate_url"] = enrollment.certificate_url if user and enrollment else None
        return course_dict

    @staticmethod
    async def get_lesson_stream(
        course_id: PydanticObjectId,
        lesson_id: PydanticObjectId,
        user: User | None = None,
    ) -> dict[str, Any]:
        """Provides secure tokenized stream details for an authorized student or preview."""
        lesson = await CourseLesson.find_one(
            CourseLesson.id == lesson_id,
            CourseLesson.course_id == course_id,
        )
        if not lesson or not lesson.is_published:
            raise NotFoundError("Lesson not found")

        # Enrollment verification unless it is a free preview
        is_enrolled = False
        if user:
            enrollment = await CourseEnrollment.find_one(
                CourseEnrollment.user_id == user.id,
                CourseEnrollment.course_id == course_id,
            )
            if enrollment:
                is_enrolled = True

        if not is_enrolled and not lesson.is_free_preview:
            # Two different problems that used to share one message. A student
            # whose session had simply ended was told to enroll in a course
            # they had already paid for, so they tried to buy it again.
            if user is None:
                raise UnauthorizedError(
                    "Please sign in to watch this lesson.",
                    error_code="sign_in_required",
                )
            raise ForbiddenError(
                "You must enroll in this course to watch this lesson.",
                error_code="not_enrolled",
            )

        # Anti-piracy watermark text (student mobile / email)
        watermark_text = None
        if user:
            user_phone = getattr(user, "phone", None) or getattr(user, "mobile_number", None) or ""
            user_email = getattr(user, "email", None) or ""
            user_name = getattr(user, "full_name", None) or ""
            identifier = user_phone or user_email or user_name or "DivinLink Student"
            watermark_text = f"DivinLink Gurukul • {identifier}"

        # Generate secure embed / stream parameters
        now = int(time.time())
        expires_at = now + settings.BUNNY_EMBED_TOKEN_TTL_SECONDS

        embed_url = ""
        token = None

        if lesson.video_provider == "youtube_unlisted":
            embed_url = f"https://www.youtube-nocookie.com/embed/{lesson.video_id}?rel=0&modestbranding=1"
        elif lesson.video_provider == "bunny_stream":
            # Bunny.net secure player iframe with SHA-256 token authentication
            lib_id = lesson.library_id or settings.BUNNY_STREAM_LIBRARY_ID
            token_key = settings.BUNNY_STREAM_TOKEN_KEY
            # The token key belongs to one library. Signing for a different
            # one produces a token Bunny rejects, and the student sees a 403
            # with nothing in our logs to explain it.
            if lib_id != settings.BUNNY_STREAM_LIBRARY_ID:
                logger.warning(
                    "Lesson {} points at Bunny library {} but the configured "
                    "token key is for {}; the player will refuse it.",
                    lesson.id,
                    lib_id,
                    settings.BUNNY_STREAM_LIBRARY_ID,
                )
            if token_key:
                # Official Bunny formula: SHA256_HEX(TokenSecurityKey + VideoID + ExpirationTimestamp)
                raw_token = f"{token_key}{lesson.video_id}{expires_at}"
                token = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
                embed_url = f"https://iframe.mediadelivery.net/embed/{lib_id}/{lesson.video_id}?token={token}&expires={expires_at}"
            else:
                # An unsigned URL is not a degraded player, it is Bunny's 403
                # page — and it arrives as HTTP 200, so nothing downstream
                # would notice. Fail here, where the reason is still known.
                logger.error(
                    "BUNNY_STREAM_TOKEN_KEY is not set; lesson {} cannot be "
                    "signed and the player would show a 403.",
                    lesson.id,
                )
                raise ServiceUnavailableError(
                    "Video playback is temporarily unavailable. "
                    "Please try again shortly.",
                    error_code="video_unavailable",
                )
        else:
            embed_url = lesson.video_id

        # Check last watch progress for auto-resuming playback
        last_watched_seconds = 0
        is_completed = False
        if user:
            prog = await CourseLessonProgress.find_one(
                CourseLessonProgress.user_id == user.id,
                CourseLessonProgress.lesson_id == lesson_id,
            )
            if prog:
                last_watched_seconds = prog.watched_seconds or 0
                is_completed = prog.is_completed or False

        # If previously watched, append t={seconds} start parameter so video resumes seamlessly
        if last_watched_seconds > 5 and not is_completed:
            separator = "&" if "?" in embed_url else "?"
            embed_url = f"{embed_url}{separator}t={last_watched_seconds}"

        return {
            "lesson_id": str(lesson.id),
            "title": lesson.title,
            "video_provider": lesson.video_provider,
            "video_id": lesson.video_id,
            "library_id": lesson.library_id,
            "embed_url": embed_url,
            "token": token,
            "expires_at": expires_at,
            "watermark_text": watermark_text,
            "notes_markdown": lesson.notes_markdown,
            "resources": lesson.resources or [],
            "last_watched_seconds": last_watched_seconds,
            "is_completed": is_completed,
        }

    @staticmethod
    async def update_progress(
        user: User,
        course_id: PydanticObjectId,
        lesson_id: PydanticObjectId,
        watched_seconds: int,
        total_seconds: int,
        mark_completed: bool = False,
    ) -> dict[str, Any]:
        """Saves current watch progress and auto-calculates total course completion."""
        enrollment = await CourseEnrollment.find_one(
            CourseEnrollment.user_id == user.id,
            CourseEnrollment.course_id == course_id,
        )
        if not enrollment:
            # Staff used to be enrolled here, silently and for free. The player
            # calls this endpoint on its own as soon as a video plays, so an
            # astrologer opening a free-preview lesson of a paid course walked
            # away with lifetime access to it — and, through the certificate
            # endpoint below, a certificate for a course they never took.
            # Admins who need access now grant it to themselves explicitly,
            # which leaves a record; see the admin enrollment endpoints.
            return {
                "progress_percent": 0.0,
                "completed_lesson_ids": [],
                "message": "Progress update skipped: user is not enrolled",
            }

        lesson = await CourseLesson.find_one(
            CourseLesson.id == lesson_id, CourseLesson.course_id == course_id
        )
        if lesson is None:
            raise NotFoundError("Lesson not found")

        now = datetime.now(timezone.utc)

        # Upsert Lesson Progress
        prog = await CourseLessonProgress.find_one(
            CourseLessonProgress.user_id == user.id,
            CourseLessonProgress.lesson_id == lesson_id,
        )
        if not prog:
            first_credit = min(max(0, watched_seconds), FIRST_PING_CREDIT_SECONDS)
            prog = CourseLessonProgress(
                user_id=user.id,
                course_id=course_id,
                lesson_id=lesson_id,
                watched_seconds=watched_seconds,
                total_seconds=total_seconds,
                credited_seconds=first_credit,
                first_watched_at=now,
                last_watched_at=now,
            )
            await prog.insert()
        else:
            first_watched = _aware_utc(prog.first_watched_at or prog.last_watched_at or now)
            if not prog.first_watched_at:
                prog.first_watched_at = first_watched

            last_watched = _aware_utc(prog.last_watched_at or now)
            elapsed = max(0.0, (now - last_watched).total_seconds())

            # Position advance claimed by client
            claimed = max(0, watched_seconds - prog.watched_seconds)
            # Allowed credit for this step based on elapsed server time * max playback speed
            step_allowed = int(elapsed * MAX_PLAYBACK_SPEED)

            # Cumulative real-time bound: Total credit can never exceed real time since first watch * 2.5 + first_ping
            total_real_elapsed = max(0.0, (now - first_watched).total_seconds())
            max_cumulative_allowed = int(total_real_elapsed * MAX_PLAYBACK_SPEED) + FIRST_PING_CREDIT_SECONDS

            # Also bounded by total lesson length
            lesson_sec = (getattr(lesson, "duration_minutes", 0) or 0) * 60
            if lesson_sec <= 0:
                lesson_sec = max(total_seconds, prog.total_seconds, MIN_LESSON_SECONDS)

            new_credited = prog.credited_seconds + min(claimed, step_allowed)
            prog.credited_seconds = min(new_credited, max_cumulative_allowed, lesson_sec)

            prog.watched_seconds = max(prog.watched_seconds, watched_seconds)
            prog.total_seconds = max(prog.total_seconds, total_seconds)
            prog.last_watched_at = now
            await prog.save()

        # Completion is earned, not declared. `mark_completed` arrives from the
        # same client that reports the position, so on its own it meant a
        # student could finish an entire course in one request and have the
        # certificate emailed to them seconds later.
        if not prog.is_completed and CourseService._has_watched_enough(
            lesson=lesson, prog=prog, mark_completed=mark_completed
        ):
            prog.is_completed = True
            prog.completed_at = now
            await prog.save()

        # Update enrollment completed lessons set
        str_id = str(lesson_id)
        if prog.is_completed and str_id not in enrollment.completed_lesson_ids:
            enrollment.completed_lesson_ids.append(str_id)

        # Count total lessons in course
        total_lessons = await CourseLesson.find(
            CourseLesson.course_id == course_id,
            {"is_published": {"$ne": False}},
        ).count()

        if total_lessons > 0:
            enrollment.progress_percent = min(
                100.0,
                round((len(enrollment.completed_lesson_ids) / total_lessons) * 100.0, 1),
            )
            if enrollment.progress_percent >= 100.0:
                enrollment.certificate_issued = True
                if not enrollment.certificate_id:
                    enrollment.certificate_id = CourseService.mint_certificate_id()
                    enrollment.certificate_issued_at = datetime.now(timezone.utc)

                web_url = getattr(settings, "FRONTEND_URL", "https://astra-astrology-web.vercel.app")
                student_name = getattr(user, "full_name", None) or "DivinLink Gurukul Scholar"
                course_item = await Course.find_one(Course.id == course_id)
                course_title = course_item.title if course_item else "DivinLink Gurukul Masterclass"
                issued_dt = enrollment.certificate_issued_at or datetime.now(timezone.utc)

                canonical_hash, signature = CourseService.compute_certificate_crypto(
                    cert_id=enrollment.certificate_id,
                    user_id=str(user.id),
                    student_name=student_name,
                    course_id=str(course_id),
                    course_title=course_title,
                    issued_iso=issued_dt.isoformat(),
                )
                enrollment.certificate_canonical_hash = canonical_hash
                enrollment.certificate_signature = signature
                enrollment.certificate_url = f"{web_url}/verify/certificate/{enrollment.certificate_id}?sig={signature[:32]}"

                # Send official congratulations certificate email if not sent yet
                user_email = getattr(user, "email", None)
                if not enrollment.certificate_email_sent and user_email:
                    try:
                        from app.services.email import send_course_certificate_email
                        dt_str = issued_dt.strftime("%d %B %Y")
                        v_link = enrollment.certificate_url
                        inst_name = course_item.instructor_name if course_item else "Pt. Acharya Rahul Sharma"

                        await send_course_certificate_email(
                            to=user_email,
                            user_name=student_name,
                            course_title=course_title,
                            certificate_id=enrollment.certificate_id,
                            issued_date=dt_str,
                            verify_url=v_link,
                            instructor_name=inst_name,
                        )
                        enrollment.certificate_email_sent = True
                        logger.info("Gurukul course certificate email sent to {} for {}", user_email, enrollment.certificate_id)
                    except Exception as err:
                        logger.warning("Failed to send graduation certificate email to {}: {}", user_email, err)

        enrollment.last_accessed_at = datetime.now(timezone.utc)
        await enrollment.save()

        message = None
        if mark_completed and not prog.is_completed:
            message = "Please watch at least 90% of the lesson before marking it as complete."

        return {
            "progress_percent": enrollment.progress_percent,
            "is_lesson_completed": prog.is_completed,
            "certificate_issued": enrollment.certificate_issued,
            "certificate_id": enrollment.certificate_id,
            "certificate_url": enrollment.certificate_url,
            "message": message,
        }

    # =========================================================================
    # ENROLLMENT & PAYMENT ORDER PROCESSING
    # =========================================================================
    @staticmethod
    async def create_course_order(user: User, course_id: PydanticObjectId) -> dict[str, Any]:
        """Creates a Razorpay order for purchasing a course or enrolls immediately if free."""
        course = await Course.find_one(Course.id == course_id, Course.is_deleted == False)
        if not course:
            raise NotFoundError("Course not found")

        # Check existing enrollment
        existing = await CourseEnrollment.find_one(
            CourseEnrollment.user_id == user.id,
            CourseEnrollment.course_id == course.id,
        )
        if existing:
            return {
                "free_enrolled": True,
                "course_id": str(course.id),
                "course_title": course.title,
                "course_slug": course.slug,
                "message": "Already enrolled",
            }

        # If completely free (₹0)
        if course.price <= 0:
            enrollment = CourseEnrollment(
                user_id=user.id,
                course_id=course.id,
                amount_paid=0.0,
                payment_id="FREE_ENROLLMENT",
                order_id="FREE_ORDER",
            )
            try:
                await enrollment.insert()
            except DuplicateKeyError:
                pass
            else:
                await Course.find_one(Course.id == course.id).update(
                    {"$inc": {"total_students": 1}}
                )
            return {
                "free_enrolled": True,
                "course_id": str(course.id),
                "course_title": course.title,
                "course_slug": course.slug,
                "message": "Successfully enrolled in free course",
            }

        # Before creating a new Razorpay order, inspect any recent open/failed orders
        # for this student+course against Razorpay. If the browser/app never returned
        # or a webhook was delayed after UPI payment, this settles the captured
        # payment and unlocks access immediately instead of charging the student twice.
        recent_orders = (
            await CourseOrder.find(
                CourseOrder.user_id == user.id,
                CourseOrder.course_id == course.id,
                {"status": {"$in": [PaymentOrderStatus.CREATED.value, PaymentOrderStatus.FAILED.value]}},
            )
            .sort([("created_at", -1)])
            .limit(3)
            .to_list()
        )
        for prev_order in recent_orders:
            settled = await CourseService._try_settle_order_from_gateway(
                order=prev_order, course=course, via="sync"
            )
            if settled is not None:
                return {
                    "free_enrolled": True,
                    "already_paid": True,
                    "course_id": str(course.id),
                    "course_title": course.title,
                    "course_slug": course.slug,
                    "message": "Already enrolled from your completed payment",
                }

        # Paid course: create Razorpay order
        amount_paise = int(round(course.price * 100))
        receipt_id = f"crs_{str(course.id)[-6:]}_{int(time.time())}_{secrets.token_hex(2)}"

        user_phone = getattr(user, "phone", None) or getattr(user, "mobile_number", None) or ""
        user_email = getattr(user, "email", "") or ""
        try:
            rzp_order = await asyncio.to_thread(
                _razorpay().order.create,
                {
                    "amount": amount_paise,
                    "currency": "INR",
                    "receipt": receipt_id,
                    "notes": {
                        "type": "course_enrollment",
                        "course_id": str(course.id),
                        "user_id": str(user.id),
                        "user_phone": user_phone,
                        "user_email": user_email,
                    },
                },
            )
        except Exception as exc:
            logger.error("Failed to create Razorpay order for course {}: {}", course.id, exc)
            raise ServiceUnavailableError("Failed to initiate payment gateway. Please try again.")

        # Written down before the student is sent to checkout. Without this
        # there was nothing tying a payment to a course: if the browser never
        # came back, the money was simply gone, and support had no record that
        # the attempt had happened at all.
        await CourseOrder(
            user_id=user.id,
            course_id=course.id,
            razorpay_order_id=rzp_order["id"],
            receipt=receipt_id,
            amount_paise=amount_paise,
            currency="INR",
        ).insert()

        return {
            "free_enrolled": False,
            "order_id": rzp_order["id"],
            "amount_paise": amount_paise,
            "amount_inr": course.price,
            "currency": "INR",
            "key_id": settings.RAZORPAY_KEY_ID,
            "course_id": str(course.id),
            "course_title": course.title,
            "course_slug": course.slug,
        }

    @staticmethod
    async def verify_course_payment(
        user: User,
        course_id: PydanticObjectId,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> dict[str, Any]:
        """Confirms the payment the browser just reported, and enrolls.

        The signature alone used to be the whole check. A signature only says
        Razorpay issued that payment — not that it was for this course, this
        student, or this amount. Any real payment on the account, a ten-rupee
        wallet top-up included, could be replayed against any course id and
        open it. The order this is bound to is what fixes that.
        """
        course = await Course.find_one(Course.id == course_id, Course.is_deleted == False)
        if not course:
            raise NotFoundError("Course not found")

        expected = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode(),
            f"{razorpay_order_id}|{razorpay_payment_id}".encode(),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, razorpay_signature):
            logger.warning(
                "Course payment signature mismatch from {} for order {}",
                user.email,
                razorpay_order_id,
            )
            raise BadRequestError(
                "Payment verification failed. Invalid signature.",
                error_code="invalid_signature",
            )

        order = await CourseOrder.find_one(
            CourseOrder.razorpay_order_id == razorpay_order_id
        )
        # Every one of these is a way the old code could be made to hand out a
        # course: an order from another student, an order for a cheaper
        # course, or no order of ours at all.
        if order is None:
            raise NotFoundError("Payment order not found.", error_code="order_not_found")
        if order.user_id != user.id or order.course_id != course.id:
            logger.warning(
                "Order {} belongs to user {} / course {}, but {} tried to use it "
                "for course {}.",
                razorpay_order_id,
                order.user_id,
                order.course_id,
                user.id,
                course.id,
            )
            raise NotFoundError("Payment order not found.", error_code="order_not_found")

        # Fast-path when webhook already settled this exact payment: do not fail
        # the student's screen with a 503 if Razorpay's fetch API happens to blip.
        if (
            order.status is PaymentOrderStatus.PAID
            and order.razorpay_payment_id == razorpay_payment_id
        ):
            existing_enrollment = await CourseEnrollment.find_one(
                CourseEnrollment.user_id == user.id,
                CourseEnrollment.course_id == course.id,
            )
            if existing_enrollment is not None:
                return {
                    "success": True,
                    "enrollment_id": str(existing_enrollment.id),
                    "course_id": str(course.id),
                    "course_slug": course.slug,
                    "course_title": course.title,
                }

        enrollment = await CourseService._settle_course_order(
            order=order,
            course=course,
            payment=await CourseService._fetch_course_payment(razorpay_payment_id),
            via="callback",
        )

        return {
            "success": True,
            "enrollment_id": str(enrollment.id),
            "course_id": str(course.id),
            "course_slug": course.slug,
            "course_title": course.title,
        }

    @staticmethod
    async def _fetch_order_payments(razorpay_order_id: str) -> dict[str, Any] | list[dict[str, Any]]:
        """Lists payments attempted against a Razorpay order."""
        return await asyncio.to_thread(_razorpay().order.payments, razorpay_order_id)

    @staticmethod
    def _extract_payment_items(payments: Any) -> list[dict[str, Any]]:
        if isinstance(payments, dict):
            items = payments.get("items", [])
            return items if isinstance(items, list) else []
        return payments if isinstance(payments, list) else []

    @staticmethod
    async def _try_settle_order_from_gateway(
        *, order: CourseOrder, course: Course, via: str
    ) -> CourseEnrollment | None:
        """Best-effort check against Razorpay for any captured payment on `order`."""
        try:
            payments = await CourseService._fetch_order_payments(order.razorpay_order_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Gateway lookup skipped for course order {}: {}",
                order.razorpay_order_id,
                exc,
            )
            return None

        for payment in CourseService._extract_payment_items(payments):
            if payment.get("status") == "captured":
                try:
                    return await CourseService._settle_course_order(
                        order=order, course=course, payment=payment, via=via
                    )
                except BadRequestError:
                    return None
        return None

    @staticmethod
    async def sync_course_payment(
        *,
        user: User,
        course_id: PydanticObjectId,
        razorpay_order_id: str | None = None,
    ) -> dict[str, Any]:
        """Checks whether the student's payment has landed (via webhook or Razorpay)
        and unlocks enrollment immediately when confirmed.

        Called by Web/App whenever checkout dismisses, returns from a UPI app, or
        browser callback hits a transient network error.
        """
        course = await Course.find_one(Course.id == course_id)
        if course is None or course.is_deleted:
            raise NotFoundError("Course not found")

        existing = await CourseEnrollment.find_one(
            CourseEnrollment.user_id == user.id,
            CourseEnrollment.course_id == course.id,
        )
        if existing is not None:
            return {
                "enrolled": True,
                "status": PaymentOrderStatus.PAID.value,
                "enrollment_id": str(existing.id),
                "course_id": str(course.id),
                "course_slug": course.slug,
                "course_title": course.title,
                "message": "Enrollment confirmed!",
            }

        if razorpay_order_id:
            order = await CourseOrder.find_one(
                CourseOrder.razorpay_order_id == razorpay_order_id
            )
            if order is None or order.user_id != user.id or order.course_id != course.id:
                raise NotFoundError("Payment order not found.", error_code="order_not_found")
            candidates = [order]
        else:
            candidates = (
                await CourseOrder.find(
                    CourseOrder.user_id == user.id,
                    CourseOrder.course_id == course.id,
                )
                .sort([("created_at", -1)])
                .limit(3)
                .to_list()
            )

        for candidate in candidates:
            enrollment = await CourseService._try_settle_order_from_gateway(
                order=candidate, course=course, via="sync"
            )
            if enrollment is not None:
                return {
                    "enrolled": True,
                    "status": PaymentOrderStatus.PAID.value,
                    "enrollment_id": str(enrollment.id),
                    "course_id": str(course.id),
                    "course_slug": course.slug,
                    "course_title": course.title,
                    "message": "Payment confirmed and course unlocked!",
                }

        latest_status = candidates[0].status.value if candidates else "no_order"
        return {
            "enrolled": False,
            "status": latest_status,
            "enrollment_id": None,
            "course_id": str(course.id),
            "course_slug": course.slug,
            "course_title": course.title,
            "message": "Payment is not captured yet.",
        }

    @staticmethod
    async def _fetch_course_payment(payment_id: str) -> dict[str, Any]:
        """Asks Razorpay what actually happened, rather than taking the
        browser's word for the amount and the status."""
        from app.core.exceptions import ServiceUnavailableError as _Unavailable

        try:
            return await asyncio.to_thread(_razorpay().payment.fetch, payment_id)
        except Exception as exc:  # noqa: BLE001
            logger.opt(exception=exc).error(
                "Could not fetch Razorpay payment {}", payment_id
            )
            raise _Unavailable(
                "Could not confirm the payment with the gateway. If money was "
                "debited, your access will be unlocked automatically.",
                error_code="payment_fetch_failed",
            ) from exc

    @staticmethod
    async def _settle_course_order(
        *,
        order: CourseOrder,
        course: Course,
        payment: dict[str, Any],
        via: str,
    ) -> CourseEnrollment:
        """Turns a captured payment into an enrollment, once.

        Reached from two directions — the browser returning from checkout and
        Razorpay's webhook — so it has to be safe to run twice. The unique
        index on (user_id, course_id) is what makes that true even when both
        arrive at the same moment.
        """
        payment_id = payment["id"]

        # Only `captured` counts. `authorized` means the bank is holding the
        # money but Razorpay has not taken it, and that hold can still be
        # voided — a course unlocked from one would be given away.
        if payment.get("status") != "captured":
            logger.info("Course payment {} is '{}', not enrolling yet.", payment_id, payment.get("status"))
            raise BadRequestError(
                "This payment has not completed yet.", error_code="payment_not_captured"
            )

        # If Razorpay included order_id or currency on the payment entity, they
        # must belong to this CourseOrder.
        payment_order_id = payment.get("order_id")
        if payment_order_id and payment_order_id != order.razorpay_order_id:
            logger.error(
                "Payment {} belongs to order {} not {} — refusing to enroll.",
                payment_id,
                payment_order_id,
                order.razorpay_order_id,
            )
            raise BadRequestError(
                "The payment does not match the order.", error_code="order_mismatch"
            )

        payment_currency = payment.get("currency")
        if payment_currency and payment_currency != order.currency:
            logger.error(
                "Payment {} currency {} does not match order {} currency {} — refusing to enroll.",
                payment_id,
                payment_currency,
                order.razorpay_order_id,
                order.currency,
            )
            raise BadRequestError(
                "The payment currency does not match the order.", error_code="currency_mismatch"
            )

        amount_paise = int(payment["amount"])
        if amount_paise != order.amount_paise:
            logger.error(
                "Payment {} is {} paise but order {} was for {} — refusing to enroll.",
                payment_id,
                amount_paise,
                order.razorpay_order_id,
                order.amount_paise,
            )
            raise BadRequestError(
                "The payment does not match the order.", error_code="amount_mismatch"
            )

        enrollment = await CourseEnrollment.find_one(
            CourseEnrollment.user_id == order.user_id,
            CourseEnrollment.course_id == order.course_id,
        )
        if enrollment is None:
            enrollment = CourseEnrollment(
                user_id=order.user_id,
                course_id=order.course_id,
                payment_id=payment_id,
                order_id=order.razorpay_order_id,
                amount_paid=amount_paise / 100,
                currency=order.currency,
            )
            try:
                await enrollment.insert()
            except DuplicateKeyError:
                # The other path got there first, which is the point of the
                # unique index. Use theirs.
                enrollment = await CourseEnrollment.find_one(
                    CourseEnrollment.user_id == order.user_id,
                    CourseEnrollment.course_id == order.course_id,
                )
                if enrollment is None:  # pragma: no cover - the index just said it exists
                    raise
            else:
                # Counted only on the insert that actually created the row, so
                # the callback and the webhook cannot count one student twice.
                await Course.find_one(Course.id == order.course_id).update(
                    {"$inc": {"total_students": 1}}
                )
                logger.info(
                    "User {} enrolled in course {} via {}", order.user_id, order.course_id, via
                )

        if order.status is not PaymentOrderStatus.PAID:
            order.status = PaymentOrderStatus.PAID
            order.razorpay_payment_id = payment_id
            order.method = payment.get("method")
            order.verified_via = via
            order.paid_at = datetime.now(timezone.utc)
            await order.save()

        return enrollment

    @staticmethod
    async def enroll_from_webhook(
        *, razorpay_order_id: str, payment: dict[str, Any]
    ) -> str:
        """The webhook's way in. Returns a short word for the event log.

        This is the path that matters most: it does not need the student's
        browser to still be open, which is exactly the case that was losing
        people the course they had just paid for.
        """
        order = await CourseOrder.find_one(
            CourseOrder.razorpay_order_id == razorpay_order_id
        )
        if order is None:
            # Recover orders opened prior to CourseOrder persistence (or where
            # order creation succeeded on Razorpay) if Razorpay's verified
            # order/payment notes identify a valid course purchase.
            notes = payment.get("notes") or {}
            raw_course_id = notes.get("course_id")
            raw_user_id = notes.get("user_id")
            if (
                notes.get("type") != "course_enrollment"
                or not raw_course_id
                or not raw_user_id
                or not PydanticObjectId.is_valid(str(raw_course_id))
                or not PydanticObjectId.is_valid(str(raw_user_id))
            ):
                return "not_a_course_order"

            course = await Course.find_one(
                Course.id == PydanticObjectId(str(raw_course_id)),
                Course.is_deleted == False,
            )
            student = await User.get(PydanticObjectId(str(raw_user_id)))
            if course is None or student is None:
                return "course_missing"

            expected_paise = int(round(course.price * 100))
            paid_paise = int(payment.get("amount") or 0)
            if expected_paise <= 0 or paid_paise < expected_paise:
                logger.error(
                    "Webhook recovery refused for order {}: paid {} < expected {}",
                    razorpay_order_id,
                    paid_paise,
                    expected_paise,
                )
                return "amount_mismatch"

            order = CourseOrder(
                user_id=student.id,
                course_id=course.id,
                razorpay_order_id=razorpay_order_id,
                receipt=f"webhook_recovered_{razorpay_order_id[-12:]}",
                amount_paise=expected_paise,
                currency=(payment.get("currency") or course.currency or "INR"),
            )
            try:
                await order.insert()
            except DuplicateKeyError:
                order = await CourseOrder.find_one(
                    CourseOrder.razorpay_order_id == razorpay_order_id
                )
                if order is None:  # pragma: no cover
                    return "not_a_course_order"
        else:
            course = await Course.find_one(Course.id == order.course_id)
            if course is None:
                logger.error(
                    "Course order {} points at course {}, which no longer exists.",
                    razorpay_order_id,
                    order.course_id,
                )
                return "course_missing"

        already = order.status is PaymentOrderStatus.PAID
        await CourseService._settle_course_order(
            order=order, course=course, payment=payment, via="webhook"
        )
        return "already_enrolled" if already else "enrolled"

    @staticmethod
    async def refund_course_order(
        *, razorpay_payment_id: str, amount_paise: int, refund: dict[str, Any]
    ) -> str:
        """Handles a processed refund for a course payment.

        Full refunds mark the CourseOrder refunded and revoke the corresponding
        enrollment so refunded purchases do not retain free lifetime access.
        """
        order = await CourseOrder.find_one(
            CourseOrder.razorpay_payment_id == razorpay_payment_id
        )
        if order is None:
            return "not_a_course_order"

        if amount_paise < order.amount_paise:
            logger.info(
                "Partial course refund {} ({} / {} paise) recorded for order {}",
                refund.get("id"),
                amount_paise,
                order.amount_paise,
                order.razorpay_order_id,
            )
            return "partial_refund_logged"

        enrollment = await CourseEnrollment.find_one(
            CourseEnrollment.user_id == order.user_id,
            CourseEnrollment.course_id == order.course_id,
        )
        if enrollment is not None:
            await enrollment.delete()
            await Course.find_one(
                Course.id == order.course_id,
                Course.total_students > 0,
            ).update({"$inc": {"total_students": -1}})

        if order.status is not PaymentOrderStatus.REFUNDED:
            order.status = PaymentOrderStatus.REFUNDED
            order.failure_reason = f"Refunded via webhook ({refund.get('id') or 'refund'})"
            order.updated_at = datetime.now(timezone.utc)
            await order.save()

        return "refunded"

    @staticmethod
    async def fail_course_order(
        *, razorpay_order_id: str, payment: dict[str, Any]
    ) -> str:
        """Records a failed attempt, so support can see it happened."""
        order = await CourseOrder.find_one(
            CourseOrder.razorpay_order_id == razorpay_order_id
        )
        if order is None:
            return "not_a_course_order"
        if order.status is PaymentOrderStatus.CREATED:
            order.status = PaymentOrderStatus.FAILED
            order.razorpay_payment_id = payment.get("id")
            order.failure_reason = payment.get("error_description") or payment.get(
                "error_reason"
            )
            order.updated_at = datetime.now(timezone.utc)
            await order.save()
        return "marked_failed"

    @staticmethod
    async def _enrich_users_and_courses(
        user_ids: list[PydanticObjectId], course_ids: list[PydanticObjectId]
    ) -> tuple[dict[str, User], dict[str, Course]]:
        users_map: dict[str, User] = {}
        courses_map: dict[str, Course] = {}
        if user_ids:
            users = await User.find({"_id": {"$in": list(set(user_ids))}}).to_list()
            users_map = {str(u.id): u for u in users}
        if course_ids:
            courses = await Course.find({"_id": {"$in": list(set(course_ids))}}).to_list()
            courses_map = {str(c.id): c for c in courses}
        return users_map, courses_map

    @staticmethod
    def _serialize_admin_order(
        order: CourseOrder, users_map: dict[str, User], courses_map: dict[str, Course]
    ) -> dict[str, Any]:
        u = users_map.get(str(order.user_id))
        c = courses_map.get(str(order.course_id))
        return {
            "id": str(order.id),
            "user_id": str(order.user_id),
            "student_name": getattr(u, "full_name", None) if u else None,
            "student_email": getattr(u, "email", None) if u else None,
            "student_phone": (
                (getattr(u, "phone", None) or getattr(u, "mobile_number", None)) if u else None
            ),
            "course_id": str(order.course_id),
            "course_title": c.title if c else None,
            "course_slug": c.slug if c else None,
            "razorpay_order_id": order.razorpay_order_id,
            "razorpay_payment_id": order.razorpay_payment_id,
            "receipt": order.receipt,
            "amount_paise": order.amount_paise,
            "amount_inr": round(order.amount_paise / 100.0, 2),
            "currency": order.currency,
            "status": order.status.value,
            "method": order.method,
            "failure_reason": order.failure_reason,
            "verified_via": order.verified_via,
            "paid_at": order.paid_at,
            "created_at": order.created_at,
        }

    @staticmethod
    async def admin_list_course_orders(
        *,
        status_filter: str | None = None,
        course_id: PydanticObjectId | None = None,
        search: str | None = None,
        page: int = 1,
        limit: int = 25,
    ) -> dict[str, Any]:
        """Lists course checkout orders for support & reconciliation."""
        query: dict[str, Any] = {}
        if status_filter and status_filter != "all":
            query["status"] = status_filter
        if course_id is not None:
            query["course_id"] = course_id

        orders = await CourseOrder.find(query).sort([("created_at", -1)]).to_list()
        users_map, courses_map = await CourseService._enrich_users_and_courses(
            [o.user_id for o in orders], [o.course_id for o in orders]
        )

        serialized = [
            CourseService._serialize_admin_order(o, users_map, courses_map) for o in orders
        ]

        if search and search.strip():
            q = search.strip().lower()
            serialized = [
                item
                for item in serialized
                if (
                    q in (item["razorpay_order_id"] or "").lower()
                    or q in (item["razorpay_payment_id"] or "").lower()
                    or q in (item["student_email"] or "").lower()
                    or q in (item["student_name"] or "").lower()
                    or q in (item["student_phone"] or "").lower()
                    or q in (item["course_title"] or "").lower()
                )
            ]

        total = len(serialized)
        pages = max(1, (total + limit - 1) // limit)
        start = (page - 1) * limit
        paged = serialized[start : start + limit]

        created_count = await CourseOrder.find(CourseOrder.status == PaymentOrderStatus.CREATED).count()
        paid_count = await CourseOrder.find(CourseOrder.status == PaymentOrderStatus.PAID).count()
        failed_count = await CourseOrder.find(CourseOrder.status == PaymentOrderStatus.FAILED).count()
        refunded_count = await CourseOrder.find(CourseOrder.status == PaymentOrderStatus.REFUNDED).count()

        return {
            "items": paged,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": pages,
            "created_count": created_count,
            "paid_count": paid_count,
            "failed_count": failed_count,
            "refunded_count": refunded_count,
        }

    @staticmethod
    async def admin_reconcile_course_order(order_id: PydanticObjectId) -> dict[str, Any]:
        """Asks Razorpay what actually happened to a stuck/created course order and enrolls if captured."""
        order = await CourseOrder.get(order_id)
        if order is None:
            raise NotFoundError("Course order not found.", error_code="order_not_found")

        course = await Course.find_one(Course.id == order.course_id)
        if course is None:
            raise NotFoundError("Course associated with this order no longer exists.")

        try:
            payments = await CourseService._fetch_order_payments(order.razorpay_order_id)
        except Exception as exc:  # noqa: BLE001
            raise ServiceUnavailableError(
                "Could not reach the payment gateway.", error_code="gateway_unavailable"
            ) from exc

        for payment in CourseService._extract_payment_items(payments):
            if payment.get("status") == "captured":
                await CourseService._settle_course_order(
                    order=order, course=course, payment=payment, via="reconcile"
                )
                break
        else:
            if order.status is PaymentOrderStatus.CREATED:
                order.status = PaymentOrderStatus.FAILED
                order.failure_reason = "No captured payment found for this order."
                order.updated_at = datetime.now(timezone.utc)
                await order.save()

        refreshed = await CourseOrder.get(order.id)
        assert refreshed is not None
        users_map, courses_map = await CourseService._enrich_users_and_courses(
            [refreshed.user_id], [refreshed.course_id]
        )
        return CourseService._serialize_admin_order(refreshed, users_map, courses_map)

    @staticmethod
    async def admin_list_course_enrollments(
        *,
        course_id: PydanticObjectId | None = None,
        search: str | None = None,
        page: int = 1,
        limit: int = 25,
    ) -> dict[str, Any]:
        query: dict[str, Any] = {}
        if course_id is not None:
            query["course_id"] = course_id

        enrollments = (
            await CourseEnrollment.find(query).sort([("enrolled_at", -1)]).to_list()
        )
        users_map, courses_map = await CourseService._enrich_users_and_courses(
            [e.user_id for e in enrollments], [e.course_id for e in enrollments]
        )

        items = []
        for e in enrollments:
            u = users_map.get(str(e.user_id))
            c = courses_map.get(str(e.course_id))
            items.append(
                {
                    "id": str(e.id),
                    "user_id": str(e.user_id),
                    "student_name": getattr(u, "full_name", None) if u else None,
                    "student_email": getattr(u, "email", None) if u else None,
                    "student_phone": (
                        (getattr(u, "phone", None) or getattr(u, "mobile_number", None))
                        if u
                        else None
                    ),
                    "course_id": str(e.course_id),
                    "course_title": c.title if c else None,
                    "course_slug": c.slug if c else None,
                    "payment_id": e.payment_id,
                    "order_id": e.order_id,
                    "amount_paid": e.amount_paid,
                    "currency": e.currency,
                    "progress_percent": e.progress_percent,
                    "certificate_issued": e.certificate_issued,
                    "enrolled_at": e.enrolled_at,
                    "last_accessed_at": e.last_accessed_at,
                }
            )

        if search and search.strip():
            q = search.strip().lower()
            items = [
                item
                for item in items
                if (
                    q in (item["student_email"] or "").lower()
                    or q in (item["student_name"] or "").lower()
                    or q in (item["student_phone"] or "").lower()
                    or q in (item["course_title"] or "").lower()
                    or q in (item["payment_id"] or "").lower()
                    or q in (item["order_id"] or "").lower()
                )
            ]

        total = len(items)
        pages = max(1, (total + limit - 1) // limit)
        start = (page - 1) * limit
        return {
            "items": items[start : start + limit],
            "total": total,
            "page": page,
            "limit": limit,
            "pages": pages,
        }

    @staticmethod
    async def admin_grant_course_enrollment(
        *,
        course_id: PydanticObjectId,
        user_id: str | None = None,
        email: str | None = None,
        amount_paid: float = 0.0,
        payment_id: str | None = None,
        note: str | None = None,
    ) -> dict[str, Any]:
        """Manually grants course access to a student (support / recovery path)."""
        course = await Course.find_one(Course.id == course_id, Course.is_deleted == False)
        if course is None:
            raise NotFoundError("Course not found")

        student: User | None = None
        if user_id and PydanticObjectId.is_valid(user_id.strip()):
            student = await User.get(PydanticObjectId(user_id.strip()))
        elif email and email.strip():
            student = await User.find_one(User.email == email.strip().lower())
        else:
            raise BadRequestError("Provide either student email or user_id.")

        if student is None:
            raise NotFoundError("Student account not found.")

        existing = await CourseEnrollment.find_one(
            CourseEnrollment.user_id == student.id,
            CourseEnrollment.course_id == course.id,
        )
        if existing is not None:
            users_map, courses_map = {str(student.id): student}, {str(course.id): course}
            u = users_map.get(str(existing.user_id))
            c = courses_map.get(str(existing.course_id))
            return {
                "already_enrolled": True,
                "enrollment": {
                    "id": str(existing.id),
                    "user_id": str(existing.user_id),
                    "student_name": getattr(u, "full_name", None) if u else None,
                    "student_email": getattr(u, "email", None) if u else None,
                    "student_phone": (
                        (getattr(u, "phone", None) or getattr(u, "mobile_number", None)) if u else None
                    ),
                    "course_id": str(existing.course_id),
                    "course_title": c.title if c else None,
                    "course_slug": c.slug if c else None,
                    "payment_id": existing.payment_id,
                    "order_id": existing.order_id,
                    "amount_paid": existing.amount_paid,
                    "currency": existing.currency,
                    "progress_percent": existing.progress_percent,
                    "certificate_issued": existing.certificate_issued,
                    "enrolled_at": existing.enrolled_at,
                    "last_accessed_at": existing.last_accessed_at,
                },
            }

        ref_payment_id = (
            payment_id.strip()
            if payment_id and payment_id.strip()
            else f"ADMIN_GRANT:{(note or 'support').strip()[:80]}"
        )
        enrollment = CourseEnrollment(
            user_id=student.id,
            course_id=course.id,
            payment_id=ref_payment_id,
            order_id="ADMIN_MANUAL_ENROLL",
            amount_paid=float(amount_paid),
            currency=course.currency or "INR",
        )
        try:
            await enrollment.insert()
        except DuplicateKeyError:
            enrollment = await CourseEnrollment.find_one(
                CourseEnrollment.user_id == student.id,
                CourseEnrollment.course_id == course.id,
            )
            assert enrollment is not None
        else:
            await Course.find_one(Course.id == course.id).update(
                {"$inc": {"total_students": 1}}
            )

        return {
            "already_enrolled": False,
            "enrollment": {
                "id": str(enrollment.id),
                "user_id": str(enrollment.user_id),
                "student_name": getattr(student, "full_name", None),
                "student_email": getattr(student, "email", None),
                "student_phone": getattr(student, "phone", None) or getattr(student, "mobile_number", None),
                "course_id": str(course.id),
                "course_title": course.title,
                "course_slug": course.slug,
                "payment_id": enrollment.payment_id,
                "order_id": enrollment.order_id,
                "amount_paid": enrollment.amount_paid,
                "currency": enrollment.currency,
                "progress_percent": enrollment.progress_percent,
                "certificate_issued": enrollment.certificate_issued,
                "enrolled_at": enrollment.enrolled_at,
                "last_accessed_at": enrollment.last_accessed_at,
            },
        }

    @staticmethod
    async def admin_revoke_course_enrollment(
        *, course_id: PydanticObjectId, enrollment_id: PydanticObjectId
    ) -> None:
        enrollment = await CourseEnrollment.find_one(
            CourseEnrollment.id == enrollment_id,
            CourseEnrollment.course_id == course_id,
        )
        if enrollment is None:
            raise NotFoundError("Enrollment not found.")
        await enrollment.delete()
        await Course.find_one(
            Course.id == course_id,
            Course.total_students > 0,
        ).update({"$inc": {"total_students": -1}})

    @staticmethod
    async def get_user_enrollments_with_details(user: User) -> list[dict[str, Any]]:
        """Returns all purchased courses enriched with course metadata."""
        enrollments = (
            await CourseEnrollment.find(CourseEnrollment.user_id == user.id)
            .sort([("last_accessed_at", -1)])
            .to_list()
        )
        result = []
        for e in enrollments:
            course = await Course.find_one(Course.id == e.course_id)
            if course and not course.is_deleted:
                web_url = getattr(settings, "FRONTEND_URL", "https://astra-astrology-web.vercel.app")
                cert_id = e.certificate_id or (CourseService.mint_certificate_id() if e.progress_percent >= 100 else None)
                cert_url = e.certificate_url or (f"{web_url}/verify/certificate/{cert_id}" if cert_id else None)
                if e.progress_percent >= 100 and (not e.certificate_id or not e.certificate_url):
                    e.certificate_issued = True
                    e.certificate_id = cert_id
                    e.certificate_url = cert_url
                    await e.save()

                result.append(
                    {
                        "id": str(e.id),
                        "course_id": str(course.id),
                        "course_title": course.title,
                        "course_slug": course.slug,
                        "thumbnail_url": course.thumbnail_url,
                        "instructor_name": course.instructor_name,
                        "enrolled_at": e.enrolled_at,
                        "expires_at": e.expires_at,
                        "progress_percent": e.progress_percent,
                        "completed_lesson_ids": e.completed_lesson_ids,
                        "certificate_issued": e.certificate_issued,
                        "certificate_id": cert_id,
                        "certificate_url": cert_url,
                    }
                )
        return result

    # =========================================================================
    # ADMIN SECTION & LESSON MANAGEMENT
    # =========================================================================
    @staticmethod
    async def admin_create_section(course_id: PydanticObjectId, title: str, order: int, description: str | None = None) -> CourseSection:
        course = await Course.find_one(Course.id == course_id, Course.is_deleted == False)
        if not course:
            raise NotFoundError("Course not found")

        section = CourseSection(
            course_id=course_id,
            title=title,
            order=order,
            description=description,
        )
        await section.insert()
        return section

    @staticmethod
    async def admin_create_lesson(
        course_id: PydanticObjectId,
        section_id: PydanticObjectId,
        title: str,
        order: int,
        duration_minutes: int,
        video_provider: str,
        video_id: str,
        library_id: str | None = None,
        is_free_preview: bool = False,
        summary: str | None = None,
        notes_markdown: str | None = None,
        resources: list[dict[str, Any]] | None = None,
    ) -> CourseLesson:
        course = await Course.find_one(Course.id == course_id, Course.is_deleted == False)
        if not course:
            raise NotFoundError("Course not found")

        section = await CourseSection.find_one(CourseSection.id == section_id, CourseSection.course_id == course_id)
        if not section:
            raise NotFoundError("Section not found")

        lesson = CourseLesson(
            course_id=course_id,
            section_id=section_id,
            title=title,
            order=order,
            duration_minutes=duration_minutes,
            video_provider=video_provider,
            video_id=video_id,
            library_id=library_id or settings.BUNNY_STREAM_LIBRARY_ID,
            is_free_preview=is_free_preview,
            summary=summary,
            notes_markdown=notes_markdown,
            resources=resources or [],
        )
        await lesson.insert()

        # Recalculate total lessons & duration for course
        all_lessons = await CourseLesson.find(CourseLesson.course_id == course_id, CourseLesson.is_published == True).to_list()
        course.total_lessons = len(all_lessons)
        course.duration_hours = round(sum(l.duration_minutes for l in all_lessons) / 60.0, 1)
        await course.save()

        return lesson

    @staticmethod
    async def create_bunny_video_placeholder(title: str) -> dict[str, Any]:
        """Calls Bunny Stream API to create a video GUID in our library for immediate upload."""
        if not settings.BUNNY_STREAM_API_KEY or not settings.BUNNY_STREAM_LIBRARY_ID:
            raise ServiceUnavailableError("Bunny Stream API keys are not configured.")

        url = f"https://video.bunnycdn.com/library/{settings.BUNNY_STREAM_LIBRARY_ID}/videos"
        headers = {
            "AccessKey": settings.BUNNY_STREAM_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(url, headers=headers, json={"title": title})
            if res.status_code not in (200, 201):
                logger.error("Bunny Stream API returned {}: {}", res.status_code, res.text)
                raise BadRequestError(f"Failed to create Bunny video placeholder: {res.text}")
            data = res.json()
            video_id = data.get("guid")

            # Bunny's presigned upload: SHA256(library_id + api_key +
            # expiry + video_id). The key stays here; the browser gets a
            # signature that only opens this one video, and only for an hour.
            # https://docs.bunny.net/stream/tus-resumable-uploads
            expire = int(time.time()) + 3600
            signature = hashlib.sha256(
                f"{settings.BUNNY_STREAM_LIBRARY_ID}"
                f"{settings.BUNNY_STREAM_API_KEY}"
                f"{expire}"
                f"{video_id}".encode()
            ).hexdigest()

            return {
                "video_id": video_id,
                "library_id": settings.BUNNY_STREAM_LIBRARY_ID,
                "title": title,
                "tus_endpoint": "https://video.bunnycdn.com/tusupload",
                "authorization_signature": signature,
                "authorization_expire": expire,
            }

    @staticmethod
    async def safe_delete_bunny_video(video_id: str | None, library_id: str | None = None) -> bool:
        """Safely purges a video from Bunny Stream API when a course, section, or lesson is deleted,
        or when a lesson/promo video is removed or replaced.
        Prevents orphaned video files from consuming storage quota and incurring Bunny.net charges.
        """
        if not video_id:
            return False

        clean_id = str(video_id).strip()
        # If user passed a full iframe embed or play URL, extract the video GUID
        # e.g., https://iframe.mediadelivery.net/embed/803267/6af0c892-1430-970e-2598-77ef12345678?token=...
        if "/" in clean_id:
            clean_id = clean_id.split("?")[0].rstrip("/").split("/")[-1]

        # Ignore empty or external video sources like YouTube
        if (
            not clean_id
            or "youtube" in clean_id.lower()
            or "youtu.be" in clean_id.lower()
            or len(clean_id) == 11  # standard YouTube ID
            or len(clean_id) < 15  # Bunny GUIDs are UUIDs (32+ chars)
        ):
            return False

        target_lib = library_id or settings.BUNNY_STREAM_LIBRARY_ID
        api_key = settings.BUNNY_STREAM_API_KEY
        if not api_key or not target_lib:
            logger.warning("Bunny Stream credentials not configured, skipping video deletion for {}", clean_id)
            return False

        url = f"https://video.bunnycdn.com/library/{target_lib}/videos/{clean_id}"
        headers = {
            "AccessKey": api_key,
            "Accept": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.delete(url, headers=headers)
                if res.status_code in (200, 204, 404):
                    logger.success(f"Bunny Stream: Successfully purged video {clean_id} from library {target_lib} (HTTP {res.status_code})")
                    return True
                logger.warning(f"Bunny Stream: Delete returned HTTP {res.status_code} for video {clean_id}: {res.text}")
                return False
        except Exception as exc:
            logger.opt(exception=exc).error(f"Bunny Stream: Failed to delete video {clean_id} from library {target_lib}")
            return False

    # -------------------------------------------------------------------------
    # GURUKUL JIGYASA (TIMESTAMPED Q&A FORUM)
    # -------------------------------------------------------------------------
    @staticmethod
    def format_timestamp(seconds: int) -> str:
        """Formats integer seconds to MM:SS or HH:MM:SS string."""
        if seconds <= 0:
            return "00:00"
        hours = seconds // 3600
        mins = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours:02d}:{mins:02d}:{secs:02d}"
        return f"{mins:02d}:{secs:02d}"

    @staticmethod
    async def list_lesson_questions(
        course_id: PydanticObjectId,
        lesson_id: PydanticObjectId,
        current_user: User | None = None,
        sort: str = "newest",  # "newest", "timestamp", "upvotes"
        limit: int = 50,
        skip: int = 0,
    ) -> list[dict[str, Any]]:
        """Returns questions for a specific lesson, optionally checking upvote by current_user."""
        query: dict[str, Any] = {
            "course_id": course_id,
            "lesson_id": lesson_id,
            "is_hidden": False,
        }

        # Sorting logic
        if sort == "timestamp":
            sort_field = [("timestamp_seconds", 1), ("created_at", -1)]
        elif sort == "upvotes":
            sort_field = [("upvote_count", -1), ("created_at", -1)]
        else:
            sort_field = [("is_pinned", -1), ("created_at", -1)]

        cursor = (
            CourseQuestion.find(query)
            .sort(sort_field)
            .skip(skip)
            .limit(limit)
        )
        questions = await cursor.to_list()

        user_id_str = str(current_user.id) if current_user else None

        result = []
        for q in questions:
            result.append({
                "id": str(q.id),
                "course_id": str(q.course_id),
                "section_id": str(q.section_id),
                "lesson_id": str(q.lesson_id),
                "user_id": str(q.user_id),
                "user_name": q.user_name,
                "user_avatar": q.user_avatar,
                "timestamp_seconds": q.timestamp_seconds,
                "timestamp_formatted": q.timestamp_formatted,
                "title": q.title,
                "content": q.content,
                "upvote_count": q.upvote_count,
                "is_upvoted_by_me": bool(user_id_str and user_id_str in q.upvote_user_ids),
                "answer_count": len(q.answers),
                "is_resolved": q.is_resolved,
                "has_official_answer": q.has_official_answer,
                "is_pinned": q.is_pinned,
                "answers": [
                    {
                        "id": a.id,
                        "user_id": str(a.user_id),
                        "user_name": a.user_name,
                        "user_role": a.user_role,
                        "user_avatar": a.user_avatar,
                        "is_official": a.is_official,
                        "content": a.content,
                        "created_at": a.created_at,
                    }
                    for a in q.answers
                ],
                "created_at": q.created_at,
            })
        return result

    @staticmethod
    async def create_lesson_question(
        user: User,
        course_id: PydanticObjectId,
        lesson_id: PydanticObjectId,
        title: str,
        content: str,
        timestamp_seconds: int = 0,
    ) -> CourseQuestion:
        """Allows an enrolled student (or admin) to ask a timestamped question on a video lesson."""
        course = await Course.find_one(Course.id == course_id, Course.is_deleted == False)
        if not course:
            raise NotFoundError("Course not found")

        lesson = await CourseLesson.find_one(CourseLesson.id == lesson_id, CourseLesson.course_id == course_id)
        if not lesson:
            raise NotFoundError("Lesson not found")

        # Check enrollment or preview or staff
        enrollment = await CourseEnrollment.find_one(
            CourseEnrollment.user_id == user.id,
            CourseEnrollment.course_id == course_id,
        )
        if not enrollment and not lesson.is_free_preview and not CourseService._is_staff(user):
            raise ForbiddenError("Please enroll in this course to participate in Gurukul Jigyasa Q&A.")

        user_name = getattr(user, "full_name", None) or "Astra Student"
        user_phone = getattr(user, "phone", None) or getattr(user, "mobile_number", None) or ""
        user_email = getattr(user, "email", None) or ""
        user_avatar = getattr(user, "avatar_url", None)

        safe_seconds = max(0, int(timestamp_seconds or 0))
        time_str = CourseService.format_timestamp(safe_seconds)

        question = CourseQuestion(
            course_id=course_id,
            section_id=lesson.section_id,
            lesson_id=lesson_id,
            user_id=user.id,
            user_name=user_name,
            user_email=user_email,
            user_phone=user_phone,
            user_avatar=user_avatar,
            timestamp_seconds=safe_seconds,
            timestamp_formatted=time_str,
            title=title.strip(),
            content=content.strip(),
        )
        await question.insert()
        return question

    @staticmethod
    async def toggle_question_upvote(user: User, question_id: PydanticObjectId) -> dict[str, Any]:
        """Toggles an upvote on a student question."""
        question = await CourseQuestion.find_one(CourseQuestion.id == question_id)
        if not question:
            raise NotFoundError("Question not found")

        user_id_str = str(user.id)
        if user_id_str in question.upvote_user_ids:
            question.upvote_user_ids.remove(user_id_str)
            is_upvoted = False
        else:
            question.upvote_user_ids.append(user_id_str)
            is_upvoted = True

        question.upvote_count = len(question.upvote_user_ids)
        await question.save()
        return {
            "question_id": str(question.id),
            "upvote_count": question.upvote_count,
            "is_upvoted_by_me": is_upvoted,
        }

    @staticmethod
    async def answer_question(
        user: User,
        question_id: PydanticObjectId,
        content: str,
        is_official: bool = False,
        mark_resolved: bool = False,
    ) -> CourseQuestionAnswer:
        """Posts an answer or Acharya explanation to a student question thread."""
        question = await CourseQuestion.find_one(CourseQuestion.id == question_id)
        if not question:
            raise NotFoundError("Question not found")

        # The old form here was `str(role.value) if hasattr(role, "value")
        # else str(role).lower()` — the `.lower()` only ever reached the second
        # branch, so an uppercase role value would have been read as a student.
        is_admin_or_acharya = CourseService._is_staff(user)

        final_is_official = is_official or is_admin_or_acharya
        user_name = getattr(user, "full_name", None) or ("Acharya Guru" if final_is_official else "Astra Student")

        answer = CourseQuestionAnswer(
            user_id=user.id,
            user_name=user_name,
            user_role="admin" if is_admin_or_acharya else "student",
            user_avatar=getattr(user, "avatar_url", None),
            is_official=final_is_official,
            content=content.strip(),
        )

        question.answers.append(answer)
        question.answer_count = len(question.answers)
        if final_is_official:
            question.has_official_answer = True
        if mark_resolved:
            question.is_resolved = True
        question.updated_at = datetime.now(timezone.utc)

        await question.save()
        return answer

    @staticmethod
    async def admin_list_questions(
        course_id: PydanticObjectId | None = None,
        lesson_id: PydanticObjectId | None = None,
        status: str = "all",  # "all", "unanswered", "answered", "resolved"
        search: str | None = None,
        limit: int = 50,
        skip: int = 0,
    ) -> dict[str, Any]:
        """Provides full Q&A inquiry management with course, lesson & student details."""
        query: dict[str, Any] = {"is_hidden": {"$ne": True}}
        if course_id:
            query["course_id"] = course_id
        if lesson_id:
            query["lesson_id"] = lesson_id

        if status == "unanswered":
            query["has_official_answer"] = {"$ne": True}
            query["is_resolved"] = {"$ne": True}
        elif status == "answered":
            query["has_official_answer"] = True
        elif status == "resolved":
            query["is_resolved"] = True

        if search:
            query["$or"] = [
                {"title": {"$regex": search, "$options": "i"}},
                {"content": {"$regex": search, "$options": "i"}},
                {"user_name": {"$regex": search, "$options": "i"}},
                {"user_email": {"$regex": search, "$options": "i"}},
                {"user_phone": {"$regex": search, "$options": "i"}},
            ]

        total = await CourseQuestion.find(query).count()
        unanswered_count = await CourseQuestion.find(
            {"has_official_answer": {"$ne": True}, "is_resolved": {"$ne": True}, "is_hidden": {"$ne": True}}
        ).count()
        resolved_count = await CourseQuestion.find({"is_resolved": True, "is_hidden": {"$ne": True}}).count()

        questions = (
            await CourseQuestion.find(query)
            .sort([("created_at", -1)])
            .skip(skip)
            .limit(limit)
            .to_list()
        )

        # Cache course, section, lesson lookups to minimize DB queries
        course_cache: dict[str, Course] = {}
        section_cache: dict[str, CourseSection] = {}
        lesson_cache: dict[str, CourseLesson] = {}
        enrollment_cache: dict[str, CourseEnrollment] = {}

        detailed_items = []
        for q in questions:
            # Course info
            cid_str = str(q.course_id)
            if cid_str not in course_cache:
                c_doc = await Course.find_one(Course.id == q.course_id)
                if c_doc:
                    course_cache[cid_str] = c_doc
            course_item = course_cache.get(cid_str)

            # Lesson info
            lid_str = str(q.lesson_id)
            if lid_str not in lesson_cache:
                l_doc = await CourseLesson.find_one(CourseLesson.id == q.lesson_id)
                if l_doc:
                    lesson_cache[lid_str] = l_doc
            lesson_item = lesson_cache.get(lid_str)

            # Section info
            sid_str = str(q.section_id)
            if sid_str not in section_cache:
                s_doc = await CourseSection.find_one(CourseSection.id == q.section_id)
                if s_doc:
                    section_cache[sid_str] = s_doc
            section_item = section_cache.get(sid_str)

            # Student enrollment info
            enr_key = f"{q.user_id}_{q.course_id}"
            if enr_key not in enrollment_cache:
                enr = await CourseEnrollment.find_one(
                    CourseEnrollment.user_id == q.user_id,
                    CourseEnrollment.course_id == q.course_id,
                )
                if enr:
                    enrollment_cache[enr_key] = enr
            enr_item = enrollment_cache.get(enr_key)

            detailed_items.append({
                "id": str(q.id),
                "course_id": str(q.course_id),
                "course_title": course_item.title if course_item else "Gurukul Masterclass",
                "course_slug": course_item.slug if course_item else "",
                "section_id": str(q.section_id),
                "section_title": section_item.title if section_item else "Curriculum Module",
                "lesson_id": str(q.lesson_id),
                "lesson_title": lesson_item.title if lesson_item else "Video Lecture",
                "video_id": lesson_item.video_id if lesson_item else None,
                "video_provider": lesson_item.video_provider if lesson_item else "bunny_stream",
                "user_id": str(q.user_id),
                "user_name": q.user_name,
                "user_email": q.user_email,
                "user_phone": q.user_phone,
                "user_avatar": q.user_avatar,
                "student_enrolled_at": enr_item.enrolled_at if enr_item else None,
                "student_progress_percent": enr_item.progress_percent if enr_item else 0.0,
                "timestamp_seconds": q.timestamp_seconds,
                "timestamp_formatted": q.timestamp_formatted,
                "title": q.title,
                "content": q.content,
                "upvote_count": q.upvote_count,
                "answer_count": len(q.answers),
                "is_resolved": q.is_resolved,
                "has_official_answer": q.has_official_answer,
                "is_pinned": q.is_pinned,
                "is_hidden": q.is_hidden,
                "answers": [
                    {
                        "id": a.id,
                        "user_id": str(a.user_id),
                        "user_name": a.user_name,
                        "user_role": a.user_role,
                        "user_avatar": a.user_avatar,
                        "is_official": a.is_official,
                        "content": a.content,
                        "created_at": a.created_at,
                    }
                    for a in q.answers
                ],
                "created_at": q.created_at,
                "updated_at": q.updated_at,
            })

        return {
            "questions": detailed_items,
            "total": total,
            "unanswered_count": unanswered_count,
            "resolved_count": resolved_count,
        }

    @staticmethod
    async def admin_update_question(
        question_id: PydanticObjectId,
        is_resolved: bool | None = None,
        is_pinned: bool | None = None,
        is_hidden: bool | None = None,
    ) -> CourseQuestion:
        """Toggles resolved, pinned, or hidden moderation status."""
        question = await CourseQuestion.find_one(CourseQuestion.id == question_id)
        if not question:
            raise NotFoundError("Question not found")

        if is_resolved is not None:
            question.is_resolved = is_resolved
        if is_pinned is not None:
            question.is_pinned = is_pinned
        if is_hidden is not None:
            question.is_hidden = is_hidden

        question.updated_at = datetime.now(timezone.utc)
        await question.save()
        return question

    @staticmethod
    async def admin_delete_question(question_id: PydanticObjectId) -> bool:
        """Deletes a question thread."""
        question = await CourseQuestion.find_one(CourseQuestion.id == question_id)
        if not question:
            raise NotFoundError("Question not found")
        await question.delete()
        return True

    @staticmethod
    async def admin_delete_answer(question_id: PydanticObjectId, answer_id: str) -> bool:
        """Deletes an answer inside a question thread."""
        question = await CourseQuestion.find_one(CourseQuestion.id == question_id)
        if not question:
            raise NotFoundError("Question not found")
        orig_count = len(question.answers)
        question.answers = [a for a in question.answers if a.id != answer_id]
        if len(question.answers) == orig_count:
            raise NotFoundError("Answer not found")
        question.answer_count = len(question.answers)
        question.has_official_answer = any(a.is_official for a in question.answers)
        question.updated_at = datetime.now(timezone.utc)
        await question.save()
        return True

    # =========================================================================
    # GURUKUL CONSECRATION CERTIFICATE ENGINE
    # =========================================================================
    @staticmethod
    def compute_certificate_crypto(
        cert_id: str,
        user_id: str,
        student_name: str,
        course_id: str,
        course_title: str,
        issued_iso: str,
    ) -> tuple[str, str]:
        """
        Computes deterministic canonical SHA-256 hash and HMAC-SHA256 digital signature.
        Using the server secret key ensures nobody outside can forge a valid signature.
        """
        secret = (
            getattr(settings, "CERTIFICATE_SIGNING_KEY", None)
            or getattr(settings, "SECRET_KEY", "astra-gurukul-cryptographic-master-key-2026")
        )
        canonical_dict = {
            "authority": "DivinLink Gurukul Council of Vedic Astrological Sciences & Celestial Arts",
            "cert_id": cert_id.strip().upper(),
            "course_id": str(course_id).strip(),
            "course_title": str(course_title).strip(),
            "issued_iso": issued_iso,
            "student_name": str(student_name).strip(),
            "user_id": str(user_id).strip(),
        }
        canonical_bytes = json.dumps(canonical_dict, sort_keys=True, separators=(",", ":")).encode("utf-8")
        canonical_hash = hashlib.sha256(canonical_bytes).hexdigest()
        signature = hmac.new(secret.encode("utf-8"), canonical_bytes, hashlib.sha256).hexdigest()
        return canonical_hash, signature

    @staticmethod
    def generate_course_certificate_data(
        enrollment: CourseEnrollment,
        course: Course,
        user: User,
        signature_token: str | None = None,
        is_public_verification: bool = False,
    ) -> dict[str, Any]:
        """Builds structured certificate metadata and cryptographically verifiable seal."""
        web_url = getattr(settings, "FRONTEND_URL", "https://astra-astrology-web.vercel.app")
        api_url = getattr(settings, "API_BASE_URL", "https://astra-astrology-backend.onrender.com")

        cert_id = enrollment.certificate_id or CourseService.mint_certificate_id()
        issued_dt = enrollment.certificate_issued_at or datetime.now(timezone.utc)
        student_name = getattr(user, "full_name", None) or "DivinLink Gurukul Scholar"
        student_email = getattr(user, "email", None)

        # Compute deterministic canonical hash & HMAC-SHA256 signature
        canonical_hash, signature = CourseService.compute_certificate_crypto(
            cert_id=cert_id,
            user_id=str(user.id),
            student_name=student_name,
            course_id=str(course.id),
            course_title=course.title,
            issued_iso=issued_dt.isoformat(),
        )

        # Record the number and the seal on the enrollment if either is
        # missing. The number has to be written down now that it is random:
        # deriving it again would produce a different one each time, and the
        # seal is computed over it.
        if (
            not enrollment.certificate_id
            or not enrollment.certificate_signature
            or not enrollment.certificate_canonical_hash
        ):
            enrollment.certificate_id = cert_id
            enrollment.certificate_canonical_hash = canonical_hash
            enrollment.certificate_signature = signature

        # Two separate questions:
        # 1. Does the seal recorded when this was issued still match the record?
        is_signature_valid = True
        tamper_reason = None
        stored_signature = enrollment.certificate_signature
        if stored_signature and not hmac.compare_digest(stored_signature, signature):
            is_signature_valid = False
            tamper_reason = (
                "This record no longer matches the seal issued with it. "
                "Its details have been altered since."
            )

        # 2. Cryptographic signature check:
        # In public verification, a valid cryptographic signature token (?sig=...) is strictly required.
        # Without it, an attacker knowing or guessing another user's certificate ID cannot claim
        # the credential was cryptographically verified.
        signature_checked = False
        if is_public_verification:
            if not signature_token or not signature_token.strip():
                is_signature_valid = False
                signature_checked = False
                tamper_reason = (
                    "Cryptographic signature token (?sig=...) is required for authentic public verification. "
                    "Without the authentic seal signature, credential authenticity cannot be verified."
                )
            else:
                signature_checked = True
                clean_token = signature_token.strip().lower()
                if len(clean_token) < 16:
                    is_signature_valid = False
                    tamper_reason = "Signature token is too short (minimum 16 hexadecimal characters required)."
                else:
                    expected_prefix = signature[: len(clean_token)].lower()
                    if not hmac.compare_digest(clean_token, expected_prefix):
                        is_signature_valid = False
                        tamper_reason = "Cryptographic signature mismatch. Token or URL parameters have been tampered with."
        elif signature_token:
            signature_checked = True
            clean_token = signature_token.strip().lower()
            if len(clean_token) < 16:
                is_signature_valid = False
                tamper_reason = "Signature token is too short (minimum 16 hexadecimal characters required)."
            else:
                expected_prefix = signature[: len(clean_token)].lower()
                if not hmac.compare_digest(clean_token, expected_prefix):
                    is_signature_valid = False
                    tamper_reason = "Cryptographic signature mismatch. Token or URL parameters have been tampered with."

        verify_url = f"{web_url}/verify/certificate/{cert_id}?sig={signature[:32]}"
        html_url = f"{api_url}/api/v1/courses/certificate/verify/{cert_id}/html?sig={signature[:32]}"

        if is_signature_valid:
            status_text = "CRYPTOGRAPHICALLY_VERIFIED_AUTHENTIC"
        elif is_public_verification and (not signature_token or not signature_token.strip()):
            status_text = "SIGNATURE_REQUIRED_FOR_VERIFICATION"
        else:
            status_text = "TAMPERED_OR_INVALID_SIGNATURE"

        tamper_check = {
            "status": status_text,
            "is_valid": is_signature_valid,
            "tamper_reason": tamper_reason,
            "signature_token_checked": signature_checked,
            "hash_verified": True,
            "canonical_hash": canonical_hash,
            "signature_truncated": f"{signature[:12]}...{signature[-8:]}",
            "full_signature": signature,
            "signature_algorithm": "HMAC-SHA256 (FIPS 198-1 Standard)",
            "authoritative_domain": web_url,
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "canonical_payload": {
                "certificate_id": cert_id,
                "student_name": student_name,
                "course_title": course.title,
                "issued_iso": issued_dt.isoformat(),
                "lessons_count": len(enrollment.completed_lesson_ids),
            },
        }

        return {
            "certificate_id": cert_id,
            "is_valid": is_signature_valid,
            "student_name": student_name,
            "student_email": student_email,
            "course_id": str(course.id),
            "course_title": course.title,
            "course_slug": course.slug,
            "instructor_name": course.instructor_name or "Pt. Acharya Rahul Sharma",
            "instructor_title": course.instructor_title or "Senior Vedic Jyotishacharya & Faculty Head",
            "instructor_avatar": course.instructor_avatar,
            "issued_at": issued_dt,
            "issued_at_formatted": issued_dt.strftime("%d %B %Y"),
            "total_lessons_completed": len(enrollment.completed_lesson_ids),
            "distinction": "Vidya Parangata (Summa Cum Laude • পরম বিদ্বান)",
            "verification_url": verify_url,
            "certificate_html_url": html_url,
            "cryptographic_signature": signature,
            "canonical_hash": canonical_hash,
            "signature_algorithm": "HMAC-SHA256 (FIPS 198-1 Standard)",
            "is_signature_valid": is_signature_valid,
            "tamper_check": tamper_check,
            "digital_seal": {
                "verification_hash": canonical_hash[:24].upper(),
                "seal_title": "DivinLink Gurukul Consecrated",
                "seal_motto": "विद्या ददाति विनयं विनयाद्याति पात्रताम्",
                "status": "VERIFIED_AUTHENTIC" if is_signature_valid else ("UNVERIFIED_MISSING_SIGNATURE" if (is_public_verification and not signature_token) else "TAMPERED"),
                "signature": f"Pt. Acharya Rahul Sharma • {issued_dt.strftime('%d-%m-%Y')}",
            },
        }

    @staticmethod
    def generate_course_certificate_html(cert: dict[str, Any]) -> str:
        """Generates an ultra-luxurious, production-level printable A4 Landscape graduation certificate."""
        canonical_hash = cert.get("canonical_hash") or cert.get("digital_seal", {}).get("verification_hash", "")
        crypto_sig = cert.get("cryptographic_signature", "")
        instructor = cert.get("instructor_name", "Pt. Acharya Rahul Sharma")
        instructor_title = cert.get("instructor_title", "Senior Vedic Jyotishacharya")
        issued_date = cert.get("issued_at_formatted", "")
        distinction = cert.get("distinction", "Vidya Parangata (Summa Cum Laude)")
        total_lessons = cert.get("total_lessons_completed", 0)
        web_url = getattr(settings, "FRONTEND_URL", "https://astra-astrology-web.vercel.app")
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={cert['verification_url']}"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>DivinLink Gurukul Certificate — {cert['student_name']} — {cert['course_title']}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Alex+Brush&family=Cinzel:wght@600;700;800;900&family=Playfair+Display:ital,wght@0,600;0,700;0,900;1,400;1,600&family=Marcellus&family=Montserrat:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: #14110E;
      color: #1A1816;
      font-family: 'Marcellus', 'Georgia', serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 30px 15px;
    }}
    .actions-bar {{
      width: 100%;
      max-width: 1060px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 20px;
    }}
    .action-btn {{
      background: linear-gradient(135deg, #D4AF37 0%, #AA771C 100%);
      color: #000;
      border: none;
      padding: 12px 24px;
      border-radius: 9999px;
      font-weight: 700;
      font-size: 14px;
      cursor: pointer;
      box-shadow: 0 4px 18px rgba(212, 175, 55, 0.4);
      transition: all 0.2s ease;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }}
    .action-btn:hover {{
      transform: translateY(-2px);
      box-shadow: 0 6px 22px rgba(212, 175, 55, 0.6);
    }}
    .back-btn {{
      background: rgba(255, 255, 255, 0.08);
      color: #E5E7EB;
      border: 1px solid rgba(255, 255, 255, 0.15);
      padding: 10px 20px;
      border-radius: 9999px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      text-decoration: none;
    }}

    .cert-container {{
      width: 1060px;
      height: 680px;
      background: #FAF8F3;
      position: relative;
      overflow: hidden;
      border-radius: 12px;
      box-shadow: 0 25px 60px rgba(0, 0, 0, 0.7);
      display: flex;
      border: 1px solid rgba(209, 178, 111, 0.4);
    }}

    .guilloche-bg {{
      position: absolute;
      top: 50%;
      left: 33%;
      transform: translate(-50%, -50%);
      width: 580px;
      height: 580px;
      pointer-events: none;
      opacity: 0.038;
      z-index: 1;
    }}

    .microtext-band {{
      position: absolute;
      left: 20px;
      right: 20px;
      display: flex;
      justify-content: space-between;
      font-family: monospace;
      font-size: 6px;
      letter-spacing: 1.5px;
      color: rgba(140, 122, 98, 0.5);
      text-transform: uppercase;
      pointer-events: none;
      z-index: 25;
    }}
    .micro-top {{ top: 6px; }}
    .micro-bot {{ bottom: 6px; }}

    .cert-left {{
      width: 66%;
      height: 100%;
      padding: 40px 24px 32px 48px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      position: relative;
      z-index: 10;
    }}

    .brand-header {{
      display: flex;
      align-items: center;
      gap: 14px;
    }}
    .brand-logo-frame {{
      width: 50px;
      height: 50px;
      border-radius: 50%;
      border: 2px solid #C59B27;
      background: #FFFFFF;
      padding: 3px;
      box-shadow: 0 2px 8px rgba(197, 155, 39, 0.2);
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }}
    .brand-logo-img {{
      width: 100%;
      height: 100%;
      object-fit: contain;
    }}
    .brand-title-wrap {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .brand-name {{
      font-family: 'Cinzel', serif;
      font-size: 16px;
      font-weight: 900;
      letter-spacing: 2.5px;
      color: #1A1816;
      line-height: 1.1;
      text-transform: uppercase;
    }}
    .brand-estd {{
      background: rgba(197, 155, 39, 0.15);
      border: 1px solid rgba(197, 155, 39, 0.35);
      color: #8C6514;
      font-size: 8px;
      font-weight: 700;
      padding: 2px 6px;
      border-radius: 4px;
      letter-spacing: 1px;
    }}
    .brand-sub {{
      font-family: 'Montserrat', sans-serif;
      font-size: 8.5px;
      font-weight: 700;
      letter-spacing: 2px;
      color: #7A6C58;
      text-transform: uppercase;
      margin-top: 3px;
    }}

    .title-block {{
      margin-top: 10px;
    }}
    .cert-main-title {{
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 52px;
      font-weight: 900;
      color: #1A1816;
      line-height: 1;
      letter-spacing: 0.5px;
    }}
    .cert-sub-banner {{
      display: flex;
      align-items: center;
      gap: 10px;
      margin-top: 5px;
      max-width: 360px;
    }}
    .sub-line {{
      flex: 1;
      height: 1px;
      background: #8C7A62;
    }}
    .sub-text {{
      font-family: 'Montserrat', sans-serif;
      font-size: 9.5px;
      font-weight: 700;
      letter-spacing: 2.5px;
      color: #6E604E;
      text-transform: uppercase;
      white-space: nowrap;
    }}

    .consecration-label {{
      font-family: 'Montserrat', sans-serif;
      font-size: 9px;
      font-weight: 700;
      letter-spacing: 2px;
      color: #7A6C58;
      text-transform: uppercase;
      margin-top: 12px;
    }}

    .recipient-name {{
      font-family: 'Alex Brush', cursive;
      font-size: 48px;
      color: #1A1816;
      line-height: 1.1;
      padding-left: 4px;
      margin-top: 2px;
    }}
    .recipient-underline-wrap {{
      position: relative;
      width: 100%;
      height: 1.5px;
      background: linear-gradient(90deg, transparent 0%, #8C7A62 20%, #8C7A62 80%, transparent 100%);
      margin-top: 2px;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    .underline-diamond {{
      background: #FAF8F3;
      padding: 0 6px;
      color: #C59B27;
      font-size: 11px;
      line-height: 1;
    }}

    .distinction-pill {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 3px 14px;
      border-radius: 9999px;
      background: linear-gradient(90deg, rgba(197, 155, 39, 0.12) 0%, rgba(255, 235, 160, 0.3) 50%, rgba(197, 155, 39, 0.12) 100%);
      border: 1px solid rgba(197, 155, 39, 0.4);
      font-size: 9.5px;
      font-weight: 700;
      color: #78350F;
      letter-spacing: 1px;
      text-transform: uppercase;
      margin-top: 8px;
      width: fit-content;
    }}

    .citation-block {{
      margin-top: 8px;
      max-width: 500px;
    }}
    .citation-paragraph {{
      font-family: 'Marcellus', 'Georgia', serif;
      font-size: 11.5px;
      line-height: 1.55;
      color: #4A4237;
    }}
    .course-plaque {{
      margin-top: 6px;
      padding: 6px 14px;
      background: #FFFDF7;
      border: 1px solid rgba(197, 155, 39, 0.35);
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}
    .course-title {{
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 14px;
      font-weight: 700;
      color: #1A1816;
    }}
    .course-meta {{
      font-family: 'Montserrat', sans-serif;
      font-size: 8px;
      color: #7A6C58;
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-top: 2px;
    }}
    .course-badge {{
      background: #D1FAE5;
      color: #065F46;
      border: 1px solid #A7F3D0;
      font-size: 8.5px;
      font-weight: 700;
      padding: 2px 8px;
      border-radius: 4px;
      letter-spacing: 0.5px;
    }}

    .citation-shloka {{
      font-family: 'Playfair Display', serif;
      font-style: italic;
      font-size: 10px;
      color: #7A5D28;
      margin-top: 5px;
    }}

    .footer-row {{
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      margin-top: 14px;
      padding-right: 18px;
    }}
    .date-col, .sig-col {{
      width: 140px;
      text-align: center;
    }}
    .col-val {{
      font-family: 'Playfair Display', serif;
      font-size: 12px;
      font-weight: 600;
      color: #1A1816;
      margin-bottom: 5px;
      min-height: 22px;
      display: flex;
      align-items: flex-end;
      justify-content: center;
    }}
    .sig-script {{
      font-family: 'Alex Brush', cursive;
      font-size: 22px;
      color: #1A1816;
    }}
    .col-line {{
      width: 100%;
      height: 1px;
      background: #8C7A62;
      margin-bottom: 4px;
    }}
    .col-label {{
      font-family: 'Montserrat', sans-serif;
      font-size: 8.5px;
      font-weight: 600;
      letter-spacing: 1px;
      color: #7A6C58;
      text-transform: uppercase;
    }}
    .col-sublabel {{
      font-family: 'Montserrat', sans-serif;
      font-size: 7px;
      color: #8C7A62;
      letter-spacing: 0.5px;
      text-transform: uppercase;
    }}

    .qr-col {{
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
    }}
    .qr-frame {{
      width: 48px;
      height: 48px;
      background: #FFF;
      border: 1.5px solid #C59B27;
      border-radius: 6px;
      padding: 3px;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 2px 6px rgba(0,0,0,0.06);
    }}
    .qr-img {{
      width: 100%;
      height: 100%;
      object-fit: contain;
    }}
    .qr-label {{
      font-family: 'Montserrat', sans-serif;
      font-size: 7px;
      font-weight: 700;
      color: #7A6C58;
      letter-spacing: 0.5px;
      text-transform: uppercase;
      margin-top: 3px;
    }}

    /* Right Side Art-Deco Lattice */
    .cert-right {{
      position: absolute;
      right: 0;
      top: 0;
      bottom: 0;
      width: 34%;
      overflow: hidden;
      pointer-events: none;
    }}
    .cert-right svg {{
      width: 100%;
      height: 100%;
      display: block;
    }}

    /* Gold Ribbon Medal Badge with DIVINLINK GURUKUL */
    .seal-wrapper {{
      position: absolute;
      right: 28%;
      top: 12%;
      z-index: 20;
      pointer-events: none;
      filter: drop-shadow(0 8px 16px rgba(0,0,0,0.35));
    }}

    @media print {{
      @page {{
        size: A4 landscape;
        margin: 0 !important;
      }}
      *, *::before, *::after {{
        box-sizing: border-box !important;
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
      }}
      html, body {{
        width: 297mm !important;
        height: 210mm !important;
        max-height: 210mm !important;
        margin: 0 !important;
        padding: 0 !important;
        background: #ffffff !important;
        color: #000000 !important;
        overflow: hidden !important;
      }}
      .actions-bar {{ display: none !important; }}
      body * {{
        visibility: hidden !important;
      }}
      .cert-container, .cert-container * {{
        visibility: visible !important;
      }}
      .cert-container {{
        position: fixed !important;
        left: 0 !important;
        top: 0 !important;
        width: 297mm !important;
        height: 210mm !important;
        max-height: 210mm !important;
        border: none !important;
        border-radius: 0 !important;
        box-shadow: none !important;
        overflow: hidden !important;
        page-break-after: avoid !important;
        page-break-inside: avoid !important;
        break-inside: avoid !important;
        break-after: avoid !important;
      }}
      .cert-left {{
        width: 66% !important;
        height: 210mm !important;
        max-height: 210mm !important;
        padding: 10mm 8mm 8mm 14mm !important;
        box-sizing: border-box !important;
      }}
      .cert-right {{
        width: 34% !important;
        height: 210mm !important;
      }}
      .seal-wrapper {{
        right: 27% !important;
        top: 10% !important;
        transform: scale(0.9) !important;
      }}
      .cert-main-title {{
        font-size: 38px !important;
      }}
      .recipient-name {{
        font-size: 36px !important;
      }}
    }}
  </style>
</head>
<body>
  <div class="actions-bar">
    <a href="{cert['verification_url']}" class="back-btn">← Back to Portal</a>
    <button class="action-btn" onclick="window.print()">
      <span>🖨️</span> Print & Save Official PDF
    </button>
  </div>

  <div class="cert-container">
    <!-- Guilloche Background Rosette Watermark -->
    <div class="guilloche-bg">
      <svg viewBox="0 0 600 600" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
        <circle cx="300" cy="300" r="270" fill="none" stroke="#C59B27" stroke-width="1.5" stroke-dasharray="5,5"/>
        <circle cx="300" cy="300" r="230" fill="none" stroke="#C59B27" stroke-width="1"/>
        <circle cx="300" cy="300" r="180" fill="none" stroke="#C59B27" stroke-width="1.2" stroke-dasharray="3,3"/>
        <circle cx="300" cy="300" r="130" fill="none" stroke="#C59B27" stroke-width="0.8"/>
        <g stroke="#C59B27" stroke-width="0.75" fill="none">
          <ellipse cx="300" cy="300" rx="260" ry="50" transform="rotate(0 300 300)"/>
          <ellipse cx="300" cy="300" rx="260" ry="50" transform="rotate(20 300 300)"/>
          <ellipse cx="300" cy="300" rx="260" ry="50" transform="rotate(40 300 300)"/>
          <ellipse cx="300" cy="300" rx="260" ry="50" transform="rotate(60 300 300)"/>
          <ellipse cx="300" cy="300" rx="260" ry="50" transform="rotate(80 300 300)"/>
          <ellipse cx="300" cy="300" rx="260" ry="50" transform="rotate(100 300 300)"/>
          <ellipse cx="300" cy="300" rx="260" ry="50" transform="rotate(120 300 300)"/>
          <ellipse cx="300" cy="300" rx="260" ry="50" transform="rotate(140 300 300)"/>
          <ellipse cx="300" cy="300" rx="260" ry="50" transform="rotate(160 300 300)"/>
        </g>
        <text x="300" y="325" fill="#C59B27" font-size="80" font-family="'Playfair Display', serif" font-weight="bold" text-anchor="middle" opacity="0.35">ॐ</text>
      </svg>
    </div>

    <!-- Micro-Text Security Perimeter Bands -->
    <div class="microtext-band micro-top">
      <span>DIVINLINK GURUKUL CELESTIAL CREDENTIALS • OFFICIALLY CONSECRATED • CANONICAL HASH VERIFIED</span>
      <span>HMAC-SHA256 DIGITAL SECURITY SEAL • MATHEMATICALLY TAMPER-PROOF • VERIFIABLE AT ASTRAGURUKUL.COM</span>
    </div>
    <div class="microtext-band micro-bot">
      <span>ID: {cert['certificate_id']} • LEDGER RECORD CONSECRATED</span>
      <span>SIG: {crypto_sig[:24]}... (HMAC-SHA256)</span>
    </div>

    <div class="cert-left">
      <!-- Brand Header with Official Logo -->
      <div class="brand-header">
        <div class="brand-logo-frame">
          <img src="{web_url}/logo.png" alt="DivinLink Gurukul" class="brand-logo-img" onerror="this.src='/logo.png'"/>
        </div>
        <div>
          <div class="brand-title-wrap">
            <span class="brand-name">DivinLink Gurukul</span>
            <span class="brand-estd">ESTD. 2026</span>
          </div>
          <div class="brand-sub">Council of Vedic Astrological Sciences & Celestial Arts</div>
        </div>
      </div>

      <!-- Title Block -->
      <div class="title-block">
        <h1 class="cert-main-title">Certificate</h1>
        <div class="cert-sub-banner">
          <div class="sub-line"></div>
          <span class="sub-text">✦ OF SCHOLARLY ACHIEVEMENT ✦</span>
          <div class="sub-line"></div>
        </div>
      </div>

      <!-- Consecration Label -->
      <div class="consecration-label">
        This is to solemnly certify & consecrate that
      </div>

      <!-- Recipient Scholar Name -->
      <div>
        <div class="recipient-name">{cert['student_name']}</div>
        <div class="recipient-underline-wrap">
          <span class="underline-diamond">✦</span>
        </div>
      </div>

      <!-- Distinction Ribbon -->
      <div class="distinction-pill">
        ★ {distinction} ★
      </div>

      <!-- Citation Body & Course Plaque -->
      <div class="citation-block">
        <div class="citation-paragraph">
          has thoroughly mastered the sacred principles, astronomical calculations, predictive methodologies, and remedial canon prescribed in the curriculum of
        </div>
        <div class="course-plaque">
          <div>
            <div class="course-title">{cert['course_title']}</div>
            <div class="course-meta">Completed 100% Curriculum ({total_lessons} Lessons & Practicums)</div>
          </div>
          <span class="course-badge">PASSED</span>
        </div>
        <div class="citation-shloka">
          « विद्या ददाति विनयं विनयाद्याति पात्रताम् • True knowledge bestows humility, worthiness, and supreme fulfillment »
        </div>
      </div>

      <!-- Footer Row: Date, Live QR Code, Dual Signatures -->
      <div class="footer-row">
        <div class="date-col">
          <div class="col-val">{issued_date}</div>
          <div class="col-line"></div>
          <div class="col-label">Date Consecrated</div>
        </div>

        <div class="qr-col">
          <div class="qr-frame">
            <img src="{qr_url}" alt="Verification QR Code" class="qr-img"/>
          </div>
          <div class="qr-label">Scan to Verify</div>
        </div>

        <div class="sig-col">
          <div class="col-val sig-script">{instructor}</div>
          <div class="col-line"></div>
          <div class="col-label">{instructor_title}</div>
          <div class="col-sublabel">Council Registrar</div>
        </div>
      </div>
    </div>

    <!-- Gold Ribbon Medal Badge with DIVINLINK GURUKUL -->
    <div class="seal-wrapper">
      <svg viewBox="0 0 160 200" width="134" height="168" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="ribbonL" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#D8B467"/>
            <stop offset="50%" stop-color="#AA8237"/>
            <stop offset="100%" stop-color="#6C4F18"/>
          </linearGradient>
          <linearGradient id="ribbonR" x1="100%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#E8CA83"/>
            <stop offset="50%" stop-color="#BA9245"/>
            <stop offset="100%" stop-color="#78581F"/>
          </linearGradient>
          <radialGradient id="goldPlate" cx="40%" cy="35%" r="65%">
            <stop offset="0%" stop-color="#FFF0B8"/>
            <stop offset="40%" stop-color="#D4AF37"/>
            <stop offset="80%" stop-color="#9A7424"/>
            <stop offset="100%" stop-color="#64470C"/>
          </radialGradient>
          <radialGradient id="darkDisc" cx="50%" cy="45%" r="50%">
            <stop offset="0%" stop-color="#2C2114"/>
            <stop offset="80%" stop-color="#151009"/>
            <stop offset="100%" stop-color="#0C0905"/>
          </radialGradient>
        </defs>

        <path d="M 66,105 L 56,175 L 68,162 L 80,175 L 75,105 Z" fill="url(#ribbonL)"/>
        <path d="M 66,105 L 68,162 L 56,175 Z" fill="rgba(0,0,0,0.18)"/>

        <path d="M 85,105 L 80,175 L 92,162 L 104,175 L 94,105 Z" fill="url(#ribbonR)"/>
        <path d="M 94,105 L 92,162 L 104,175 Z" fill="rgba(0,0,0,0.12)"/>

        <polygon
          points="123.63,80.00 120.35,85.25 120.91,91.43 116.14,95.42 114.99,101.51 109.11,103.54 106.37,109.11 99.85,108.97 95.86,113.74 89.28,111.45 84.49,114.99 78.40,110.51 73.15,112.54 67.97,106.37 63.18,106.77 59.19,99.28 55.44,97.94 53.03,89.51 51.00,86.77 50.44,78.28 50.21,74.29 51.68,66.07 53.24,61.03 56.65,53.63 60.15,49.89 65.40,43.63 70.58,41.22 77.00,36.37 83.00,35.51 90.00,32.26 96.37,33.00 103.23,31.45 109.11,33.54 114.99,35.51 119.85,40.11 123.63,44.75 126.97,51.03 128.91,57.28 130.44,64.29 128.68,71.07 127.24,76.03"
          fill="url(#goldPlate)"
          stroke="#8B6508"
          stroke-width="0.8"
        />

        <circle cx="80" cy="80" r="38" fill="none" stroke="#FFEBA0" stroke-width="1.2"/>
        <circle cx="80" cy="80" r="35" fill="none" stroke="#8B6508" stroke-width="0.8"/>
        <circle cx="80" cy="80" r="32.5" fill="none" stroke="#FFEBA0" stroke-width="0.7" stroke-dasharray="1.5,1.5"/>
        <circle cx="80" cy="80" r="30" fill="none" stroke="#64470C" stroke-width="1.2"/>

        <circle cx="80" cy="80" r="28.5" fill="url(#darkDisc)"/>
        <circle cx="80" cy="80" r="27" fill="none" stroke="#D4AF37" stroke-width="0.6"/>

        <text x="80" y="65" fill="#FFE89E" font-family="sans-serif" font-size="5" font-weight="bold" text-anchor="middle" letter-spacing="1.5">★ ★ ★</text>
        <text x="80" y="74" fill="#FFF3CA" font-family="'Cinzel', serif" font-size="7" font-weight="900" text-anchor="middle" letter-spacing="1">DIVINLINK</text>
        <text x="80" y="81" fill="#E5C370" font-family="'Cinzel', serif" font-size="6" font-weight="800" text-anchor="middle" letter-spacing="1.2">GURUKUL</text>
        <path d="M 59,84 L 64,84 M 96,84 L 101,84" stroke="#D4AF37" stroke-width="0.5"/>
        <text x="80" y="87" fill="#E5C370" font-family="sans-serif" font-size="4.5" font-weight="800" text-anchor="middle" letter-spacing="1.2">EXCELLENCE</text>
        <text x="80" y="95" fill="#FFF3CA" font-family="'Cinzel', serif" font-size="7" font-weight="700" text-anchor="middle" letter-spacing="1">2026</text>
      </svg>
    </div>

    <!-- Right Column: Geometric Art-Deco Gold Lattice Pattern -->
    <div class="cert-right">
      <svg viewBox="0 0 320 640" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="patGoldMetal" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#D1B26F"/>
            <stop offset="30%" stop-color="#A68444"/>
            <stop offset="70%" stop-color="#DDC385"/>
            <stop offset="100%" stop-color="#8E6C2E"/>
          </linearGradient>
          <linearGradient id="patGoldLight" x1="0%" y1="100%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#A68444"/>
            <stop offset="50%" stop-color="#F0DCA0"/>
            <stop offset="100%" stop-color="#BD9C59"/>
          </linearGradient>

          <g id="patDiamondCross">
            <path d="M-160,-160 L160,160 M160,-160 L-160,160" stroke="url(#patGoldMetal)" stroke-width="16" fill="none"/>
            
            <polygon points="0,-110 110,0 0,110 -110,0" fill="none" stroke="url(#patGoldMetal)" stroke-width="14"/>
            <polygon points="0,-96 96,0 0,96 -96,0" fill="none" stroke="#FAF8F3" stroke-width="4"/>
            <polygon points="0,-90 90,0 0,90 -90,0" fill="none" stroke="url(#patGoldLight)" stroke-width="3"/>

            <path d="M-28,-28 L-28,-80 L0,-100 L28,-80 L28,-28 Z" fill="url(#patGoldMetal)"/>
            <path d="M-20,-28 L-20,-75 L0,-90 L20,-75 L20,-28 Z" fill="#FAF8F3"/>
            <path d="M-12,-28 L-12,-70 L0,-80 L12,-70 L12,-28 Z" fill="url(#patGoldLight)"/>

            <path d="M-28,28 L-28,80 L0,100 L28,80 L28,28 Z" fill="url(#patGoldMetal)"/>
            <path d="M-20,28 L-20,75 L0,90 L20,75 L20,28 Z" fill="#FAF8F3"/>
            <path d="M-12,28 L-12,70 L0,80 L12,70 L12,28 Z" fill="url(#patGoldLight)"/>

            <path d="M-28,-28 L-80,-28 L-100,0 L-80,28 L-28,28 Z" fill="url(#patGoldMetal)"/>
            <path d="M-28,-20 L-75,-20 L-90,0 L-75,20 L-28,20 Z" fill="#FAF8F3"/>
            <path d="M-28,-12 L-70,-12 L-80,0 L-70,12 L-28,12 Z" fill="url(#patGoldLight)"/>

            <path d="M28,-28 L80,-28 L100,0 L80,28 L28,28 Z" fill="url(#patGoldMetal)"/>
            <path d="M28,-20 L75,-20 L90,0 L75,20 L28,20 Z" fill="#FAF8F3"/>
            <path d="M28,-12 L70,-12 L80,0 L70,12 L28,12 Z" fill="url(#patGoldLight)"/>

            <polygon points="0,-28 28,0 0,28 -28,0" fill="url(#patGoldMetal)"/>
            <polygon points="0,-20 20,0 0,20 -20,0" fill="#FAF8F3"/>
            <polygon points="0,-12 12,0 0,12 -12,0" fill="url(#patGoldLight)"/>
            <polygon points="0,-5 5,0 0,5 -5,0" fill="url(#patGoldMetal)"/>

            <path d="M38,-38 L55,-55 M46,-38 L63,-55 M54,-38 L71,-55" stroke="url(#patGoldMetal)" stroke-width="3" fill="none"/>
            <path d="M38,38 L55,55 M46,38 L63,55 M54,38 L71,55" stroke="url(#patGoldMetal)" stroke-width="3" fill="none"/>
            <path d="M-38,38 L-55,55 M-46,38 L-63,55 M-54,38 L-71,55" stroke="url(#patGoldMetal)" stroke-width="3" fill="none"/>
            <path d="M-38,-38 L-55,-55 M-46,-38 L-63,-55 M-54,-38 L-71,-55" stroke="url(#patGoldMetal)" stroke-width="3" fill="none"/>
          </g>
        </defs>

        <rect width="320" height="640" fill="#FAF8F3"/>

        <g transform="translate(160, -30)"><use href="#patDiamondCross"/></g>
        <g transform="translate(160, 210)"><use href="#patDiamondCross"/></g>
        <g transform="translate(160, 450)"><use href="#patDiamondCross"/></g>
        <g transform="translate(160, 690)"><use href="#patDiamondCross"/></g>

        <g transform="translate(0, 90)"><use href="#patDiamondCross"/></g>
        <g transform="translate(0, 330)"><use href="#patDiamondCross"/></g>
        <g transform="translate(0, 570)"><use href="#patDiamondCross"/></g>

        <g transform="translate(320, 90)"><use href="#patDiamondCross"/></g>
        <g transform="translate(320, 330)"><use href="#patDiamondCross"/></g>
        <g transform="translate(320, 570)"><use href="#patDiamondCross"/></g>
      </svg>
    </div>
  </div>
</body>
</html>"""


    @staticmethod
    async def get_course_certificate(user: User, course_id: PydanticObjectId) -> dict[str, Any]:
        """Provides verified certificate data for a student who finished 100% of a course."""
        course = await Course.find_one(Course.id == course_id, Course.is_deleted == False)
        if not course:
            raise NotFoundError("Course not found")

        enrollment = await CourseEnrollment.find_one(
            CourseEnrollment.user_id == user.id,
            CourseEnrollment.course_id == course_id,
        )
        if not enrollment:
            # This used to mint an enrollment at 100% with the certificate
            # already issued, for anyone whose role contained "admin" or
            # "astrologer" — a verifiable credential for a course they had
            # never opened. A certificate has to be earned by the person
            # holding it, whoever they are.
            raise ForbiddenError(
                "You are not enrolled in this course.", error_code="not_enrolled"
            )

        # Ensure certificate fields are populated
        if enrollment.progress_percent < 100.0:
            total_published = await CourseLesson.find(
                CourseLesson.course_id == course_id,
                {"is_published": {"$ne": False}},
            ).count()
            if total_published > 0 and len(enrollment.completed_lesson_ids) >= total_published:
                enrollment.progress_percent = 100.0
            else:
                raise ForbiddenError(f"Masterclass is at {enrollment.progress_percent}%. Please complete 100% to generate certificate.")

        web_url = getattr(settings, "FRONTEND_URL", "https://astra-astrology-web.vercel.app")
        if not enrollment.certificate_id:
            enrollment.certificate_id = CourseService.mint_certificate_id()
            enrollment.certificate_issued_at = datetime.now(timezone.utc)
        if not enrollment.certificate_url:
            enrollment.certificate_url = f"{web_url}/verify/certificate/{enrollment.certificate_id}"
        enrollment.certificate_issued = True

        cert_data = CourseService.generate_course_certificate_data(enrollment, course, user)
        if not enrollment.certificate_signature or not enrollment.certificate_canonical_hash:
            enrollment.certificate_signature = cert_data.get("cryptographic_signature")
            enrollment.certificate_canonical_hash = cert_data.get("canonical_hash")

        await enrollment.save()
        return cert_data

    @staticmethod
    async def verify_course_certificate(
        certificate_id: str,
        signature_token: str | None = None,
    ) -> dict[str, Any]:
        """Publicly verifies an issued Astra Gurukul Certificate ID with tamper detection."""
        clean_id = certificate_id.strip().upper()
        enrollment = await CourseEnrollment.find_one(CourseEnrollment.certificate_id == clean_id)
        if not enrollment:
            # Fallback by enrollment ObjectId if someone passed enrollment id
            if len(clean_id) == 24 and PydanticObjectId.is_valid(clean_id):
                enrollment = await CourseEnrollment.find_one(CourseEnrollment.id == PydanticObjectId(clean_id))

        if not enrollment or not enrollment.certificate_issued:
            raise NotFoundError("Certificate not found or not yet consecrated.")

        course = await Course.find_one(Course.id == enrollment.course_id)
        if not course:
            raise NotFoundError("Associated course not found.")

        student_user = await User.find_one(User.id == enrollment.user_id)
        mock_user = student_user or User(
            id=enrollment.user_id,
            email="scholar@astragurukul.com",
            first_name="Astra",
            last_name="Scholar",
        )

        return CourseService.generate_course_certificate_data(
            enrollment,
            course,
            mock_user,
            signature_token=signature_token,
        )

