"""Admin Endpoints for Astra Gurukul Courses, Modules & Video Lessons."""

from typing import Annotated
from datetime import datetime, timezone

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import AdminUser
from app.core.exceptions import NotFoundError
from app.models.course import Course, CourseLesson, CourseSection
from app.schemas.common import ApiResponse
from app.schemas.course import (
    BunnyCreateVideoRequest,
    BunnyCreateVideoResponse,
    CourseCreateRequest,
    CourseDetailOut,
    CourseLessonCreateRequest,
    CourseLessonOut,
    CourseLessonUpdateRequest,
    CourseListItemOut,
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
    discount = 0
    if payload.mrp > 0 and payload.mrp > payload.price:
        discount = int(round(((payload.mrp - payload.price) / payload.mrp) * 100))

    course = Course(
        title=payload.title,
        slug=payload.slug,
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
    """Updates course details, pricing, or publishing status."""
    course = await Course.find_one(Course.id == course_id, Course.is_deleted == False)
    if not course:
        raise NotFoundError("Course not found")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(course, k, v)

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
    """Soft deletes a course from the catalog."""
    course = await Course.find_one(Course.id == course_id)
    if not course:
        raise NotFoundError("Course not found")

    course.is_deleted = True
    course.is_published = False
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
    lesson = await CourseService.admin_create_lesson(
        course_id=course_id,
        section_id=PydanticObjectId(payload.section_id),
        title=payload.title,
        order=payload.order,
        duration_minutes=payload.duration_minutes,
        video_provider=payload.video_provider,
        video_id=payload.video_id,
        library_id=payload.library_id,
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

    await lesson.delete()

    # Recalculate course lessons and duration
    course = await Course.find_one(Course.id == course_id)
    if course:
        remaining = await CourseLesson.find(CourseLesson.course_id == course_id, CourseLesson.is_published == True).to_list()
        course.total_lessons = len(remaining)
        course.duration_hours = round(sum(l.duration_minutes for l in remaining) / 60.0, 1)
        await course.save()

    return ApiResponse(data={"message": "Lesson deleted successfully"})


# -----------------------------------------------------------------------------
# BUNNY STREAM API INTEGRATION HELPER
# -----------------------------------------------------------------------------
@router.post("/create-bunny-video", response_model=ApiResponse[BunnyCreateVideoResponse])
async def admin_create_bunny_video_placeholder(
    payload: BunnyCreateVideoRequest,
    _: AdminUser,
) -> ApiResponse[BunnyCreateVideoResponse]:
    """Calls Bunny Stream API to create a video placeholder in library 803267."""
    result = await CourseService.create_bunny_video_placeholder(title=payload.title)
    return ApiResponse(data=BunnyCreateVideoResponse(**result))
