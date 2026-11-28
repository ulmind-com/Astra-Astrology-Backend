"""Course and Learning Management Service for Astra Gurukul."""

import asyncio
import hashlib
import hmac
import json
import secrets
import time
import urllib.parse
from datetime import datetime, timedelta, timezone
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
from app.core.security import safe_regex_pattern
from pymongo.errors import DuplicateKeyError

from app.assets.certificate_template_b64 import CERTIFICATE_TEMPLATE_B64
from app.assets.signature_b64 import SIGNATURE_B64

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
    def is_enrollment_active(enrollment: CourseEnrollment | None) -> bool:
        """Determines whether a course enrollment is currently valid and unexpired."""
        if not enrollment:
            return False
        if enrollment.expires_at is None:
            return True  # None represents Lifetime Access
        return datetime.now(timezone.utc) < _aware_utc(enrollment.expires_at)

    @staticmethod
    def mint_certificate_id() -> str:
        """A fresh, unguessable credential number for DivinLink Gurukul.

        Existing numbers (including legacy ASTRA-CERT-*) are left alone, so every
        certificate already in circulation keeps verifying seamlessly.
        """
        return f"DIVINLINK-CERT-{secrets.token_hex(8).upper()}"

    @staticmethod
    def format_certificate_issued_iso(dt: datetime | None) -> str:
        """
        Formats certificate issued timestamp into a canonical, deterministic UTC ISO-8601 string.
        Truncates microseconds to seconds (%Y-%m-%dT%H:%M:%SZ) so MongoDB BSON Date millisecond truncation
        never corrupts the SHA-256 canonical hash or HMAC-SHA256 signature across database round-trips.
        """
        if dt is None:
            dt = datetime.now(timezone.utc)
        aware_dt = _aware_utc(dt).astimezone(timezone.utc)
        return aware_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

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


    _courses_cache: dict[tuple[Any, ...], tuple[float, list[Course]]] = {}
    _COURSES_CACHE_TTL_SECONDS: float = 30.0

    @classmethod
    def invalidate_courses_cache(cls) -> None:
        cls._courses_cache.clear()

    @staticmethod
    async def list_courses(
        category: str | None = None,
        level: str | None = None,
        search: str | None = None,
        limit: int = 20,
        skip: int = 0,
    ) -> list[Course]:
        """Returns active, published courses with optional filtering and high-speed in-memory caching."""
        now = time.monotonic()
        cache_key = (category or "", level or "", (search or "").strip().lower(), limit, skip)
        cached = CourseService._courses_cache.get(cache_key)
        if cached is not None and (now - cached[0]) < CourseService._COURSES_CACHE_TTL_SECONDS:
            return cached[1]

        query: dict[str, Any] = {"is_published": True, "is_deleted": False}
        if category and category != "all":
            query["category"] = category
        if level and level != "all":
            query["level"] = level
        if search and search.strip():
            pat = safe_regex_pattern(search)
            query["$or"] = [
                {"title": pat},
                {"subtitle": pat},
                {"tags": {"$in": [search.strip().lower()]}},
            ]

        courses = (
            await Course.find(query)
            .sort([("is_featured", -1), ("created_at", -1)])
            .skip(max(0, skip))
            .limit(min(max(1, limit), 100))
            .to_list()
        )
        if len(CourseService._courses_cache) >= 50:
            CourseService._courses_cache.clear()
        CourseService._courses_cache[cache_key] = (now, courses)
        return courses

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
        is_expired = False
        enrollment_expires_at = None
        user_progress_percent = 0.0
        completed_lesson_ids: set[str] = set()

        if user:
            enrollment = await CourseEnrollment.find_one(
                CourseEnrollment.user_id == user.id,
                CourseEnrollment.course_id == course.id,
            )
            if enrollment:
                is_active = CourseService.is_enrollment_active(enrollment)
                is_enrolled = is_active
                is_expired = not is_active
                enrollment_expires_at = enrollment.expires_at
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
                if is_active and enrollment.progress_percent >= 100:
                    web_url = getattr(settings, "FRONTEND_URL", "https://astra-astrology-web.vercel.app")
                    if not enrollment.certificate_id:
                        enrollment.certificate_id = CourseService.mint_certificate_id()
                        enrollment.certificate_issued_at = datetime.now(timezone.utc).replace(microsecond=0)
                    elif not enrollment.certificate_issued_at:
                        enrollment.certificate_issued_at = datetime.now(timezone.utc).replace(microsecond=0)
                    if not enrollment.certificate_url or "?sig=" not in enrollment.certificate_url or not enrollment.certificate_signature:
                        student_name = getattr(user, "full_name", None) or "DivinLink Gurukul Scholar"
                        issued_dt = enrollment.certificate_issued_at
                        issued_iso = CourseService.format_certificate_issued_iso(issued_dt)
                        canonical_hash, signature = CourseService.compute_certificate_crypto(
                            cert_id=enrollment.certificate_id,
                            user_id=str(user.id),
                            student_name=student_name,
                            course_id=str(course.id),
                            course_title=course.title,
                            issued_iso=issued_iso,
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
                # Security hardening: Never expose raw unlisted YouTube video IDs in course hierarchy
                masked_video_id = (
                    None
                    if les.video_provider == "youtube_unlisted"
                    else (les.video_id if can_view else None)
                )
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
                        "video_id": masked_video_id,
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
        course_dict["is_expired"] = is_expired
        course_dict["expires_at"] = enrollment_expires_at
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
        is_expired = False
        if user:
            enrollment = await CourseEnrollment.find_one(
                CourseEnrollment.user_id == user.id,
                CourseEnrollment.course_id == course_id,
            )
            if enrollment:
                if CourseService.is_enrollment_active(enrollment):
                    is_enrolled = True
                else:
                    is_expired = True

        if not is_enrolled and not lesson.is_free_preview:
            # Clear error reporting: distinguish between logged out, not enrolled, and expired
            if user is None:
                raise UnauthorizedError(
                    "Please sign in to watch this lesson.",
                    error_code="sign_in_required",
                )
            if is_expired:
                expiry_dt = (
                    enrollment.expires_at.strftime("%d %B %Y")
                    if enrollment and enrollment.expires_at
                    else "previously"
                )
                raise ForbiddenError(
                    f"Your course enrollment expired on {expiry_dt}. Please re-enroll to continue watching.",
                    error_code="enrollment_expired",
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
            embed_url = (
                f"https://www.youtube-nocookie.com/embed/{lesson.video_id}"
                f"?enablejsapi=1&rel=0&modestbranding=1&controls=1&showinfo=0&disablekb=1&playsinline=1"
            )
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
            "video_id": None if lesson.video_provider == "youtube_unlisted" else lesson.video_id,
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
        if not enrollment or not CourseService.is_enrollment_active(enrollment):
            # Staff used to be enrolled here, silently and for free. The player
            # calls this endpoint on its own as soon as a video plays, so an
            # astrologer opening a free-preview lesson of a paid course walked
            # away with lifetime access to it — and, through the certificate
            # endpoint below, a certificate for a course they never took.
            # Admins who need access now grant it to themselves explicitly,
            # which leaves a record; see the admin enrollment endpoints.
            msg = (
                "Progress update skipped: enrollment expired"
                if enrollment
                else "Progress update skipped: user is not enrolled"
            )
            return {
                "progress_percent": enrollment.progress_percent if enrollment else 0.0,
                "completed_lesson_ids": [],
                "is_lesson_completed": False,
                "certificate_issued": False,
                "certificate_id": None,
                "certificate_url": None,
                "message": msg,
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

        # Update enrollment completed lessons set atomically in MongoDB
        str_id = str(lesson_id)
        if prog.is_completed:
            await CourseEnrollment.find_one(CourseEnrollment.id == enrollment.id).update(
                {"$addToSet": {"completed_lesson_ids": str_id}}
            )

        # Reload fresh enrollment state to avoid race conditions with concurrent lesson completions
        fresh_enrollment = await CourseEnrollment.find_one(CourseEnrollment.id == enrollment.id)
        if fresh_enrollment:
            enrollment = fresh_enrollment

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
                    enrollment.certificate_issued_at = datetime.now(timezone.utc).replace(microsecond=0)
                elif not enrollment.certificate_issued_at:
                    enrollment.certificate_issued_at = datetime.now(timezone.utc).replace(microsecond=0)

                web_url = getattr(settings, "FRONTEND_URL", "https://astra-astrology-web.vercel.app")
                student_name = getattr(user, "full_name", None) or "DivinLink Gurukul Scholar"
                course_item = await Course.find_one(Course.id == course_id)
                course_title = course_item.title if course_item else "DivinLink Gurukul Masterclass"
                issued_dt = enrollment.certificate_issued_at
                issued_iso = CourseService.format_certificate_issued_iso(issued_dt)

                canonical_hash, signature = CourseService.compute_certificate_crypto(
                    cert_id=enrollment.certificate_id,
                    user_id=str(user.id),
                    student_name=student_name,
                    course_id=str(course_id),
                    course_title=course_title,
                    issued_iso=issued_iso,
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

        # Atomic field update preserving completed_lesson_ids set
        set_fields: dict[str, Any] = {
            "progress_percent": enrollment.progress_percent,
            "last_accessed_at": datetime.now(timezone.utc),
        }
        if enrollment.certificate_issued:
            set_fields.update({
                "certificate_issued": True,
                "certificate_id": enrollment.certificate_id,
                "certificate_issued_at": enrollment.certificate_issued_at,
                "certificate_canonical_hash": enrollment.certificate_canonical_hash,
                "certificate_signature": enrollment.certificate_signature,
                "certificate_url": enrollment.certificate_url,
                "certificate_email_sent": enrollment.certificate_email_sent,
            })
        await CourseEnrollment.find_one(CourseEnrollment.id == enrollment.id).update({"$set": set_fields})

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

        # Check existing enrollment (only active, unexpired enrollments prevent purchasing)
        existing = await CourseEnrollment.find_one(
            CourseEnrollment.user_id == user.id,
            CourseEnrollment.course_id == course.id,
        )
        if existing and CourseService.is_enrollment_active(existing):
            return {
                "free_enrolled": True,
                "course_id": str(course.id),
                "course_title": course.title,
                "course_slug": course.slug,
                "message": "Already enrolled",
            }

        now = datetime.now(timezone.utc)
        access_days = getattr(course, "access_duration_days", None)
        expires_at = (
            now + timedelta(days=access_days)
            if (isinstance(access_days, int) and access_days > 0)
            else None
        )

        # If completely free (₹0)
        if course.price <= 0:
            if existing:
                existing.expires_at = expires_at
                existing.enrolled_at = now
                existing.payment_id = "FREE_ENROLLMENT_RENEW"
                existing.order_id = "FREE_ORDER_RENEW"
                await existing.save()
                return {
                    "free_enrolled": True,
                    "course_id": str(course.id),
                    "course_title": course.title,
                    "course_slug": course.slug,
                    "message": "Successfully renewed free course access",
                }

            enrollment = CourseEnrollment(
                user_id=user.id,
                course_id=course.id,
                amount_paid=0.0,
                payment_id="FREE_ENROLLMENT",
                order_id="FREE_ORDER",
                enrolled_at=now,
                expires_at=expires_at,
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

        now = datetime.now(timezone.utc)
        access_days = getattr(course, "access_duration_days", None)
        expires_at = (
            now + timedelta(days=access_days)
            if (isinstance(access_days, int) and access_days > 0)
            else None
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
                enrolled_at=now,
                expires_at=expires_at,
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
        else:
            # Re-enrollment or renewal: update access validity window
            enrollment.payment_id = payment_id
            enrollment.order_id = order.razorpay_order_id
            enrollment.amount_paid = amount_paise / 100
            enrollment.currency = order.currency
            enrollment.enrolled_at = now
            enrollment.expires_at = expires_at
            await enrollment.save()
            logger.info(
                "User {} renewed course {} via {} (expires on {})",
                order.user_id,
                order.course_id,
                via,
                expires_at,
            )

        # Ensure persistent legal invoice number is generated
        if not order.invoice_number:
            prefix = "DIVIN-CRS-INV"
            year = now.year
            raw_key = order.razorpay_order_id or str(order.id)
            clean_key = raw_key.replace("order_", "").replace("crs_", "").replace("-", "")
            suffix = clean_key[-6:].upper() if len(clean_key) >= 6 else str(order.user_id)[-6:].upper()
            order.invoice_number = f"{prefix}-{year}-{suffix}"

        if not getattr(enrollment, "invoice_number", None):
            enrollment.invoice_number = order.invoice_number
            await enrollment.save()

        if order.status is not PaymentOrderStatus.PAID:
            order.status = PaymentOrderStatus.PAID
            order.razorpay_payment_id = payment_id
            order.method = payment.get("method")
            order.verified_via = via
            order.paid_at = datetime.now(timezone.utc)
            await order.save()

        # Dispatch official Tax Invoice & Consecrated Enrollment Bill to student's email
        if not getattr(order, "invoice_email_sent", False):
            order.invoice_email_sent = True
            order.invoice_sent_at = datetime.now(timezone.utc)
            await order.save()

            async def _dispatch_course_invoice_email_task() -> None:
                try:
                    from app.services.email import send_course_purchase_invoice_email

                    student_user = await User.get(order.user_id)
                    if not student_user or not student_user.email:
                        logger.warning("No valid email address for student {} to send course invoice.", order.user_id)
                        return

                    student_name = (
                        getattr(student_user, "full_name", None)
                        or getattr(student_user, "name", None)
                        or "Valued Scholar"
                    )
                    frontend_base = getattr(settings, "FRONTEND_URL", "https://astra-astrology-web.vercel.app").rstrip("/")
                    course_url = f"{frontend_base}/courses/{course.slug or str(course.id)}"
                    invoice_url = f"{frontend_base}/account/courses"

                    access_type = "Lifetime Access"
                    if course.access_duration_days and course.access_duration_days > 0:
                        access_type = f"{course.access_duration_days} Days Access"

                    formatted_date = (order.paid_at or datetime.now(timezone.utc)).strftime("%d %B %Y, %I:%M %p IST")
                    method_display = (payment.get("method") or "Online / Razorpay").upper()
                    inv_num = order.invoice_number or f"DIVIN-CRS-{str(order.id)[-6:].upper()}"

                    await send_course_purchase_invoice_email(
                        to=student_user.email,
                        user_name=student_name,
                        course_title=course.title,
                        invoice_number=inv_num,
                        order_id=order.razorpay_order_id,
                        payment_id=payment_id,
                        amount_inr=float(amount_paise / 100.0),
                        payment_method=method_display,
                        purchase_date=formatted_date,
                        course_url=course_url,
                        invoice_url=invoice_url,
                        instructor_name=course.instructor_name or "Pt. Acharya Rahul Sharma",
                        access_type=access_type,
                    )
                    logger.info("Official Course Purchase Invoice successfully dispatched to {} for course {}", student_user.email, course.title)
                except Exception as exc:
                    logger.opt(exception=exc).warning(
                        "Failed to dispatch course purchase invoice email for order {}: {}", order.id, exc
                    )

            asyncio.create_task(_dispatch_course_invoice_email_task())

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
            "invoice_number": getattr(order, "invoice_number", None),
            "invoice_email_sent": getattr(order, "invoice_email_sent", False),
            "created_at": order.created_at,
        }

    @staticmethod
    async def _search_user_and_course_ids(
        search: str, include_courses: bool = True
    ) -> tuple[list[PydanticObjectId], list[PydanticObjectId]]:
        pat = safe_regex_pattern(search)
        users = (
            await User.find(
                {
                    "$or": [
                        {"email": pat},
                        {"first_name": pat},
                        {"last_name": pat},
                        {"phone": pat},
                    ]
                }
            )
            .limit(200)
            .to_list()
        )
        user_ids = [u.id for u in users]
        course_ids: list[PydanticObjectId] = []
        if include_courses:
            courses = await Course.find({"title": pat}).limit(100).to_list()
            course_ids = [c.id for c in courses]
        return user_ids, course_ids

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
        cap_limit = min(max(1, limit), 100)
        safe_page = max(1, page)
        query: dict[str, Any] = {}
        if status_filter and status_filter != "all":
            query["status"] = status_filter
        if course_id is not None:
            query["course_id"] = course_id

        if search and search.strip():
            pat = safe_regex_pattern(search)
            user_ids, course_ids = await CourseService._search_user_and_course_ids(search)
            or_clauses: list[dict[str, Any]] = [
                {"razorpay_order_id": pat},
                {"razorpay_payment_id": pat},
            ]
            if user_ids:
                or_clauses.append({"user_id": {"$in": user_ids}})
            if course_ids:
                or_clauses.append({"course_id": {"$in": course_ids}})
            query["$or"] = or_clauses

        cursor = CourseOrder.find(query)
        total = await cursor.count()
        pages = max(1, (total + cap_limit - 1) // cap_limit)
        start = (safe_page - 1) * cap_limit
        paged_orders = (
            await cursor.sort([("created_at", -1)])
            .skip(start)
            .limit(cap_limit)
            .to_list()
        )
        users_map, courses_map = await CourseService._enrich_users_and_courses(
            [o.user_id for o in paged_orders], [o.course_id for o in paged_orders]
        )
        paged = [
            CourseService._serialize_admin_order(o, users_map, courses_map)
            for o in paged_orders
        ]

        created_count = await CourseOrder.find(CourseOrder.status == PaymentOrderStatus.CREATED).count()
        paid_count = await CourseOrder.find(CourseOrder.status == PaymentOrderStatus.PAID).count()
        failed_count = await CourseOrder.find(CourseOrder.status == PaymentOrderStatus.FAILED).count()
        refunded_count = await CourseOrder.find(CourseOrder.status == PaymentOrderStatus.REFUNDED).count()

        return {
            "items": paged,
            "total": total,
            "page": safe_page,
            "limit": cap_limit,
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
        cap_limit = min(max(1, limit), 100)
        safe_page = max(1, page)
        query: dict[str, Any] = {}
        if course_id is not None:
            query["course_id"] = course_id

        if search and search.strip():
            pat = safe_regex_pattern(search)
            user_ids, course_ids = await CourseService._search_user_and_course_ids(search)
            or_clauses: list[dict[str, Any]] = [
                {"payment_id": pat},
                {"order_id": pat},
            ]
            if user_ids:
                or_clauses.append({"user_id": {"$in": user_ids}})
            if course_ids:
                or_clauses.append({"course_id": {"$in": course_ids}})
            query["$or"] = or_clauses

        cursor = CourseEnrollment.find(query)
        total = await cursor.count()
        pages = max(1, (total + cap_limit - 1) // cap_limit)
        start = (safe_page - 1) * cap_limit
        enrollments = (
            await cursor.sort([("enrolled_at", -1)])
            .skip(start)
            .limit(cap_limit)
            .to_list()
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
                    "student_avatar": getattr(u, "avatar_url", None) if u else None,
                    "course_id": str(e.course_id),
                    "course_title": c.title if c else None,
                    "course_slug": c.slug if c else None,
                    "payment_id": e.payment_id,
                    "order_id": e.order_id,
                    "amount_paid": e.amount_paid,
                    "currency": e.currency,
                    "progress_percent": e.progress_percent,
                    "completed_lessons_count": len(e.completed_lesson_ids or []),
                    "total_lessons_count": c.total_lessons if c else len(e.completed_lesson_ids or []),
                    "certificate_issued": e.certificate_issued,
                    "certificate_id": e.certificate_id,
                    "certificate_url": e.certificate_url,
                    "certificate_issued_at": e.certificate_issued_at,
                    "invoice_number": getattr(e, "invoice_number", None),
                    "enrolled_at": e.enrolled_at,
                    "expires_at": e.expires_at,
                    "is_expired": bool(
                        e.expires_at
                        and datetime.now(timezone.utc) >= _aware_utc(e.expires_at)
                    ),
                    "last_accessed_at": e.last_accessed_at,
                }
            )

        return {
            "items": items,
            "total": total,
            "page": safe_page,
            "limit": cap_limit,
            "pages": pages,
        }

    @staticmethod
    async def admin_get_course_learners(
        *,
        course_id: PydanticObjectId,
        search: str | None = None,
        progress_status: str | None = None,
        sort_by: str | None = "enrolled_desc",
        page: int = 1,
        limit: int = 25,
    ) -> dict[str, Any]:
        course = await Course.get(course_id)
        if not course:
            raise NotFoundError("Course not found.", error_code="course_not_found")

        cap_limit = min(max(1, limit), 100)
        safe_page = max(1, page)
        total_lessons_in_course = await CourseLesson.find(CourseLesson.course_id == course_id).count()

        # Summary stats aggregated directly in MongoDB (avoids loading all enrollments)
        col = CourseEnrollment.get_pymongo_collection()
        agg_cursor = await col.aggregate([
            {"$match": {"course_id": course_id}},
            {
                "$group": {
                    "_id": None,
                    "total_enrolled": {"$sum": 1},
                    "completed_count": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$or": [
                                        {"$gte": ["$progress_percent", 100]},
                                        {"$eq": ["$certificate_issued", True]},
                                    ]
                                },
                                1,
                                0,
                            ]
                        }
                    },
                    "in_progress_count": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$and": [
                                        {"$gt": ["$progress_percent", 0]},
                                        {"$lt": ["$progress_percent", 100]},
                                        {"$ne": ["$certificate_issued", True]},
                                    ]
                                },
                                1,
                                0,
                            ]
                        }
                    },
                    "not_started_count": {
                        "$sum": {"$cond": [{"$eq": ["$progress_percent", 0]}, 1, 0]}
                    },
                    "total_progress_sum": {"$sum": {"$ifNull": ["$progress_percent", 0]}},
                    "total_revenue": {"$sum": {"$ifNull": ["$amount_paid", 0]}},
                }
            },
        ])
        agg_rows = [r async for r in agg_cursor]
        stat_row = agg_rows[0] if agg_rows else {}
        total_enrolled = int(stat_row.get("total_enrolled", 0) or 0)
        completed_count = int(stat_row.get("completed_count", 0) or 0)
        in_progress_count = int(stat_row.get("in_progress_count", 0) or 0)
        not_started_count = int(stat_row.get("not_started_count", 0) or 0)
        total_progress_sum = float(stat_row.get("total_progress_sum", 0.0) or 0.0)
        total_revenue = float(stat_row.get("total_revenue", 0.0) or 0.0)
        avg_progress = round(total_progress_sum / max(1, total_enrolled), 1)

        query: dict[str, Any] = {"course_id": course_id}
        if search and search.strip():
            pat = safe_regex_pattern(search)
            user_ids, _ = await CourseService._search_user_and_course_ids(
                search, include_courses=False
            )
            or_clauses: list[dict[str, Any]] = [
                {"payment_id": pat},
                {"order_id": pat},
                {"certificate_id": pat},
            ]
            if user_ids:
                or_clauses.append({"user_id": {"$in": user_ids}})
            query["$or"] = or_clauses

        now_utc = datetime.now(timezone.utc)
        if progress_status and progress_status != "all":
            if progress_status == "completed":
                query["$and"] = query.get("$and", []) + [
                    {"$or": [{"progress_percent": {"$gte": 100}}, {"certificate_issued": True}]}
                ]
            elif progress_status == "in_progress":
                query["progress_percent"] = {"$gt": 0, "$lt": 100}
                query["certificate_issued"] = {"$ne": True}
            elif progress_status == "not_started":
                query["progress_percent"] = 0
            elif progress_status == "expired":
                query["expires_at"] = {"$ne": None, "$lte": now_utc}

        sort_spec = [("enrolled_at", -1)]
        if sort_by == "enrolled_asc":
            sort_spec = [("enrolled_at", 1)]
        elif sort_by == "progress_desc":
            sort_spec = [("progress_percent", -1)]
        elif sort_by == "progress_asc":
            sort_spec = [("progress_percent", 1)]
        elif sort_by == "last_active_desc":
            sort_spec = [("last_accessed_at", -1)]

        cursor = CourseEnrollment.find(query)
        total_filtered = await cursor.count()
        pages = max(1, (total_filtered + cap_limit - 1) // cap_limit)
        start = (safe_page - 1) * cap_limit
        paged_enrollments = await cursor.sort(sort_spec).skip(start).limit(cap_limit).to_list()

        page_user_ids = [e.user_id for e in paged_enrollments]
        users = await User.find({"_id": {"$in": page_user_ids}}).to_list() if page_user_ids else []
        users_map = {str(u.id): u for u in users}

        items: list[dict[str, Any]] = []
        for e in paged_enrollments:
            u = users_map.get(str(e.user_id))
            is_expired = bool(e.expires_at and now_utc >= _aware_utc(e.expires_at))
            items.append({
                "id": str(e.id),
                "user_id": str(e.user_id),
                "student_name": getattr(u, "full_name", None) if u else None,
                "student_email": getattr(u, "email", None) if u else None,
                "student_phone": (
                    (getattr(u, "phone", None) or getattr(u, "mobile_number", None))
                    if u
                    else None
                ),
                "student_avatar": getattr(u, "avatar_url", None) if u else None,
                "course_id": str(course.id),
                "course_title": course.title,
                "course_slug": course.slug,
                "payment_id": e.payment_id,
                "order_id": e.order_id,
                "amount_paid": e.amount_paid,
                "currency": e.currency,
                "progress_percent": e.progress_percent,
                "completed_lessons_count": len(e.completed_lesson_ids or []),
                "total_lessons_count": total_lessons_in_course,
                "certificate_issued": e.certificate_issued,
                "certificate_id": e.certificate_id,
                "certificate_url": e.certificate_url,
                "certificate_issued_at": e.certificate_issued_at,
                "enrolled_at": e.enrolled_at,
                "expires_at": e.expires_at,
                "is_expired": is_expired,
                "last_accessed_at": e.last_accessed_at,
            })

        return {
            "course_id": str(course.id),
            "course_title": course.title,
            "course_slug": course.slug,
            "price": course.price,
            "stats": {
                "total_enrolled": total_enrolled,
                "completed_count": completed_count,
                "in_progress_count": in_progress_count,
                "not_started_count": not_started_count,
                "average_progress_percent": avg_progress,
                "total_revenue": total_revenue,
                "total_lessons_in_course": total_lessons_in_course,
            },
            "items": items,
            "total": total_filtered,
            "page": safe_page,
            "limit": cap_limit,
            "pages": pages,
        }

    @staticmethod
    async def admin_get_learner_progress(
        *,
        course_id: PydanticObjectId,
        user_id: PydanticObjectId,
    ) -> dict[str, Any]:
        course = await Course.get(course_id)
        if not course:
            raise NotFoundError("Course not found.", error_code="course_not_found")

        enrollment = await CourseEnrollment.find_one(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.user_id == user_id,
        )
        if not enrollment:
            raise NotFoundError(
                "Student is not enrolled in this course.",
                error_code="enrollment_not_found",
            )

        user = await User.get(user_id)

        # Fetch sections and lessons
        sections = (
            await CourseSection.find(CourseSection.course_id == course_id)
            .sort([("order", 1)])
            .to_list()
        )
        lessons = (
            await CourseLesson.find(CourseLesson.course_id == course_id)
            .sort([("order", 1)])
            .to_list()
        )

        # Fetch progress records
        progress_records = (
            await CourseLessonProgress.find(
                CourseLessonProgress.course_id == course_id,
                CourseLessonProgress.user_id == user_id,
            ).to_list()
        )
        progress_map = {str(p.lesson_id): p for p in progress_records}
        completed_set = set(enrollment.completed_lesson_ids or [])

        # Group lessons by section
        lessons_by_section: dict[str, list[Any]] = {}
        total_watched_sec = 0

        for l in lessons:
            sec_id = str(l.section_id)
            if sec_id not in lessons_by_section:
                lessons_by_section[sec_id] = []

            p = progress_map.get(str(l.id))
            is_comp = (str(l.id) in completed_set) or (p.is_completed if p else False)
            watched_sec = p.watched_seconds if p else 0
            credited_sec = p.credited_seconds if p else 0
            total_watched_sec += max(watched_sec, credited_sec)

            lessons_by_section[sec_id].append({
                "lesson_id": str(l.id),
                "title": l.title,
                "order": l.order,
                "duration_minutes": l.duration_minutes,
                "is_completed": is_comp,
                "completed_at": p.completed_at if p else None,
                "watched_seconds": watched_sec,
                "credited_seconds": credited_sec,
                "last_watched_at": p.last_watched_at if p else None,
            })

        sections_out = []
        for s in sections:
            sec_id = str(s.id)
            sections_out.append({
                "section_id": sec_id,
                "title": s.title,
                "order": s.order,
                "lessons": lessons_by_section.get(sec_id, []),
            })

        is_expired = bool(
            enrollment.expires_at
            and datetime.now(timezone.utc) >= _aware_utc(enrollment.expires_at)
        )

        return {
            "enrollment_id": str(enrollment.id),
            "user_id": str(user_id),
            "student_name": getattr(user, "full_name", None) if user else None,
            "student_email": getattr(user, "email", None) if user else None,
            "student_phone": (
                (getattr(user, "phone", None) or getattr(user, "mobile_number", None))
                if user
                else None
            ),
            "student_avatar": getattr(user, "avatar_url", None) if user else None,
            "course_id": str(course.id),
            "course_title": course.title,
            "course_slug": course.slug,
            "enrolled_at": enrollment.enrolled_at,
            "expires_at": enrollment.expires_at,
            "is_expired": is_expired,
            "payment_id": enrollment.payment_id,
            "order_id": enrollment.order_id,
            "amount_paid": enrollment.amount_paid,
            "currency": enrollment.currency,
            "progress_percent": enrollment.progress_percent,
            "completed_lessons_count": len(enrollment.completed_lesson_ids or []),
            "total_lessons_count": len(lessons),
            "total_watched_seconds": total_watched_sec,
            "certificate_issued": enrollment.certificate_issued,
            "certificate_id": enrollment.certificate_id,
            "certificate_url": enrollment.certificate_url,
            "certificate_issued_at": enrollment.certificate_issued_at,
            "last_accessed_at": enrollment.last_accessed_at,
            "sections": sections_out,
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
        access_duration_days: int | None = None,
        expires_at: datetime | None = None,
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

        now = datetime.now(timezone.utc)
        target_expires_at = expires_at
        if target_expires_at is None:
            access_days = access_duration_days or getattr(course, "access_duration_days", None)
            if isinstance(access_days, int) and access_days > 0:
                target_expires_at = now + timedelta(days=access_days)

        ref_payment_id = (
            payment_id.strip()
            if payment_id and payment_id.strip()
            else f"ADMIN_GRANT:{(note or 'support').strip()[:80]}"
        )

        existing = await CourseEnrollment.find_one(
            CourseEnrollment.user_id == student.id,
            CourseEnrollment.course_id == course.id,
        )
        if existing is not None:
            # If target expiration was provided or existing was expired, update expiration
            if target_expires_at is not None or not CourseService.is_enrollment_active(existing):
                existing.expires_at = target_expires_at
                existing.payment_id = ref_payment_id
                existing.amount_paid = float(amount_paid)
                await existing.save()

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
                    "expires_at": existing.expires_at,
                    "is_expired": bool(
                        existing.expires_at
                        and datetime.now(timezone.utc) >= _aware_utc(existing.expires_at)
                    ),
                    "last_accessed_at": existing.last_accessed_at,
                },
            }

        enrollment = CourseEnrollment(
            user_id=student.id,
            course_id=course.id,
            payment_id=ref_payment_id,
            order_id="ADMIN_MANUAL_ENROLL",
            amount_paid=float(amount_paid),
            currency=course.currency or "INR",
            enrolled_at=now,
            expires_at=target_expires_at,
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
                "expires_at": enrollment.expires_at,
                "is_expired": bool(
                    enrollment.expires_at
                    and datetime.now(timezone.utc) >= _aware_utc(enrollment.expires_at)
                ),
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
    async def admin_update_enrollment_validity(
        *,
        enrollment_id: PydanticObjectId,
        course_id: PydanticObjectId | None = None,
        mode: str = "set_days",
        days: int | None = None,
        expires_at: datetime | None = None,
        note: str | None = None,
    ) -> dict[str, Any]:
        """Updates or extends the access validity duration for an enrolled student."""
        query = [CourseEnrollment.id == enrollment_id]
        if course_id:
            query.append(CourseEnrollment.course_id == course_id)

        enrollment = await CourseEnrollment.find_one(*query)
        if enrollment is None:
            raise NotFoundError("Enrollment not found.")

        course = await Course.find_one(Course.id == enrollment.course_id)
        student = await User.find_one(User.id == enrollment.user_id)
        now = datetime.now(timezone.utc)

        target_expires_at: datetime | None = None

        if mode == "lifetime":
            target_expires_at = None
        elif mode == "set_days":
            if not days or days <= 0:
                raise BadRequestError("Number of days must be at least 1.")
            target_expires_at = now + timedelta(days=days)
        elif mode == "extend_days":
            if not days or days <= 0:
                raise BadRequestError("Number of days to extend must be at least 1.")
            base_time = now
            if enrollment.expires_at:
                aware_exp = _aware_utc(enrollment.expires_at)
                if aware_exp > now:
                    base_time = aware_exp
            target_expires_at = base_time + timedelta(days=days)
        elif mode == "set_date":
            if not expires_at:
                raise BadRequestError("An expiration date must be provided.")
            target_expires_at = _aware_utc(expires_at)
            if target_expires_at <= now:
                raise BadRequestError("Expiration date must be in the future.")
        else:
            raise BadRequestError(f"Unsupported validity mode: {mode}")

        enrollment.expires_at = target_expires_at
        await enrollment.save()

        logger.info(
            f"Admin updated validity for enrollment {enrollment_id} (Student: {student.email if student else enrollment.user_id}) "
            f"mode '{mode}', new expires_at: {target_expires_at}. Note: {note}"
        )

        return {
            "id": str(enrollment.id),
            "user_id": str(enrollment.user_id),
            "student_name": getattr(student, "full_name", None) if student else None,
            "student_email": getattr(student, "email", None) if student else None,
            "student_phone": (
                (getattr(student, "phone", None) or getattr(student, "mobile_number", None)) if student else None
            ),
            "course_id": str(enrollment.course_id),
            "course_title": course.title if course else None,
            "course_slug": course.slug if course else None,
            "payment_id": enrollment.payment_id,
            "order_id": enrollment.order_id,
            "amount_paid": enrollment.amount_paid,
            "currency": enrollment.currency,
            "progress_percent": enrollment.progress_percent,
            "certificate_issued": enrollment.certificate_issued,
            "enrolled_at": enrollment.enrolled_at,
            "expires_at": enrollment.expires_at,
            "is_expired": bool(
                enrollment.expires_at
                and datetime.now(timezone.utc) >= _aware_utc(enrollment.expires_at)
            ),
            "last_accessed_at": enrollment.last_accessed_at,
        }

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
            if course:
                web_url = getattr(settings, "FRONTEND_URL", "https://astra-astrology-web.vercel.app")
                
                # Check if student completed all published lessons even if progress_percent is lagging
                if e.progress_percent < 100.0:
                    total_published = await CourseLesson.find(
                        CourseLesson.course_id == e.course_id,
                        {"is_published": {"$ne": False}},
                    ).count()
                    if total_published > 0 and len(e.completed_lesson_ids or []) >= total_published:
                        e.progress_percent = 100.0

                if e.progress_percent >= 100.0 or bool(e.certificate_issued):
                    e.certificate_issued = True
                    if not e.certificate_id:
                        e.certificate_id = CourseService.mint_certificate_id()
                    if not e.certificate_issued_at:
                        e.certificate_issued_at = datetime.now(timezone.utc).replace(microsecond=0)

                    # Ensure certificate signature and signed verification URL are always fresh and valid
                    student_name = getattr(user, "full_name", None) or "DivinLink Gurukul Scholar"
                    issued_iso = CourseService.format_certificate_issued_iso(e.certificate_issued_at)
                    c_hash, c_sig = CourseService.compute_certificate_crypto(
                        cert_id=e.certificate_id,
                        user_id=str(user.id),
                        student_name=student_name,
                        course_id=str(course.id),
                        course_title=course.title,
                        issued_iso=issued_iso,
                    )
                    expected_url = f"{web_url}/verify/certificate/{e.certificate_id}?sig={c_sig[:32]}"
                    if (
                        e.certificate_signature != c_sig
                        or e.certificate_canonical_hash != c_hash
                        or e.certificate_url != expected_url
                    ):
                        e.certificate_canonical_hash = c_hash
                        e.certificate_signature = c_sig
                        e.certificate_url = expected_url
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
                        "is_expired": bool(
                            e.expires_at
                            and datetime.now(timezone.utc) >= _aware_utc(e.expires_at)
                        ),
                        "access_duration_days": course.access_duration_days,
                        "progress_percent": e.progress_percent,
                        "completed_lesson_ids": e.completed_lesson_ids,
                        "certificate_issued": e.certificate_issued,
                        "certificate_id": e.certificate_id,
                        "certificate_url": e.certificate_url,
                        "invoice_number": getattr(e, "invoice_number", None),
                        "invoice_url": f"/api/v1/courses/{course.id}/invoice/html",
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
    def get_signed_bunny_embed_url(
        video_id: str,
        library_id: str | None = None,
        expires_in_seconds: int = 7200,
    ) -> str:
        """Generates a signed Bunny.net embed URL with token authentication.
        Prevents 403 Forbidden errors in admin preview and classroom players.
        """
        clean_id = str(video_id or "").strip()
        if "/" in clean_id:
            clean_id = clean_id.split("?")[0].rstrip("/").split("/")[-1]

        lib_id = library_id or settings.BUNNY_STREAM_LIBRARY_ID
        token_key = settings.BUNNY_STREAM_TOKEN_KEY
        expires_at = int(time.time()) + max(300, expires_in_seconds)

        if token_key and clean_id:
            raw_token = f"{token_key}{clean_id}{expires_at}"
            token = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
            return f"https://iframe.mediadelivery.net/embed/{lib_id}/{clean_id}?token={token}&expires={expires_at}"
        return f"https://iframe.mediadelivery.net/embed/{lib_id}/{clean_id}"

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
            "is_hidden": {"$ne": True},
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
        is_active = CourseService.is_enrollment_active(enrollment)
        if not is_active and not lesson.is_free_preview and not CourseService._is_staff(user):
            if enrollment:
                raise ForbiddenError(
                    "Your course enrollment has expired. Please renew your access to participate in Gurukul Jigyasa Q&A.",
                    error_code="enrollment_expired",
                )
            raise ForbiddenError(
                "Please enroll in this course to participate in Gurukul Jigyasa Q&A.",
                error_code="not_enrolled",
            )

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

        is_staff = CourseService._is_staff(user)
        if getattr(question, "is_hidden", False) and not is_staff:
            raise NotFoundError("Question not found or has been hidden.")

        if not is_staff:
            enrollment = await CourseEnrollment.find_one(
                CourseEnrollment.user_id == user.id,
                CourseEnrollment.course_id == question.course_id,
            )
            is_active = CourseService.is_enrollment_active(enrollment)
            if not is_active:
                lesson = await CourseLesson.find_one(
                    CourseLesson.id == question.lesson_id,
                    CourseLesson.course_id == question.course_id,
                )
                is_preview = bool(lesson and getattr(lesson, "is_free_preview", False))
                if not is_preview:
                    if enrollment:
                        raise ForbiddenError(
                            "Your course enrollment has expired. Please renew your access to participate in Gurukul Jigyasa Q&A.",
                            error_code="enrollment_expired",
                        )
                    raise ForbiddenError(
                        "Please enroll in this course to participate in Gurukul Jigyasa Q&A.",
                        error_code="not_enrolled",
                    )

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
        stripped_content = content.strip()
        if not stripped_content:
            raise BadRequestError("Answer content cannot be empty.")

        question = await CourseQuestion.find_one(CourseQuestion.id == question_id)
        if not question:
            raise NotFoundError("Question not found")

        is_admin_or_acharya = CourseService._is_staff(user)

        # 1. Reject answer if question was hidden by moderator/admin
        if getattr(question, "is_hidden", False) and not is_admin_or_acharya:
            raise NotFoundError("Question not found or has been hidden.")

        # 2. Verify active course enrollment for non-staff students
        if not is_admin_or_acharya:
            enrollment = await CourseEnrollment.find_one(
                CourseEnrollment.user_id == user.id,
                CourseEnrollment.course_id == question.course_id,
            )
            is_active = CourseService.is_enrollment_active(enrollment)
            if not is_active:
                lesson = await CourseLesson.find_one(
                    CourseLesson.id == question.lesson_id,
                    CourseLesson.course_id == question.course_id,
                )
                is_preview = bool(lesson and getattr(lesson, "is_free_preview", False))
                if not is_preview:
                    if enrollment:
                        raise ForbiddenError(
                            "Your course enrollment has expired. Please renew your access to answer questions in Gurukul Jigyasa Q&A.",
                            error_code="enrollment_expired",
                        )
                    raise ForbiddenError(
                        "Please enroll in this course to answer questions in Gurukul Jigyasa Q&A.",
                        error_code="not_enrolled",
                    )

        final_is_official = is_official or is_admin_or_acharya
        user_name = getattr(user, "full_name", None) or ("Acharya Guru" if final_is_official else "Astra Student")

        answer = CourseQuestionAnswer(
            user_id=user.id,
            user_name=user_name,
            user_role="admin" if is_admin_or_acharya else "student",
            user_avatar=getattr(user, "avatar_url", None),
            is_official=final_is_official,
            content=stripped_content,
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
        status: str = "all",  # "all", "unanswered", "answered", "resolved", "hidden"
        search: str | None = None,
        limit: int = 50,
        skip: int = 0,
    ) -> dict[str, Any]:
        """Provides full Q&A inquiry management with course, lesson & student details."""
        query: dict[str, Any] = {}
        if course_id:
            query["course_id"] = course_id
        if lesson_id:
            query["lesson_id"] = lesson_id

        if status == "unanswered":
            query["has_official_answer"] = {"$ne": True}
            query["is_resolved"] = {"$ne": True}
            query["is_hidden"] = {"$ne": True}
        elif status == "answered":
            query["has_official_answer"] = True
            query["is_hidden"] = {"$ne": True}
        elif status == "resolved":
            query["is_resolved"] = True
            query["is_hidden"] = {"$ne": True}
        elif status == "hidden":
            query["is_hidden"] = True
        else:
            query["is_hidden"] = {"$ne": True}

        if search and search.strip():
            pat = safe_regex_pattern(search)
            query["$or"] = [
                {"title": pat},
                {"content": pat},
                {"user_name": pat},
                {"user_email": pat},
                {"user_phone": pat},
            ]

        total = await CourseQuestion.find(query).count()
        unanswered_count = await CourseQuestion.find(
            {"has_official_answer": {"$ne": True}, "is_resolved": {"$ne": True}, "is_hidden": {"$ne": True}}
        ).count()
        resolved_count = await CourseQuestion.find({"is_resolved": True, "is_hidden": {"$ne": True}}).count()
        hidden_count = await CourseQuestion.find({"is_hidden": True}).count()

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
            "hidden_count": hidden_count,
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
        issued_dt = enrollment.certificate_issued_at or datetime.now(timezone.utc).replace(microsecond=0)
        student_name = getattr(user, "full_name", None) or "DivinLink Gurukul Scholar"
        student_email = getattr(user, "email", None)

        issued_iso = CourseService.format_certificate_issued_iso(issued_dt)

        # Compute deterministic canonical hash & HMAC-SHA256 signature
        canonical_hash, signature = CourseService.compute_certificate_crypto(
            cert_id=cert_id,
            user_id=str(user.id),
            student_name=student_name,
            course_id=str(course.id),
            course_title=course.title,
            issued_iso=issued_iso,
        )

        # Backward compatibility fallback for legacy certificates minted with dt.isoformat()
        if enrollment.certificate_signature and not hmac.compare_digest(enrollment.certificate_signature, signature):
            legacy_iso = issued_dt.isoformat()
            legacy_hash, legacy_sig = CourseService.compute_certificate_crypto(
                cert_id=cert_id,
                user_id=str(user.id),
                student_name=student_name,
                course_id=str(course.id),
                course_title=course.title,
                issued_iso=legacy_iso,
            )
            if hmac.compare_digest(enrollment.certificate_signature, legacy_sig):
                canonical_hash, signature = legacy_hash, legacy_sig
                issued_iso = legacy_iso

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
                "issued_iso": issued_iso,
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
        """Generates an exact-match printable A4 Landscape certificate matching the client DivinLink specification."""
        canonical_hash = cert.get("canonical_hash") or cert.get("digital_seal", {}).get("verification_hash", "")
        crypto_sig = cert.get("cryptographic_signature", "")
        student_name = cert.get("student_name", "Scholar")
        course_title = cert.get("course_title", "Bhrigunandi Naadi Jyotish")
        instructor = cert.get("instructor_name", "Rahul Sharma")
        if "Rahul" in instructor:
            instructor_display = "RAHUL SHARMA"
            instructor_clean = "Rahul Sharma"
        else:
            instructor_display = instructor.upper()
            instructor_clean = instructor

        issued_dt = cert.get("issued_at")
        if isinstance(issued_dt, datetime):
            month_name = issued_dt.strftime("%B")
            year_val = issued_dt.strftime("%Y")
        elif isinstance(issued_dt, str) and len(issued_dt) >= 7:
            try:
                dt_obj = datetime.fromisoformat(issued_dt.replace("Z", "+00:00"))
                month_name = dt_obj.strftime("%B")
                year_val = dt_obj.strftime("%Y")
            except Exception:
                month_name = "June"
                year_val = "2026"
        else:
            month_name = "June"
            year_val = "2026"

        held_line = f"that held in {month_name} year of {year_val}"
        web_url = getattr(settings, "FRONTEND_URL", "https://astra-astrology-web.vercel.app")
        encoded_verify_url = urllib.parse.quote(cert.get("verification_url", ""), safe="")
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={encoded_verify_url}"
        cert_id = cert.get("certificate_id", "ASTRA-CERT-VERIFIED")
        sig_short = crypto_sig[:24] + "..." if crypto_sig else "HMAC-SHA256"

        is_rahul = "rahul" in instructor.lower()
        if is_rahul:
            sig_element = f'<img src="{SIGNATURE_B64}" alt="Rahul Sharma Signature" class="sig-img" />'
        else:
            sig_element = f'<div class="sig-cursive">{instructor_clean}</div>'

        main_title = f"PARTICIPATION OF {course_title.upper()}"
        subtitle = "BASIC AND ADVANCE LEVEL ONLINE COURSE ON ZOOM"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=1000, initial-scale=1.0" />
  <title>Participation Certificate — {student_name} — {course_title}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Alex+Brush&family=Cinzel:wght@600;700;800;900&family=Playfair+Display:ital,wght@0,600;0,700;0,800;0,900;1,400;1,600&family=Marcellus&family=Montserrat:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    @page {{
      size: landscape;
      margin: 0;
    }}
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      -webkit-print-color-adjust: exact !important;
      print-color-adjust: exact !important;
    }}
    body {{
      background: #0B121E;
      color: #1A1816;
      font-family: 'Cinzel', 'Playfair Display', Georgia, serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 24px 12px;
    }}
    .actions-bar {{
      width: 1000px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 16px;
    }}
    .action-btn {{
      background: linear-gradient(135deg, #DEBA70 0%, #A57B2F 100%);
      color: #0B1B36;
      border: none;
      padding: 10px 22px;
      border-radius: 9999px;
      font-weight: 700;
      font-size: 13px;
      cursor: pointer;
      box-shadow: 0 4px 18px rgba(197, 155, 78, 0.4);
      transition: all 0.2s ease;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      font-family: 'Montserrat', sans-serif;
    }}
    .action-btn:hover {{
      transform: translateY(-2px);
      box-shadow: 0 6px 22px rgba(197, 155, 78, 0.6);
    }}
    .back-btn {{
      background: rgba(255, 255, 255, 0.08);
      color: #E5E7EB;
      border: 1px solid rgba(255, 255, 255, 0.15);
      padding: 9px 18px;
      border-radius: 9999px;
      font-size: 12.5px;
      font-weight: 600;
      cursor: pointer;
      text-decoration: none;
      font-family: 'Montserrat', sans-serif;
    }}
    .cert-outer {{
      width: 1000px;
      height: 523px;
      min-width: 1000px;
      max-width: 1000px;
      min-height: 523px;
      max-height: 523px;
      position: relative;
      overflow: hidden;
      border-radius: 8px;
      background-color: #FAF8F5;
      background-image: url('{CERTIFICATE_TEMPLATE_B64}');
      background-repeat: no-repeat;
      background-position: center center;
      background-size: 100% 100%;
      box-shadow: 0 25px 60px rgba(0, 0, 0, 0.75);
      user-select: none;
    }}
    .cert-content {{
      position: absolute;
      inset: 0;
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      z-index: 5;
    }}
    .cert-main-title {{
      position: absolute;
      top: 136px;
      left: 140px;
      right: 140px;
      font-family: 'Cinzel', serif;
      font-size: 20px;
      font-weight: 800;
      letter-spacing: 0.10em;
      color: #0E2042;
      text-transform: uppercase;
      line-height: 1.2;
    }}
    .cert-sub-title {{
      position: absolute;
      top: 166px;
      left: 140px;
      right: 140px;
      font-family: 'Cinzel', 'Montserrat', serif;
      font-size: 13px;
      font-weight: 700;
      letter-spacing: 0.18em;
      color: #9E7730;
      text-transform: uppercase;
    }}
    .cert-divider {{
      position: absolute;
      top: 188px;
      left: 0;
      right: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 10px;
      color: #B88E3E;
      letter-spacing: 4px;
    }}
    .cert-certify-line {{
      position: absolute;
      top: 212px;
      left: 0;
      right: 0;
      font-family: 'Playfair Display', Georgia, serif;
      font-style: italic;
      font-size: 15.5px;
      color: #374151;
      letter-spacing: 0.02em;
    }}
    .cert-student-name {{
      position: absolute;
      top: 236px;
      left: 140px;
      right: 140px;
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 38px;
      font-weight: 800;
      color: #0B1B36;
      line-height: 1.1;
      letter-spacing: 0.02em;
    }}
    .cert-body-line-1 {{
      position: absolute;
      top: 294px;
      left: 140px;
      right: 140px;
      font-family: 'Marcellus', Georgia, serif;
      font-size: 14px;
      color: #1F2937;
    }}
    .cert-body-line-2 {{
      position: absolute;
      top: 314px;
      left: 140px;
      right: 140px;
      font-family: 'Marcellus', Georgia, serif;
      font-size: 14px;
      color: #1F2937;
    }}
    .cert-signatory-wrap {{
      position: absolute;
      top: 356px;
      left: 210px;
      right: 210px;
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
    }}
    .sig-top-name {{
      font-family: 'Montserrat', sans-serif;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.12em;
      color: #0B1B36;
      text-transform: uppercase;
    }}
    .sig-wishes {{
      font-family: 'Playfair Display', Georgia, serif;
      font-style: italic;
      font-size: 12.5px;
      color: #4B5563;
      margin-top: 1px;
    }}
    .sig-img {{
      height: 38px;
      object-fit: contain;
      margin: 1px 0;
    }}
    .sig-cursive {{
      font-family: 'Alex Brush', cursive;
      font-size: 34px;
      color: #1A2538;
      line-height: 1;
      margin: 2px 0;
    }}
    .sig-line {{
      width: 200px;
      height: 1px;
      background: #CBD5E1;
      margin: 2px auto 4px auto;
    }}
    .sig-bottom-name {{
      font-family: 'Cinzel', 'Montserrat', sans-serif;
      font-size: 12px;
      font-weight: 800;
      letter-spacing: 0.10em;
      color: #0B1B36;
      text-transform: uppercase;
    }}
    .sig-bottom-org {{
      font-family: 'Cinzel', 'Montserrat', sans-serif;
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 0.16em;
      color: #64748B;
      text-transform: uppercase;
      margin-top: 1px;
    }}
    .cert-qr-container {{
      position: absolute;
      bottom: 24px;
      right: 32px;
      display: flex;
      flex-direction: column;
      align-items: center;
      text-decoration: none;
      z-index: 10;
      opacity: 0.9;
      transition: opacity 0.2s;
    }}
    .cert-qr-container:hover {{
      opacity: 1;
    }}
    .cert-qr-img {{
      width: 44px;
      height: 44px;
      border-radius: 4px;
      border: 1px solid rgba(197, 155, 78, 0.4);
      background: #FFFFFF;
      padding: 2px;
    }}
    .cert-qr-label {{
      font-family: 'Montserrat', sans-serif;
      font-size: 6.5px;
      font-weight: 700;
      color: #9E7730;
      letter-spacing: 0.5px;
      margin-top: 2px;
      text-transform: uppercase;
    }}
    .cert-security-bar {{
      position: absolute;
      bottom: 6px;
      left: 20px;
      right: 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-family: monospace;
      font-size: 6.5px;
      color: #8C7A62;
      opacity: 0.65;
      letter-spacing: 1px;
      text-transform: uppercase;
      pointer-events: none;
    }}
    @media print {{
      body {{
        background: transparent !important;
        padding: 0 !important;
      }}
      .actions-bar {{
        display: none !important;
      }}
      .cert-outer {{
        box-shadow: none !important;
        border-radius: 0 !important;
        width: 100% !important;
        height: 100vh !important;
        page-break-inside: avoid !important;
        break-inside: avoid !important;
      }}
    }}
  </style>
</head>
<body>
  <div class="actions-bar">
    <a href="{web_url}/account/courses" class="back-btn">← Back to My Courses</a>
    <button onclick="window.print()" class="action-btn">🖨️ Print / Save PDF</button>
  </div>

  <div class="cert-outer">
    <div class="cert-content">
      <div class="cert-main-title">{main_title}</div>
      <div class="cert-sub-title">{subtitle}</div>
      <div class="cert-divider">———— ◆ ————</div>
      <div class="cert-certify-line">This is to certify that</div>
      <div class="cert-student-name">{student_name}</div>
      <div class="cert-body-line-1">Has successfully completed online course of {course_title}</div>
      <div class="cert-body-line-2">{held_line}</div>

      <div class="cert-signatory-wrap">
        <div class="sig-top-name">{instructor_display}</div>
        <div class="sig-wishes">wishes him/her all the best for future</div>
        {sig_element}
        <div class="sig-line"></div>
        <div class="sig-bottom-name">{instructor_display}</div>
        <div class="sig-bottom-org">DIVINLINK</div>
      </div>
    </div>

    <!-- Official Tamper-Proof Cryptographic Verification QR Code -->
    <a href="{cert.get('verification_url', '')}" target="_blank" rel="noopener noreferrer" class="cert-qr-container" title="Verify authenticity online">
      <img src="{qr_url}" alt="Certificate QR" class="cert-qr-img" />
      <span class="cert-qr-label">Verify Credential</span>
    </a>

    <!-- Anti-Fraud Security Bar -->
    <div class="cert-security-bar">
      <span>ID: {cert_id} • CANONICAL HASH: {canonical_hash[:20]}...</span>
      <span>DIGITAL SIGNATURE: {sig_short} • OFFICIALLY CONSECRATED</span>
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
        if not enrollment.certificate_issued_at:
            enrollment.certificate_issued_at = datetime.now(timezone.utc).replace(microsecond=0)
        enrollment.certificate_issued = True

        cert_data = CourseService.generate_course_certificate_data(enrollment, course, user)
        expected_cert_url = cert_data.get("verification_url")
        crypto_sig = cert_data.get("cryptographic_signature")
        c_hash = cert_data.get("canonical_hash")

        if (
            enrollment.certificate_signature != crypto_sig
            or enrollment.certificate_canonical_hash != c_hash
            or enrollment.certificate_url != expected_cert_url
        ):
            enrollment.certificate_signature = crypto_sig
            enrollment.certificate_canonical_hash = c_hash
            enrollment.certificate_url = expected_cert_url
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
            # Cross-compatibility between ASTRA-CERT- and DIVINLINK-CERT-
            if clean_id.startswith("ASTRA-CERT-"):
                divinlink_id = clean_id.replace("ASTRA-CERT-", "DIVINLINK-CERT-")
                enrollment = await CourseEnrollment.find_one(CourseEnrollment.certificate_id == divinlink_id)
            elif clean_id.startswith("DIVINLINK-CERT-"):
                astra_id = clean_id.replace("DIVINLINK-CERT-", "ASTRA-CERT-")
                enrollment = await CourseEnrollment.find_one(CourseEnrollment.certificate_id == astra_id)
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
            is_public_verification=True,
        )

    @staticmethod
    async def reconcile_all_completed_certificates() -> dict[str, Any]:
        """Scans all course enrollments across the entire system.

        For every student who completed 100% of a course (or completed all published lessons):
        1. Ensures progress_percent is 100.0 and certificate_issued is True.
        2. Mints a certificate_id if not present.
        3. Updates certificate_issued_at if not present.
        4. Recomputes deterministic canonical hash and HMAC-SHA256 signature with latest DivinLink authority.
        5. Updates certificate_signature, certificate_canonical_hash, and certificate_url.
        6. Saves updated enrollment back to database.
        Returns a summary of total enrollments checked, completed, and updated.
        """
        web_url = getattr(settings, "FRONTEND_URL", "https://astra-astrology-web.vercel.app")
        all_enrollments = await CourseEnrollment.find_all().to_list()
        courses_cache: dict[str, Course] = {}
        users_cache: dict[str, User] = {}

        total_checked = len(all_enrollments)
        completed_found = 0
        updated_count = 0

        for enrollment in all_enrollments:
            course_id_str = str(enrollment.course_id)
            if course_id_str not in courses_cache:
                c = await Course.find_one(Course.id == enrollment.course_id)
                if c:
                    courses_cache[course_id_str] = c
            course = courses_cache.get(course_id_str)
            if not course:
                continue

            user_id_str = str(enrollment.user_id)
            if user_id_str not in users_cache:
                u = await User.find_one(User.id == enrollment.user_id)
                if u:
                    users_cache[user_id_str] = u
            user = users_cache.get(user_id_str)
            if not user:
                continue

            # Determine completion
            total_published = await CourseLesson.find(
                CourseLesson.course_id == enrollment.course_id,
                {"is_published": {"$ne": False}},
            ).count()

            is_completed = (
                enrollment.progress_percent >= 100.0
                or (total_published > 0 and len(enrollment.completed_lesson_ids or []) >= total_published)
                or enrollment.certificate_issued
            )

            if not is_completed:
                continue

            completed_found += 1
            changed = False

            if enrollment.progress_percent < 100.0:
                enrollment.progress_percent = 100.0
                changed = True

            if not enrollment.certificate_issued:
                enrollment.certificate_issued = True
                changed = True

            if not enrollment.certificate_id:
                enrollment.certificate_id = CourseService.mint_certificate_id()
                changed = True

            if not enrollment.certificate_issued_at:
                enrollment.certificate_issued_at = datetime.now(timezone.utc).replace(microsecond=0)
                changed = True

            student_name = getattr(user, "full_name", None) or "DivinLink Gurukul Scholar"
            issued_iso = CourseService.format_certificate_issued_iso(enrollment.certificate_issued_at)

            canonical_hash, signature = CourseService.compute_certificate_crypto(
                cert_id=enrollment.certificate_id,
                user_id=str(user.id),
                student_name=student_name,
                course_id=str(course.id),
                course_title=course.title,
                issued_iso=issued_iso,
            )

            expected_url = f"{web_url}/verify/certificate/{enrollment.certificate_id}?sig={signature[:32]}"

            if enrollment.certificate_canonical_hash != canonical_hash:
                enrollment.certificate_canonical_hash = canonical_hash
                changed = True

            if enrollment.certificate_signature != signature:
                enrollment.certificate_signature = signature
                changed = True

            if enrollment.certificate_url != expected_url:
                enrollment.certificate_url = expected_url
                changed = True

            if changed:
                await enrollment.save()
                updated_count += 1
                logger.info(
                    "Reconciled certificate for user {} ({}) on course {}: cert_id={}",
                    user.id,
                    student_name,
                    course.title,
                    enrollment.certificate_id,
                )

        return {
            "total_enrollments_checked": total_checked,
            "completed_enrollments": completed_found,
            "certificates_reconciled_and_updated": updated_count,
        }

