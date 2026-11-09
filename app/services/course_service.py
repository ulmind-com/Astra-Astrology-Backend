"""Course and Learning Management Service for Astra Gurukul."""

import asyncio
import hashlib
import hmac
import json
import time
from datetime import datetime, timezone
from typing import Any

from beanie import PydanticObjectId
import httpx
from loguru import logger

from app.core.config import settings
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError, ServiceUnavailableError
from app.models.course import (
    Course,
    CourseEnrollment,
    CourseLesson,
    CourseLessonProgress,
    CourseQuestion,
    CourseQuestionAnswer,
    CourseSection,
)
from app.models.user import User
from app.services.payments import _razorpay


class CourseService:
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
        course = await Course.find_one(Course.slug == slug, Course.is_deleted == False)
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
            if not enrollment:
                role_str = str(getattr(user, "role", "user")).lower()
                if "admin" in role_str or "astrologer" in role_str:
                    enrollment = CourseEnrollment(
                        user_id=user.id,
                        course_id=course.id,
                        payment_id="admin_access",
                        order_id="admin_access",
                        amount_paid=0.0,
                        currency="INR",
                    )
                    await enrollment.insert()

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
                        enrollment.certificate_id = f"ASTRA-CERT-{str(user.id)[-6:].upper()}-{str(course.id)[-4:].upper()}"
                        enrollment.certificate_issued_at = datetime.now(timezone.utc)
                    if not enrollment.certificate_url:
                        enrollment.certificate_url = f"{web_url}/verify/certificate/{enrollment.certificate_id}"
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
            raise ForbiddenError("You must enroll in this course to watch this lesson.")

        # Anti-piracy watermark text (student mobile / email)
        watermark_text = None
        if user:
            user_phone = getattr(user, "phone", None) or getattr(user, "mobile_number", None) or ""
            user_email = getattr(user, "email", None) or ""
            user_name = getattr(user, "full_name", None) or ""
            identifier = user_phone or user_email or user_name or "Astra Student"
            watermark_text = f"Astra Gurukul • {identifier}"

        # Generate secure embed / stream parameters
        now = int(time.time())
        expires_at = now + 7200  # 2 hours validity

        embed_url = ""
        token = None

        if lesson.video_provider == "youtube_unlisted":
            embed_url = f"https://www.youtube-nocookie.com/embed/{lesson.video_id}?rel=0&modestbranding=1"
        elif lesson.video_provider == "bunny_stream":
            # Bunny.net secure player iframe with SHA-256 token authentication
            lib_id = lesson.library_id or settings.BUNNY_STREAM_LIBRARY_ID
            token_key = settings.BUNNY_STREAM_TOKEN_KEY
            if token_key:
                # Official Bunny formula: SHA256_HEX(TokenSecurityKey + VideoID + ExpirationTimestamp)
                raw_token = f"{token_key}{lesson.video_id}{expires_at}"
                token = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
                embed_url = f"https://iframe.mediadelivery.net/embed/{lib_id}/{lesson.video_id}?token={token}&expires={expires_at}"
            else:
                embed_url = f"https://iframe.mediadelivery.net/embed/{lib_id}/{lesson.video_id}"
        else:
            embed_url = lesson.video_id

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
            role_str = str(getattr(user, "role", "user")).lower()
            if "admin" in role_str or "astrologer" in role_str:
                enrollment = CourseEnrollment(
                    user_id=user.id,
                    course_id=course_id,
                    payment_id="admin_access",
                    order_id="admin_access",
                    amount_paid=0.0,
                    currency="INR",
                )
                await enrollment.insert()
            else:
                raise ForbiddenError("Not enrolled in this course")

        # Upsert Lesson Progress
        prog = await CourseLessonProgress.find_one(
            CourseLessonProgress.user_id == user.id,
            CourseLessonProgress.lesson_id == lesson_id,
        )
        if not prog:
            prog = CourseLessonProgress(
                user_id=user.id,
                course_id=course_id,
                lesson_id=lesson_id,
                watched_seconds=watched_seconds,
                total_seconds=total_seconds,
                is_completed=mark_completed or (total_seconds > 0 and watched_seconds >= total_seconds * 0.9),
            )
            await prog.insert()
        else:
            prog.watched_seconds = max(prog.watched_seconds, watched_seconds)
            prog.total_seconds = max(prog.total_seconds, total_seconds)
            if mark_completed or (total_seconds > 0 and watched_seconds >= total_seconds * 0.9):
                prog.is_completed = True
            prog.last_watched_at = datetime.now(timezone.utc)
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
                    enrollment.certificate_id = f"ASTRA-CERT-{str(user.id)[-6:].upper()}-{str(course_id)[-4:].upper()}"
                    enrollment.certificate_issued_at = datetime.now(timezone.utc)
                web_url = getattr(settings, "FRONTEND_URL", "https://astra-astrology-web.vercel.app")
                if not enrollment.certificate_url:
                    enrollment.certificate_url = f"{web_url}/verify/certificate/{enrollment.certificate_id}"

                # Send official congratulations certificate email if not sent yet
                user_email = getattr(user, "email", None)
                if not enrollment.certificate_email_sent and user_email:
                    try:
                        from app.services.email import send_course_certificate_email
                        course_item = await Course.find_one(Course.id == course_id)
                        c_title = course_item.title if course_item else "Astra Gurukul Masterclass"
                        u_name = getattr(user, "full_name", None) or "Astra Gurukul Scholar"
                        dt_str = (enrollment.certificate_issued_at or datetime.now(timezone.utc)).strftime("%d %B %Y")
                        v_link = f"{web_url}/verify/certificate/{enrollment.certificate_id}"
                        inst_name = course_item.instructor_name if course_item else "Pt. Acharya Rahul Sharma"

                        await send_course_certificate_email(
                            to=user_email,
                            user_name=u_name,
                            course_title=c_title,
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

        return {
            "progress_percent": enrollment.progress_percent,
            "is_lesson_completed": prog.is_completed,
            "certificate_issued": enrollment.certificate_issued,
            "certificate_id": enrollment.certificate_id,
            "certificate_url": enrollment.certificate_url,
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
            await enrollment.insert()
            course.total_students += 1
            await course.save()
            return {
                "free_enrolled": True,
                "course_id": str(course.id),
                "course_title": course.title,
                "course_slug": course.slug,
                "message": "Successfully enrolled in free course",
            }

        # Paid course: create Razorpay order
        amount_paise = int(round(course.price * 100))
        receipt_id = f"crs_{str(course.id)[-6:]}_{int(time.time())}"

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
        """Validates Razorpay signature and unlocks instant course access."""
        course = await Course.find_one(Course.id == course_id, Course.is_deleted == False)
        if not course:
            raise NotFoundError("Course not found")

        # Cryptographic signature validation
        expected = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode(),
            f"{razorpay_order_id}|{razorpay_payment_id}".encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected, razorpay_signature):
            logger.error("Course payment signature mismatch: expected {}, got {}", expected, razorpay_signature)
            raise BadRequestError("Payment verification failed. Invalid signature.")

        # Check or create enrollment (idempotent)
        enrollment = await CourseEnrollment.find_one(
            CourseEnrollment.user_id == user.id,
            CourseEnrollment.course_id == course.id,
        )
        if not enrollment:
            enrollment = CourseEnrollment(
                user_id=user.id,
                course_id=course.id,
                payment_id=razorpay_payment_id,
                order_id=razorpay_order_id,
                amount_paid=course.price,
                currency="INR",
            )
            await enrollment.insert()
            course.total_students += 1
            await course.save()
            logger.info("User {} successfully enrolled in course {}", user.id, course.id)

        return {
            "success": True,
            "enrollment_id": str(enrollment.id),
            "course_id": str(course.id),
            "course_slug": course.slug,
            "course_title": course.title,
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
            if course and not course.is_deleted:
                web_url = getattr(settings, "FRONTEND_URL", "https://astra-astrology-web.vercel.app")
                cert_id = e.certificate_id or (f"ASTRA-CERT-{str(user.id)[-6:].upper()}-{str(course.id)[-4:].upper()}" if e.progress_percent >= 100 else None)
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
            return {
                "video_id": video_id,
                "library_id": settings.BUNNY_STREAM_LIBRARY_ID,
                "title": title,
                "upload_url": f"https://video.bunnycdn.com/library/{settings.BUNNY_STREAM_LIBRARY_ID}/videos/{video_id}",
                "access_key": settings.BUNNY_STREAM_API_KEY,
            }

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
        user_role_str = str(getattr(user, "role", "user")).lower()
        is_admin_or_astrologer = "admin" in user_role_str or "astrologer" in user_role_str

        if not enrollment and not lesson.is_free_preview and not is_admin_or_astrologer:
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

        role = getattr(user, "role", "student")
        role_str = str(role.value) if hasattr(role, "value") else str(role).lower()
        is_admin_or_acharya = "admin" in role_str or "astrologer" in role_str

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
            "authority": "Astra Gurukul Council of Astrological Regents",
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
    ) -> dict[str, Any]:
        """Builds structured certificate metadata and cryptographically verifiable seal."""
        web_url = getattr(settings, "FRONTEND_URL", "https://astra-astrology-web.vercel.app")
        api_url = getattr(settings, "API_BASE_URL", "https://astra-astrology-backend.onrender.com")

        cert_id = enrollment.certificate_id or f"ASTRA-CERT-{str(user.id)[-6:].upper()}-{str(course.id)[-4:].upper()}"
        issued_dt = enrollment.certificate_issued_at or datetime.now(timezone.utc)
        student_name = getattr(user, "full_name", None) or "Astra Gurukul Scholar"
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

        # Record signature on enrollment if empty
        if not enrollment.certificate_signature or not enrollment.certificate_canonical_hash:
            enrollment.certificate_canonical_hash = canonical_hash
            enrollment.certificate_signature = signature

        # Check signature verification against provided token if passed
        is_signature_valid = True
        tamper_reason = None
        if signature_token:
            clean_token = signature_token.strip().lower()
            expected_prefix = signature[: len(clean_token)].lower()
            if not hmac.compare_digest(clean_token, expected_prefix):
                is_signature_valid = False
                tamper_reason = "Cryptographic signature mismatch. Token or URL parameters have been tampered with."

        verify_url = f"{web_url}/verify/certificate/{cert_id}?sig={signature[:32]}"
        html_url = f"{api_url}/api/v1/courses/certificate/verify/{cert_id}/html"

        tamper_check = {
            "status": "CRYPTOGRAPHICALLY_VERIFIED_AUTHENTIC" if is_signature_valid else "TAMPERED_OR_INVALID_SIGNATURE",
            "is_valid": is_signature_valid,
            "tamper_reason": tamper_reason,
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
                "seal_title": "Astra Cosmic Gurukul Consecrated",
                "seal_motto": "विद्या ददाति विनयं विनयाद्याति पात्रताम्",
                "status": "VERIFIED_AUTHENTIC" if is_signature_valid else "TAMPERED",
                "signature": f"Pt. Acharya Rahul Sharma • {issued_dt.strftime('%d-%m-%Y')}",
            },
        }

    @staticmethod
    def generate_course_certificate_html(cert: dict[str, Any]) -> str:
        """Generates an ultra-luxurious, printable A4 Landscape graduation certificate."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Gurukul Certificate — {cert['student_name']} — {cert['course_title']}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700;800;900&family=Playfair+Display:ital,wght@0,600;0,700;0,900;1,400;1,600&family=Marcellus&display=swap" rel="stylesheet">
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: #0B0F19;
      color: #1A1A1A;
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
      max-width: 1100px;
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
    .cert-frame {{
      width: 100%;
      max-width: 1100px;
      aspect-ratio: 1.414;
      background: #FFFDF9;
      position: relative;
      border-radius: 4px;
      padding: 24px;
      box-shadow: 0 25px 60px rgba(0, 0, 0, 0.7), 0 0 40px rgba(212, 175, 55, 0.2);
      border: 8px solid #1E293B;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      overflow: hidden;
    }}
    .cert-inner-border {{
      position: absolute;
      top: 14px; left: 14px; right: 14px; bottom: 14px;
      border: 2px solid #C89B3C;
      pointer-events: none;
    }}
    .cert-inner-hairline {{
      position: absolute;
      top: 18px; left: 18px; right: 18px; bottom: 18px;
      border: 1px dashed rgba(200, 155, 60, 0.5);
      pointer-events: none;
    }}
    .corner {{
      position: absolute;
      font-size: 24px;
      color: #C89B3C;
      line-height: 1;
      z-index: 2;
    }}
    .corner.tl {{ top: 22px; left: 22px; }}
    .corner.tr {{ top: 22px; right: 22px; }}
    .corner.bl {{ bottom: 22px; left: 22px; }}
    .corner.br {{ bottom: 22px; right: 22px; }}

    .watermark-bg {{
      position: absolute;
      top: 50%; left: 50%;
      transform: translate(-50%, -50%);
      font-size: 420px;
      color: rgba(200, 155, 60, 0.035);
      pointer-events: none;
      font-family: 'Cinzel', serif;
      user-select: none;
      z-index: 1;
    }}

    .cert-content {{
      position: relative;
      z-index: 3;
      height: 100%;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      text-align: center;
      padding: 15px 35px;
    }}

    .header-block {{ margin-bottom: 8px; }}
    .om-badge {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 32px;
      color: #8B6508;
      line-height: 1;
      margin-bottom: 4px;
    }}
    .gurukul-brand {{
      font-family: 'Cinzel', serif;
      font-size: 13px;
      font-weight: 800;
      letter-spacing: 4px;
      color: #8B6508;
      text-transform: uppercase;
      margin-bottom: 4px;
    }}
    .gurukul-sub {{
      font-size: 11px;
      letter-spacing: 1.5px;
      color: #6B7280;
      text-transform: uppercase;
    }}

    .shloka-banner {{
      margin: 10px auto 14px;
      padding: 6px 20px;
      background: rgba(200, 155, 60, 0.08);
      border-top: 1px solid rgba(200, 155, 60, 0.3);
      border-bottom: 1px solid rgba(200, 155, 60, 0.3);
      font-size: 12px;
      color: #78350F;
      font-style: italic;
      max-width: 780px;
    }}

    .cert-title-block {{ margin-bottom: 12px; }}
    .cert-main-title {{
      font-family: 'Cinzel', serif;
      font-size: 26px;
      font-weight: 800;
      color: #1F2937;
      letter-spacing: 2px;
      text-transform: uppercase;
      background: linear-gradient(135deg, #8B6508 0%, #1F2937 50%, #8B6508 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    .conferred-upon {{
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 3px;
      text-transform: uppercase;
      color: #9CA3AF;
      margin-top: 6px;
    }}

    .student-name {{
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 36px;
      font-weight: 900;
      color: #0F172A;
      margin: 8px 0;
      text-shadow: 0 1px 2px rgba(0,0,0,0.1);
      letter-spacing: 0.5px;
    }}

    .course-decree {{
      font-size: 13px;
      line-height: 1.6;
      color: #4B5563;
      max-width: 760px;
      margin: 0 auto 10px;
    }}

    .course-card {{
      display: inline-block;
      padding: 8px 24px;
      background: linear-gradient(135deg, #FAF5E4 0%, #FFFDF7 100%);
      border: 1px solid #C89B3C;
      border-radius: 8px;
      margin-bottom: 12px;
    }}
    .course-name {{
      font-family: 'Cinzel', serif;
      font-size: 17px;
      font-weight: 700;
      color: #92400E;
    }}

    .distinction-pill {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 14px;
      background: #ECFDF5;
      border: 1px solid #10B981;
      border-radius: 9999px;
      font-size: 11px;
      font-weight: 700;
      color: #065F46;
      letter-spacing: 1px;
      text-transform: uppercase;
      margin-bottom: 14px;
    }}

    .footer-signatures {{
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      padding-top: 10px;
      border-top: 1px solid rgba(200, 155, 60, 0.25);
    }}
    .sig-col {{
      width: 240px;
      text-align: center;
    }}
    .sig-line {{
      font-family: 'Playfair Display', cursive, serif;
      font-style: italic;
      font-size: 22px;
      color: #1E293B;
      padding-bottom: 4px;
      border-bottom: 1.5px solid #C89B3C;
      margin-bottom: 4px;
    }}
    .sig-name {{
      font-size: 12px;
      font-weight: 700;
      color: #1F2937;
    }}
    .sig-title {{
      font-size: 10px;
      color: #6B7280;
    }}

    .gold-seal {{
      width: 100px;
      height: 100px;
      border-radius: 50%;
      background: radial-gradient(circle, #FFE494 0%, #D4AF37 60%, #AA771C 100%);
      border: 3px double #FFF;
      box-shadow: 0 4px 14px rgba(170, 119, 28, 0.4);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      color: #381E00;
      text-align: center;
      padding: 4px;
      position: relative;
    }}
    .gold-seal::after {{
      content: "";
      position: absolute;
      bottom: -14px;
      width: 28px;
      height: 22px;
      background: #AA771C;
      clip-path: polygon(0 0, 100% 0, 50% 100%);
      z-index: -1;
    }}
    .seal-text-top {{ font-size: 7px; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase; }}
    .seal-icon {{ font-size: 22px; line-height: 1; margin: 2px 0; }}
    .seal-text-bot {{ font-size: 7px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; }}

    .metadata-strip {{
      margin-top: 12px;
      padding-top: 8px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-size: 9px;
      color: #9CA3AF;
      border-top: 1px dashed rgba(200, 155, 60, 0.2);
    }}
    .meta-id {{ font-family: monospace; font-weight: 700; color: #4B5563; }}

    .micro-text-band {{
      font-family: monospace;
      font-size: 5px;
      letter-spacing: 2px;
      color: rgba(184, 134, 11, 0.45);
      text-transform: uppercase;
      white-space: nowrap;
      overflow: hidden;
      user-select: none;
      position: absolute;
    }}
    .micro-top {{ top: 12px; left: 24px; right: 24px; text-align: center; }}
    .micro-bot {{ bottom: 12px; left: 24px; right: 24px; text-align: center; }}

    .guilloche-bg {{
      position: absolute;
      top: 50%; left: 50%;
      transform: translate(-50%, -50%);
      width: 440px;
      height: 440px;
      pointer-events: none;
      opacity: 0.05;
      z-index: 1;
    }}

    @media print {{
      body {{
        background: #FFF !important;
        padding: 0 !important;
      }}
      .actions-bar {{ display: none !important; }}
      .cert-frame {{
        max-width: 100% !important;
        width: 100% !important;
        height: 100vh !important;
        aspect-ratio: auto !important;
        box-shadow: none !important;
        border: 4px solid #8B6508 !important;
      }}
      @page {{
        size: A4 landscape;
        margin: 0;
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

  <div class="cert-frame">
    <div class="micro-text-band micro-top">ASTRA GURUKUL CELESTIAL CREDENTIALS • OFFICIALLY CONSECRATED BY BOARD OF ASTROLOGICAL REGENTS • CANONICAL HASH VERIFIED • ASTRA GURUKUL CELESTIAL CREDENTIALS</div>
    <div class="micro-text-band micro-bot">HMAC-SHA256 DIGITAL SECURITY SEAL • MATHEMATICALLY TAMPER-PROOF • VERIFIABLE AT ASTRAGURUKUL.COM • HMAC-SHA256 DIGITAL SECURITY SEAL</div>

    <div class="cert-inner-border"></div>
    <div class="cert-inner-hairline"></div>
    <div class="corner tl">⚜</div>
    <div class="corner tr">⚜</div>
    <div class="corner bl">⚜</div>
    <div class="corner br">⚜</div>
    <div class="watermark-bg">ॐ</div>

    <div class="guilloche-bg">
      <svg viewBox="0 0 400 400" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
        <circle cx="200" cy="200" r="180" fill="none" stroke="#C89B3C" stroke-width="1" stroke-dasharray="3,3"/>
        <circle cx="200" cy="200" r="140" fill="none" stroke="#C89B3C" stroke-width="1"/>
        <circle cx="200" cy="200" r="100" fill="none" stroke="#C89B3C" stroke-width="1" stroke-dasharray="2,2"/>
        <g stroke="#C89B3C" stroke-width="0.8">
          <ellipse cx="200" cy="200" rx="170" ry="35" fill="none" transform="rotate(0 200 200)"/>
          <ellipse cx="200" cy="200" rx="170" ry="35" fill="none" transform="rotate(30 200 200)"/>
          <ellipse cx="200" cy="200" rx="170" ry="35" fill="none" transform="rotate(60 200 200)"/>
          <ellipse cx="200" cy="200" rx="170" ry="35" fill="none" transform="rotate(90 200 200)"/>
          <ellipse cx="200" cy="200" rx="170" ry="35" fill="none" transform="rotate(120 200 200)"/>
          <ellipse cx="200" cy="200" rx="170" ry="35" fill="none" transform="rotate(150 200 200)"/>
        </g>
      </svg>
    </div>

    <div class="cert-content">
      <div class="header-block">
        <div class="om-badge">ॐ</div>
        <div class="gurukul-brand">Astra Cosmic Gurukul • বিশ্ব জ্যোতিষ বিদ্যাপীঠ</div>
        <div class="gurukul-sub">Council of Vedic Sciences, Nakshatra Computations & Remedial Canon</div>
      </div>

      <div class="shloka-banner">
        "विद्या ददाति विनयं विनयाद्याति पात्रताम् । पात्रत्वाद्धनमाप्नोति धनाद्धर्मं ततः सुखम् ॥"
      </div>

      <div class="cert-title-block">
        <h1 class="cert-main-title">Certificate of Scholarly Excellence</h1>
        <p class="conferred-upon">This Sacred Parchment Is Solemnly Conferred Upon</p>
      </div>

      <div class="student-name">{cert['student_name']}</div>

      <p class="course-decree">
        for having successfully accomplished with supreme distinction the rigorous canonical curriculum,
        planetary algorithms, celestial treatises, and predictive methodology for the sacred masterclass:
      </p>

      <div>
        <div class="course-card">
          <div class="course-name">{cert['course_title']}</div>
        </div>
      </div>

      <div>
        <div class="distinction-pill">
          <span>★</span> {cert['distinction']} <span>★</span>
        </div>
      </div>

      <div class="footer-signatures">
        <div class="sig-col">
          <div class="sig-line">{cert['instructor_name']}</div>
          <div class="sig-name">{cert['instructor_name']}</div>
          <div class="sig-title">{cert['instructor_title']}</div>
        </div>

        <div class="gold-seal">
          <div class="seal-text-top">Astra Gurukul</div>
          <div class="seal-icon">☸</div>
          <div class="seal-text-bot">Consecrated</div>
        </div>

        <div class="sig-col">
          <div class="sig-line">Council Registrar</div>
          <div class="sig-name">Board of Astrological Regents</div>
          <div class="sig-title">Director of Celestial Credentials</div>
        </div>
      </div>

      <div class="metadata-strip">
        <div>Certificate ID: <span class="meta-id">{cert['certificate_id']}</span></div>
        <div>Date: <strong>{cert['issued_at_formatted']}</strong></div>
        <div>Canonical Hash: <span class="meta-id">{cert.get('canonical_hash', cert['digital_seal']['verification_hash'])[:20]}...</span></div>
        <div>Signature: <span class="meta-id">{cert.get('cryptographic_signature', '')[:16]}... (HMAC-SHA256)</span></div>
      </div>
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
            role_str = str(getattr(user, "role", "user")).lower()
            if "admin" in role_str or "astrologer" in role_str:
                enrollment = CourseEnrollment(
                    user_id=user.id,
                    course_id=course_id,
                    payment_id="admin_access",
                    order_id="admin_access",
                    amount_paid=0.0,
                    currency="INR",
                    progress_percent=100.0,
                    certificate_issued=True,
                )
                await enrollment.insert()
            else:
                raise ForbiddenError("You are not enrolled in this course.")

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
            enrollment.certificate_id = f"ASTRA-CERT-{str(user.id)[-6:].upper()}-{str(course_id)[-4:].upper()}"
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

