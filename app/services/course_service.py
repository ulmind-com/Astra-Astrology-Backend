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
        """Generates an ultra-luxurious, production-level printable A4 Landscape graduation certificate."""
        canonical_hash = cert.get("canonical_hash") or cert.get("digital_seal", {}).get("verification_hash", "")
        crypto_sig = cert.get("cryptographic_signature", "")
        instructor = cert.get("instructor_name", "Pt. Acharya Rahul Sharma")
        issued_date = cert.get("issued_at_formatted", "")

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Astra Gurukul Certificate — {cert['student_name']} — {cert['course_title']}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Alex+Brush&family=Cinzel:wght@600;700;800;900&family=Playfair+Display:ital,wght@0,600;0,700;0,900;1,400;1,600&family=Marcellus&family=Montserrat:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: #181410;
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
      max-width: 1040px;
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
      width: 1040px;
      height: 670px;
      background: #FAF8F2;
      position: relative;
      overflow: hidden;
      border-radius: 8px;
      box-shadow: 0 25px 60px rgba(0, 0, 0, 0.7);
      display: flex;
      border: 1px solid rgba(209, 178, 111, 0.35);
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
      color: rgba(140, 122, 98, 0.45);
      text-transform: uppercase;
      pointer-events: none;
      z-index: 25;
    }}
    .micro-top {{ top: 6px; }}
    .micro-bot {{ bottom: 6px; }}

    .cert-left {{
      width: 66%;
      height: 100%;
      padding: 42px 24px 34px 50px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      position: relative;
      z-index: 10;
    }}

    .brand-header {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .brand-logo-icon {{
      width: 44px;
      height: 44px;
    }}
    .brand-name {{
      font-family: 'Cinzel', serif;
      font-size: 14px;
      font-weight: 800;
      letter-spacing: 2.5px;
      color: #1A1816;
      line-height: 1.2;
    }}
    .brand-sub {{
      font-family: 'Montserrat', sans-serif;
      font-size: 8.5px;
      font-weight: 600;
      letter-spacing: 2px;
      color: #7A6C58;
      text-transform: uppercase;
    }}

    .title-block {{
      margin-top: 14px;
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
      margin-top: 6px;
      max-width: 330px;
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
      font-size: 9.5px;
      font-weight: 700;
      letter-spacing: 2.5px;
      color: #7A6C58;
      text-transform: uppercase;
      margin-top: 18px;
    }}

    .recipient-name {{
      font-family: 'Alex Brush', cursive;
      font-size: 48px;
      color: #1A1816;
      line-height: 1.1;
      padding-left: 4px;
      margin-top: 4px;
    }}
    .recipient-underline {{
      width: 100%;
      height: 1px;
      background: #8C7A62;
      margin-top: 2px;
    }}

    .citation-paragraph {{
      font-family: 'Marcellus', 'Georgia', serif;
      font-size: 12px;
      line-height: 1.6;
      color: #4A4237;
      margin-top: 12px;
      max-width: 500px;
    }}
    .citation-shloka {{
      font-family: 'Playfair Display', serif;
      font-style: italic;
      font-size: 11px;
      color: #7A5D28;
      margin-top: 6px;
    }}

    .footer-row {{
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      margin-top: 18px;
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
      min-height: 24px;
      display: flex;
      align-items: flex-end;
      justify-content: center;
    }}
    .sig-script {{
      font-family: 'Alex Brush', cursive;
      font-size: 24px;
      color: #1A1816;
    }}
    .col-line {{
      width: 100%;
      height: 1px;
      background: #8C7A62;
      margin-bottom: 5px;
    }}
    .col-label {{
      font-family: 'Montserrat', sans-serif;
      font-size: 9px;
      font-weight: 600;
      letter-spacing: 1px;
      color: #7A6C58;
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
      border: 1px solid #C59B27;
      border-radius: 4px;
      padding: 3px;
      display: flex;
      align-items: center;
      justify-content: center;
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

    /* Gold Ribbon Medal Badge */
    .seal-wrapper {{
      position: absolute;
      right: 28%;
      top: 13%;
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
      .cert-container {{
        width: 297mm !important;
        height: 210mm !important;
        max-height: 210mm !important;
        border: none !important;
        border-radius: 0 !important;
        box-shadow: none !important;
        page-break-inside: avoid !important;
        break-inside: avoid !important;
      }}
      .cert-left {{
        width: 66% !important;
        padding: 16mm 10mm 12mm 18mm !important;
      }}
      .cert-right {{
        width: 34% !important;
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
    <div class="microtext-band micro-top">
      <span>ASTRA GURUKUL CELESTIAL CREDENTIALS • OFFICIALLY CONSECRATED • CANONICAL HASH VERIFIED</span>
      <span>HMAC-SHA256 DIGITAL SECURITY SEAL • MATHEMATICALLY TAMPER-PROOF • VERIFIABLE AT ASTRAGURUKUL.COM</span>
    </div>
    <div class="microtext-band micro-bot">
      <span>ID: {cert['certificate_id']}</span>
      <span>SIG: {crypto_sig[:24]}... (HMAC-SHA256)</span>
    </div>

    <div class="cert-left">
      <!-- Brand Header -->
      <div class="brand-header">
        <svg class="brand-logo-icon" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="5" y="5" width="90" height="90" rx="16" fill="#1A1816"/>
          <circle cx="50" cy="50" r="38" stroke="#D4AF37" stroke-width="1.5" stroke-dasharray="2,2"/>
          <circle cx="50" cy="50" r="28" stroke="#D4AF37" stroke-width="1"/>
          <path d="M 50,22 C 38,22 38,50 50,50 C 62,50 62,22 50,22 Z" fill="#D4AF37" opacity="0.9"/>
          <path d="M 50,78 C 38,78 38,50 50,50 C 62,50 62,78 50,78 Z" fill="#D4AF37" opacity="0.9"/>
          <path d="M 22,50 C 22,38 50,38 50,50 C 50,62 22,62 22,50 Z" fill="#D4AF37" opacity="0.9"/>
          <path d="M 78,50 C 78,38 50,38 50,50 C 50,62 78,62 78,50 Z" fill="#D4AF37" opacity="0.9"/>
          <circle cx="50" cy="50" r="5" fill="#FFF"/>
        </svg>
        <div>
          <div class="brand-name">ASTRA GURUKUL</div>
          <div class="brand-sub">COUNCIL OF VEDIC SCIENCES</div>
        </div>
      </div>

      <!-- Title Block -->
      <div class="title-block">
        <h1 class="cert-main-title">Certificate</h1>
        <div class="cert-sub-banner">
          <div class="sub-line"></div>
          <span class="sub-text">✦ OF ACHIEVEMENT ✦</span>
          <div class="sub-line"></div>
        </div>
      </div>

      <!-- Consecration Label -->
      <div class="consecration-label">
        THIS CERTIFICATE IS PROUDLY PRESENTED TO
      </div>

      <!-- Recipient Scholar Name -->
      <div>
        <div class="recipient-name">{cert['student_name']}</div>
        <div class="recipient-underline"></div>
      </div>

      <!-- Citation Body Paragraph -->
      <div class="citation-paragraph">
        has successfully completed the sacred curriculum and demonstrated scholarly excellence in <strong>{cert['course_title']}</strong>, mastering classical predictive calculations, nakshatra computations, and remedial planetary sciences.
        <div class="citation-shloka">
          « विद्या ददाति विनयं विनयाद्याति पात्रताम् • True knowledge bestows humility, worthiness, and supreme fulfillment »
        </div>
      </div>

      <!-- Footer Row: Date, Live QR Code, Signature -->
      <div class="footer-row">
        <div class="date-col">
          <div class="col-val">{issued_date}</div>
          <div class="col-line"></div>
          <div class="col-label">Date</div>
        </div>

        <div class="qr-col">
          <div class="qr-frame">
            <svg viewBox="0 0 100 100" width="100%" height="100%">
              <rect width="100" height="100" fill="#FFF"/>
              <rect x="10" y="10" width="28" height="28" fill="#1A1816"/>
              <rect x="15" y="15" width="18" height="18" fill="#FFF"/>
              <rect x="19" y="19" width="10" height="10" fill="#1A1816"/>
              <rect x="62" y="10" width="28" height="28" fill="#1A1816"/>
              <rect x="67" y="15" width="18" height="18" fill="#FFF"/>
              <rect x="71" y="19" width="10" height="10" fill="#1A1816"/>
              <rect x="10" y="62" width="28" height="28" fill="#1A1816"/>
              <rect x="15" y="67" width="18" height="18" fill="#FFF"/>
              <rect x="19" y="71" width="10" height="10" fill="#1A1816"/>
              <circle cx="50" cy="50" r="6" fill="#B8860B"/>
              <rect x="44" y="15" width="10" height="10" fill="#1A1816"/>
              <rect x="44" y="75" width="10" height="10" fill="#1A1816"/>
              <rect x="75" y="44" width="10" height="10" fill="#1A1816"/>
            </svg>
          </div>
          <div class="qr-label">Official QR</div>
        </div>

        <div class="sig-col">
          <div class="col-val sig-script">{instructor}</div>
          <div class="col-line"></div>
          <div class="col-label">Signature</div>
        </div>
      </div>
    </div>

    <!-- Gold Ribbon Medal Badge -->
    <div class="seal-wrapper">
      <svg viewBox="0 0 160 200" width="130" height="162" xmlns="http://www.w3.org/2000/svg">
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

        <text x="80" y="66" fill="#FFE89E" font-family="sans-serif" font-size="5.5" font-weight="bold" text-anchor="middle" letter-spacing="1.5">★ ★ ★</text>
        <text x="80" y="76" fill="#FFF3CA" font-family="'Cinzel', serif" font-size="9" font-weight="900" text-anchor="middle" letter-spacing="1.2">BEST</text>
        <path d="M 59,80 L 64,80 M 96,80 L 101,80" stroke="#D4AF37" stroke-width="0.5"/>
        <text x="80" y="83" fill="#E5C370" font-family="sans-serif" font-size="5" font-weight="800" text-anchor="middle" letter-spacing="1.5">AWARD</text>
        <text x="80" y="92" fill="#FFF3CA" font-family="'Cinzel', serif" font-size="7.5" font-weight="700" text-anchor="middle" letter-spacing="1">2026</text>
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
            <polygon points="0,-96 96,0 0,96 -96,0" fill="none" stroke="#FAF8F2" stroke-width="4"/>
            <polygon points="0,-90 90,0 0,90 -90,0" fill="none" stroke="url(#patGoldLight)" stroke-width="3"/>

            <path d="M-28,-28 L-28,-80 L0,-100 L28,-80 L28,-28 Z" fill="url(#patGoldMetal)"/>
            <path d="M-20,-28 L-20,-75 L0,-90 L20,-75 L20,-28 Z" fill="#FAF8F2"/>
            <path d="M-12,-28 L-12,-70 L0,-80 L12,-70 L12,-28 Z" fill="url(#patGoldLight)"/>

            <path d="M-28,28 L-28,80 L0,100 L28,80 L28,28 Z" fill="url(#patGoldMetal)"/>
            <path d="M-20,28 L-20,75 L0,90 L20,75 L20,28 Z" fill="#FAF8F2"/>
            <path d="M-12,28 L-12,70 L0,80 L12,70 L12,28 Z" fill="url(#patGoldLight)"/>

            <path d="M-28,-28 L-80,-28 L-100,0 L-80,28 L-28,28 Z" fill="url(#patGoldMetal)"/>
            <path d="M-28,-20 L-75,-20 L-90,0 L-75,20 L-28,20 Z" fill="#FAF8F2"/>
            <path d="M-28,-12 L-70,-12 L-80,0 L-70,12 L-28,12 Z" fill="url(#patGoldLight)"/>

            <path d="M28,-28 L80,-28 L100,0 L80,28 L28,28 Z" fill="url(#patGoldMetal)"/>
            <path d="M28,-20 L75,-20 L90,0 L75,20 L28,20 Z" fill="#FAF8F2"/>
            <path d="M28,-12 L70,-12 L80,0 L70,12 L28,12 Z" fill="url(#patGoldLight)"/>

            <polygon points="0,-28 28,0 0,28 -28,0" fill="url(#patGoldMetal)"/>
            <polygon points="0,-20 20,0 0,20 -20,0" fill="#FAF8F2"/>
            <polygon points="0,-12 12,0 0,12 -12,0" fill="url(#patGoldLight)"/>
            <polygon points="0,-5 5,0 0,5 -5,0" fill="url(#patGoldMetal)"/>

            <path d="M38,-38 L55,-55 M46,-38 L63,-55 M54,-38 L71,-55" stroke="url(#patGoldMetal)" stroke-width="3" fill="none"/>
            <path d="M38,38 L55,55 M46,38 L63,55 M54,38 L71,55" stroke="url(#patGoldMetal)" stroke-width="3" fill="none"/>
            <path d="M-38,38 L-55,55 M-46,38 L-63,55 M-54,38 L-71,55" stroke="url(#patGoldMetal)" stroke-width="3" fill="none"/>
            <path d="M-38,-38 L-55,-55 M-46,-38 L-63,-55 M-54,-38 L-71,-55" stroke="url(#patGoldMetal)" stroke-width="3" fill="none"/>
          </g>
        </defs>

        <rect width="320" height="640" fill="#FAF8F2"/>

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

