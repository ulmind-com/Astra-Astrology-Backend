"""Admin Endpoints for Astra Gurukul Courses, Modules & Video Lessons."""

from typing import Annotated
import asyncio
from datetime import datetime, timezone

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from loguru import logger

from app.api.dependencies import AdminUser
from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.models.course import Course, CourseLesson, CourseSection
from app.schemas.common import ApiResponse
from app.services.storage import safe_delete_cloudinary_image, upload_file
from app.schemas.course import (
    AdminCourseQuestionAnswerRequest,
    AdminCourseQuestionDetailOut,
    AdminCourseQuestionListResponse,
    AdminCourseQuestionUpdateRequest,
    BunnyCreateVideoRequest,
    BunnyCreateVideoResponse,
    CourseCreateRequest,
    CourseDetailOut,
    CourseLessonCreateRequest,
    CourseLessonOut,
    CourseLessonUpdateRequest,
    CourseListItemOut,
    CourseQuestionAnswerOut,
    CourseSectionCreateRequest,
    CourseSectionOut,
    CourseSectionUpdateRequest,
    CourseUpdateRequest,
)
from app.services.course_service import CourseService

router = APIRouter(prefix="/admin/courses", tags=["admin-courses"])


@router.get("", response_model=ApiResponse[list[CourseListItemOut]])
async def admin_list_courses(
    _: AdminUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    skip: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[list[CourseListItemOut]]:
    """Lists all courses including drafts and unlisted courses for administrators."""
    courses = (
        await Course.find(Course.is_deleted == False)
        .sort([("created_at", -1)])
        .skip(skip)
        .limit(limit)
        .to_list()
    )
    items = [
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
        )
        for c in courses
    ]
    return ApiResponse(data=items)


@router.post("", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def admin_create_course(
    payload: CourseCreateRequest,
    _: AdminUser,
) -> ApiResponse[dict]:
    """Creates a new course entry in the Gurukul catalog."""
    import re
    import secrets

    discount = 0
    if payload.mrp > 0 and payload.mrp > payload.price:
        discount = int(round(((payload.mrp - payload.price) / payload.mrp) * 100))

    # Clean and validate slug
    raw_slug = (payload.slug or "").strip().lower()
    clean_slug = re.sub(r"[^a-z0-9]+", "-", raw_slug).strip("-")
    if not clean_slug:
        clean_slug = re.sub(r"[^a-z0-9]+", "-", (payload.title or "course").strip().lower()).strip("-")
    if not clean_slug:
        clean_slug = f"course-{secrets.token_hex(4)}"

    # Ensure unique slug across active courses so courses never collide
    unique_slug = clean_slug
    counter = 1
    while await Course.find_one(Course.slug == unique_slug, Course.is_deleted == False):
        counter += 1
        unique_slug = f"{clean_slug}-{counter}"

    course = Course(
        title=payload.title,
        slug=unique_slug,
        subtitle=payload.subtitle,
        description=payload.description,
        category=payload.category,
        level=payload.level,
        language=payload.language,
        instructor_name=payload.instructor_name,
        instructor_title=payload.instructor_title,
        instructor_avatar=payload.instructor_avatar,
        instructor_bio=payload.instructor_bio,
        thumbnail_url=payload.thumbnail_url,
        promo_video_url=payload.promo_video_url,
        promo_video_provider=payload.promo_video_provider,
        price=payload.price,
        mrp=payload.mrp,
        discount_percent=discount,
        certificate_enabled=payload.certificate_enabled,
        what_you_will_learn=payload.what_you_will_learn,
        prerequisites=payload.prerequisites,
        tags=payload.tags,
    )
    await course.insert()
    return ApiResponse(data={"id": str(course.id), "slug": course.slug, "message": "Course created successfully"})


# -----------------------------------------------------------------------------
# BUNNY STREAM INTEGRATION
# -----------------------------------------------------------------------------
@router.post("/create-bunny-video", response_model=ApiResponse[BunnyCreateVideoResponse])
async def admin_create_bunny_video_placeholder(
    payload: BunnyCreateVideoRequest,
    _: AdminUser,
) -> ApiResponse[BunnyCreateVideoResponse]:
    """Calls Bunny Stream API to create a video placeholder in library 803267."""
    clean_title = (payload.title or "").strip()
    if len(clean_title) < 2:
        clean_title = f"Lecture Video {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}"
    result = await CourseService.create_bunny_video_placeholder(title=clean_title)
    return ApiResponse(data=BunnyCreateVideoResponse(**result))


# -----------------------------------------------------------------------------
# GURUKUL JIGYASA (ADMIN Q&A INQUIRY MANAGEMENT)
# (Registered before /{course_id} to prevent path parameter shadowing)
# -----------------------------------------------------------------------------
@router.get("/questions", response_model=ApiResponse[AdminCourseQuestionListResponse])
async def admin_list_course_questions(
    _: AdminUser,
    course_id: Annotated[str | None, Query(description="Filter by Course ID")] = None,
    lesson_id: Annotated[str | None, Query(description="Filter by Lesson ID")] = None,
    status: Annotated[str, Query(description="all, unanswered, answered, resolved")] = "all",
    search: Annotated[str | None, Query(description="Search in student name/email/question text")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    skip: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[AdminCourseQuestionListResponse]:
    """Lists all Gurukul Jigyasa student inquiries with video, course & student metadata."""
    cid_oid = PydanticObjectId(course_id) if course_id and PydanticObjectId.is_valid(course_id) else None
    lid_oid = PydanticObjectId(lesson_id) if lesson_id and PydanticObjectId.is_valid(lesson_id) else None

    data = await CourseService.admin_list_questions(
        course_id=cid_oid,
        lesson_id=lid_oid,
        status=status,
        search=search,
        limit=limit,
        skip=skip,
    )
    return ApiResponse(data=AdminCourseQuestionListResponse(**data))


@router.post("/questions/{question_id}/answers", response_model=ApiResponse[CourseQuestionAnswerOut])
async def admin_answer_question(
    question_id: PydanticObjectId,
    payload: AdminCourseQuestionAnswerRequest,
    admin: AdminUser,
) -> ApiResponse[CourseQuestionAnswerOut]:
    """Posts an official Acharya answer to a student question thread."""
    ans = await CourseService.answer_question(
        user=admin,
        question_id=question_id,
        content=payload.content,
        is_official=True,
        mark_resolved=payload.mark_resolved,
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
    return ApiResponse(data=out, message="Official Gurukul answer posted successfully!")


@router.patch("/questions/{question_id}", response_model=ApiResponse[dict])
async def admin_update_question_status(
    question_id: PydanticObjectId,
    payload: AdminCourseQuestionUpdateRequest,
    _: AdminUser,
) -> ApiResponse[dict]:
    """Updates question resolution status, pin status, or moderation visibility."""
    q = await CourseService.admin_update_question(
        question_id=question_id,
        is_resolved=payload.is_resolved,
        is_pinned=payload.is_pinned,
        is_hidden=payload.is_hidden,
    )
    return ApiResponse(
        data={
            "id": str(q.id),
            "is_resolved": q.is_resolved,
            "is_pinned": q.is_pinned,
            "is_hidden": q.is_hidden,
        },
        message="Question status updated",
    )


@router.delete("/questions/{question_id}", response_model=ApiResponse[dict])
async def admin_delete_question(
    question_id: PydanticObjectId,
    _: AdminUser,
) -> ApiResponse[dict]:
    """Deletes a question thread."""
    await CourseService.admin_delete_question(question_id)
    return ApiResponse(data={"message": "Question deleted successfully"})


@router.delete("/questions/{question_id}/answers/{answer_id}", response_model=ApiResponse[dict])
async def admin_delete_answer(
    question_id: PydanticObjectId,
    answer_id: str,
    _: AdminUser,
) -> ApiResponse[dict]:
    """Deletes an answer inside a question thread."""
    await CourseService.admin_delete_answer(question_id, answer_id)
    return ApiResponse(data={"message": "Answer deleted successfully"})


@router.post("/upload-thumbnail", response_model=ApiResponse[dict[str, str]])
async def admin_upload_course_thumbnail(
    file: UploadFile = File(...),
    _: AdminUser = None,
) -> ApiResponse[dict[str, str]]:
    """Uploads a course thumbnail with 16:9 WebP compression specifically into courses folder."""
    COURSE_THUMBNAIL_TRANSFORMATION = [
        {"width": 1280, "height": 720, "crop": "fill", "aspect_ratio": "16:9"},
        {"quality": "auto:good"},
        {"fetch_format": "auto"},
    ]
    result = await upload_file(
        file,
        folder="courses/thumbnails",
        transformation=COURSE_THUMBNAIL_TRANSFORMATION,
        image_format="webp",
    )
    return ApiResponse(
        data={
            "url": result.url,
            "secure_url": result.url,
            "public_id": result.public_id,
            "format": result.format or "webp",
        },
        message="Course thumbnail uploaded and compressed successfully.",
    )


@router.get("/{course_id}", response_model=ApiResponse[CourseDetailOut])
async def admin_get_course_detail(
    course_id: PydanticObjectId,
    _: AdminUser,
) -> ApiResponse[CourseDetailOut]:
    """Retrieves full course details with all sections and lessons for admin curriculum editing."""
    course = await Course.find_one(Course.id == course_id, Course.is_deleted == False)
    if not course:
        raise NotFoundError("Course not found")

    sections = await CourseSection.find(CourseSection.course_id == course.id).sort([("order", 1)]).to_list()
    sections_out = []
    for s in sections:
        lessons = await CourseLesson.find(CourseLesson.section_id == s.id).sort([("order", 1)]).to_list()
        sections_out.append(
            CourseSectionOut(
                id=str(s.id),
                title=s.title,
                order=s.order,
                description=s.description,
                lessons=[
                    CourseLessonOut(
                        id=str(l.id),
                        section_id=str(l.section_id),
                        title=l.title,
                        order=l.order,
                        duration_minutes=l.duration_minutes,
                        is_free_preview=l.is_free_preview,
                        summary=l.summary,
                        resources_count=len(l.resources or []),
                        video_provider=l.video_provider,
                        video_id=l.video_id,
                        is_completed=False,
                    )
                    for l in lessons
                ],
            )
        )

    data = CourseDetailOut(
        id=str(course.id),
        title=course.title,
        slug=course.slug,
        subtitle=course.subtitle,
        category=course.category,
        level=course.level,
        language=course.language,
        instructor_name=course.instructor_name,
        instructor_title=course.instructor_title,
        instructor_avatar=course.instructor_avatar,
        thumbnail_url=course.thumbnail_url,
        price=course.price,
        mrp=course.mrp,
        discount_percent=course.discount_percent,
        currency=course.currency,
        duration_hours=course.duration_hours,
        total_lessons=course.total_lessons,
        total_students=course.total_students,
        average_rating=course.average_rating,
        rating_count=course.rating_count,
        is_featured=course.is_featured,
        certificate_enabled=course.certificate_enabled,
        description=course.description,
        promo_video_url=course.promo_video_url,
        promo_video_provider=course.promo_video_provider,
        what_you_will_learn=course.what_you_will_learn,
        prerequisites=course.prerequisites,
        tags=course.tags,
        sections=sections_out,
        is_enrolled=True,
        user_progress_percent=0.0,
    )
    return ApiResponse(data=data)


@router.put("/{course_id}", response_model=ApiResponse[dict])
async def admin_update_course(
    course_id: PydanticObjectId,
    payload: CourseUpdateRequest,
    _: AdminUser,
) -> ApiResponse[dict]:
    """Updates course details, pricing, or publishing status with Cloudinary garbage-collection."""
    course = await Course.find_one(Course.id == course_id, Course.is_deleted == False)
    if not course:
        raise NotFoundError("Course not found")

    old_thumbnail = course.thumbnail_url
    new_thumbnail = payload.thumbnail_url
    old_avatar = course.instructor_avatar
    new_avatar = payload.instructor_avatar
    old_promo = course.promo_video_url
    old_promo_provider = course.promo_video_provider
    new_promo = payload.promo_video_url

    # Slug uniqueness check if updated
    if payload.slug is not None:
        import re
        new_slug = re.sub(r"[^a-z0-9]+", "-", payload.slug.strip().lower()).strip("-")
        if new_slug and new_slug != course.slug:
            existing = await Course.find_one(Course.slug == new_slug, Course.id != course.id, Course.is_deleted == False)
            if existing:
                raise BadRequestError(f"A course with slug '{new_slug}' already exists. Please choose a different slug.")
            course.slug = new_slug

    data = payload.model_dump(exclude_unset=True)
    # Don't re-assign slug from data since handled above
    data.pop("slug", None)
    for k, v in data.items():
        setattr(course, k, v)

    # Cloudinary Auto-Cleanup: If thumbnail is changed or cleared, purge the old Cloudinary asset
    if old_thumbnail and (payload.thumbnail_url is not None) and (new_thumbnail != old_thumbnail):
        logger.info(f"Course {course_id} thumbnail replaced/cleared. Purging old asset: {old_thumbnail}")
        asyncio.create_task(safe_delete_cloudinary_image(old_thumbnail))

    # Cloudinary Auto-Cleanup: If instructor avatar is changed or cleared, purge the old Cloudinary asset
    if old_avatar and (payload.instructor_avatar is not None) and (new_avatar != old_avatar):
        logger.info(f"Course {course_id} avatar replaced/cleared. Purging old asset: {old_avatar}")
        asyncio.create_task(safe_delete_cloudinary_image(old_avatar))

    # Bunny Stream Auto-Cleanup: If promo video is changed or cleared, purge the old Bunny asset
    if old_promo and (payload.promo_video_url is not None) and (new_promo != old_promo):
        if old_promo_provider == "bunny_stream" or "bunny" in str(old_promo) or (len(str(old_promo)) > 20 and "youtube" not in str(old_promo).lower()):
            logger.info(f"Course {course_id} promo video changed/cleared. Purging old Bunny asset: {old_promo}")
            asyncio.create_task(CourseService.safe_delete_bunny_video(old_promo))

    if course.mrp > 0 and course.mrp > course.price:
        course.discount_percent = int(round(((course.mrp - course.price) / course.mrp) * 100))

    course.updated_at = datetime.now(timezone.utc)
    await course.save()
    return ApiResponse(data={"id": str(course.id), "message": "Course updated successfully"})


@router.delete("/{course_id}", response_model=ApiResponse[dict])
async def admin_delete_course(
    course_id: PydanticObjectId,
    _: AdminUser,
) -> ApiResponse[dict]:
    """Soft deletes a course from the catalog and cleans up Cloudinary and Bunny media assets."""
    course = await Course.find_one(Course.id == course_id)
    if not course:
        raise NotFoundError("Course not found")

    if course.thumbnail_url:
        logger.info(f"Course {course_id} deleted. Purging thumbnail from Cloudinary: {course.thumbnail_url}")
        asyncio.create_task(safe_delete_cloudinary_image(course.thumbnail_url))

    if course.instructor_avatar:
        logger.info(f"Course {course_id} deleted. Purging instructor avatar from Cloudinary: {course.instructor_avatar}")
        asyncio.create_task(safe_delete_cloudinary_image(course.instructor_avatar))

    # Bunny Stream Auto-Cleanup: Purge promo video
    if course.promo_video_url and (course.promo_video_provider == "bunny_stream" or "bunny" in str(course.promo_video_url) or len(str(course.promo_video_url)) > 20):
        logger.info(f"Course {course_id} deleted. Purging promo video from Bunny: {course.promo_video_url}")
        asyncio.create_task(CourseService.safe_delete_bunny_video(course.promo_video_url))

    # Bunny Stream Auto-Cleanup: Purge all lesson videos belonging to this course
    course_lessons = await CourseLesson.find(CourseLesson.course_id == course_id).to_list()
    for l in course_lessons:
        if l.video_id:
            logger.info(f"Course {course_id} deleted. Purging Bunny video {l.video_id} for lesson {l.id}")
            asyncio.create_task(CourseService.safe_delete_bunny_video(l.video_id, l.library_id))

    import secrets

    course.is_deleted = True
    course.is_published = False
    # Free up slug so a new course can use it without conflicts
    course.slug = f"{course.slug}-deleted-{secrets.token_hex(4)}"
    course.updated_at = datetime.now(timezone.utc)
    await course.save()
    return ApiResponse(data={"message": "Course deleted successfully"})


# -----------------------------------------------------------------------------
# SECTIONS & MODULES MANAGEMENT
# -----------------------------------------------------------------------------
@router.post("/{course_id}/sections", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def admin_create_section(
    course_id: PydanticObjectId,
    payload: CourseSectionCreateRequest,
    _: AdminUser,
) -> ApiResponse[dict]:
    section = await CourseService.admin_create_section(
        course_id=course_id,
        title=payload.title,
        order=payload.order,
        description=payload.description,
    )
    return ApiResponse(data={"id": str(section.id), "title": section.title, "order": section.order})


@router.put("/{course_id}/sections/{section_id}", response_model=ApiResponse[dict])
async def admin_update_section(
    course_id: PydanticObjectId,
    section_id: PydanticObjectId,
    payload: CourseSectionUpdateRequest,
    _: AdminUser,
) -> ApiResponse[dict]:
    section = await CourseSection.find_one(CourseSection.id == section_id, CourseSection.course_id == course_id)
    if not section:
        raise NotFoundError("Section not found")

    if payload.title is not None:
        section.title = payload.title
    if payload.order is not None:
        section.order = payload.order
    if payload.description is not None:
        section.description = payload.description

    await section.save()
    return ApiResponse(data={"id": str(section.id), "title": section.title, "order": section.order})


@router.delete("/{course_id}/sections/{section_id}", response_model=ApiResponse[dict])
async def admin_delete_section(
    course_id: PydanticObjectId,
    section_id: PydanticObjectId,
    _: AdminUser,
) -> ApiResponse[dict]:
    section = await CourseSection.find_one(CourseSection.id == section_id, CourseSection.course_id == course_id)
    if not section:
        raise NotFoundError("Section not found")

    # Bunny Stream Auto-Cleanup: Purge all videos belonging to lessons in this section
    lessons = await CourseLesson.find(CourseLesson.section_id == section_id).to_list()
    for l in lessons:
        if l.video_id:
            logger.info(f"Section {section_id} deleted. Purging Bunny video {l.video_id} for lesson {l.id}")
            asyncio.create_task(CourseService.safe_delete_bunny_video(l.video_id, l.library_id))

    # Delete associated lessons
    await CourseLesson.find(CourseLesson.section_id == section_id).delete()
    await section.delete()
    return ApiResponse(data={"message": "Section and lessons deleted successfully"})


# -----------------------------------------------------------------------------
# LESSONS & VIDEO MANAGEMENT
# -----------------------------------------------------------------------------
@router.post("/{course_id}/lessons", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def admin_create_lesson(
    course_id: PydanticObjectId,
    payload: CourseLessonCreateRequest,
    _: AdminUser,
) -> ApiResponse[dict]:
    clean_sec = payload.section_id.strip()
    try:
        sec_oid = PydanticObjectId(clean_sec)
    except Exception:
        raise NotFoundError("Invalid Section ID format")

    lesson = await CourseService.admin_create_lesson(
        course_id=course_id,
        section_id=sec_oid,
        title=payload.title.strip() or "Untitled Lesson",
        order=int(payload.order),
        duration_minutes=int(payload.duration_minutes),
        video_provider=payload.video_provider,
        video_id=payload.video_id.strip(),
        library_id=payload.library_id or settings.BUNNY_STREAM_LIBRARY_ID,
        is_free_preview=payload.is_free_preview,
        summary=payload.summary,
        notes_markdown=payload.notes_markdown,
        resources=[r.model_dump() for r in payload.resources] if payload.resources else [],
    )
    return ApiResponse(data={"id": str(lesson.id), "title": lesson.title, "order": lesson.order})


@router.put("/{course_id}/lessons/{lesson_id}", response_model=ApiResponse[dict])
async def admin_update_lesson(
    course_id: PydanticObjectId,
    lesson_id: PydanticObjectId,
    payload: CourseLessonUpdateRequest,
    _: AdminUser,
) -> ApiResponse[dict]:
    lesson = await CourseLesson.find_one(CourseLesson.id == lesson_id, CourseLesson.course_id == course_id)
    if not lesson:
        raise NotFoundError("Lesson not found")

    old_video_id = lesson.video_id
    old_library_id = lesson.library_id
    old_provider = lesson.video_provider
    new_video_id = payload.video_id

    # Bunny Stream Auto-Cleanup: If old video exists and is replaced or cleared, purge from Bunny
    if old_video_id and (new_video_id is not None) and (new_video_id.strip() != old_video_id.strip()):
        if old_provider == "bunny_stream" or len(old_video_id) > 15:
            logger.info(f"Lesson {lesson_id} video changed from '{old_video_id}' to '{new_video_id}'. Purging old Bunny video.")
            asyncio.create_task(CourseService.safe_delete_bunny_video(old_video_id, old_library_id))

    data = payload.model_dump(exclude_unset=True)
    if "resources" in data and data["resources"] is not None:
        data["resources"] = [r.model_dump() if hasattr(r, "model_dump") else r for r in payload.resources or []]

    for k, v in data.items():
        setattr(lesson, k, v)

    lesson.updated_at = datetime.now(timezone.utc)
    await lesson.save()
    return ApiResponse(data={"id": str(lesson.id), "title": lesson.title, "order": lesson.order})


@router.delete("/{course_id}/lessons/{lesson_id}", response_model=ApiResponse[dict])
async def admin_delete_lesson(
    course_id: PydanticObjectId,
    lesson_id: PydanticObjectId,
    _: AdminUser,
) -> ApiResponse[dict]:
    lesson = await CourseLesson.find_one(CourseLesson.id == lesson_id, CourseLesson.course_id == course_id)
    if not lesson:
        raise NotFoundError("Lesson not found")

    # Bunny Stream Auto-Cleanup: Purge video from Bunny
    if lesson.video_id and (lesson.video_provider == "bunny_stream" or len(lesson.video_id) > 15):
        logger.info(f"Lesson {lesson_id} deleted. Purging Bunny video {lesson.video_id}")
        asyncio.create_task(CourseService.safe_delete_bunny_video(lesson.video_id, lesson.library_id))

    await lesson.delete()

    # Recalculate course lessons and duration
    course = await Course.find_one(Course.id == course_id)
    if course:
        remaining = await CourseLesson.find(CourseLesson.course_id == course_id, CourseLesson.is_published == True).to_list()
        course.total_lessons = len(remaining)
        course.duration_hours = round(sum(l.duration_minutes for l in remaining) / 60.0, 1)
        await course.save()

    return ApiResponse(data={"message": "Lesson deleted successfully"})


