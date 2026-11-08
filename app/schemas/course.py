"""Pydantic schemas for Astra Gurukul Courses, Modules, Lessons & Enrollments."""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class LessonResourceOut(BaseModel):
    title: str
    url: str
    type: str = "pdf"  # pdf, audio, image, link


class CourseLessonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    section_id: str
    title: str
    order: int
    duration_minutes: int
    is_free_preview: bool
    summary: str | None = None
    resources_count: int = 0
    # Video streaming details are only populated for enrolled users or free previews
    video_provider: str | None = None
    video_id: str | None = None
    is_completed: bool = False


class CourseSectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    order: int
    description: str | None = None
    lessons: list[CourseLessonOut] = Field(default_factory=list)


class CourseListItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    slug: str
    subtitle: str
    category: str
    level: str
    language: str
    instructor_name: str
    instructor_title: str
    instructor_avatar: str | None = None
    thumbnail_url: str
    price: float
    mrp: float
    discount_percent: int
    currency: str
    duration_hours: float
    total_lessons: int
    total_students: int
    average_rating: float
    rating_count: int
    is_featured: bool
    certificate_enabled: bool


class CourseDetailOut(CourseListItemOut):
    description: str
    promo_video_url: str | None = None
    promo_video_provider: str = "youtube"
    what_you_will_learn: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    sections: list[CourseSectionOut] = Field(default_factory=list)
    is_enrolled: bool = False
    user_progress_percent: float = 0.0


class CourseEnrollmentOut(BaseModel):
    id: str
    course_id: str
    course_title: str | None = None
    course_slug: str | None = None
    thumbnail_url: str | None = None
    instructor_name: str | None = None
    enrolled_at: datetime
    expires_at: datetime | None = None
    progress_percent: float
    completed_lesson_ids: list[str]
    certificate_issued: bool
    certificate_url: str | None = None


class LessonStreamResponse(BaseModel):
    """Secure playback response for an individual video lesson."""

    lesson_id: str
    title: str
    video_provider: str
    video_id: str
    library_id: str | None = None
    embed_url: str
    token: str | None = None
    expires_at: int | None = None
    watermark_text: str | None = None
    notes_markdown: str | None = None
    resources: list[LessonResourceOut] = Field(default_factory=list)


class LessonProgressUpdateRequest(BaseModel):
    watched_seconds: int = Field(..., ge=0)
    total_seconds: int = Field(..., ge=0)
    mark_completed: bool = False


class CourseCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    slug: str = Field(..., min_length=3, max_length=220)
    subtitle: str = Field("", max_length=300)
    description: str = Field(...)
    category: str = Field(default="vedic_astrology")
    level: str = Field(default="all_levels")
    language: str = Field(default="bn")
    instructor_name: str = Field(default="Pt. Acharya Rahul Sharma")
    instructor_title: str = Field(default="Senior Vedic Jyotishacharya")
    instructor_avatar: str | None = None
    instructor_bio: str | None = None
    thumbnail_url: str = Field(...)
    promo_video_url: str | None = None
    promo_video_provider: str = Field(default="youtube")
    price: float = Field(..., ge=0)
    mrp: float = Field(..., ge=0)
    certificate_enabled: bool = True
    what_you_will_learn: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class CourseUpdateRequest(BaseModel):
    title: str | None = None
    subtitle: str | None = None
    description: str | None = None
    category: str | None = None
    level: str | None = None
    language: str | None = None
    instructor_name: str | None = None
    instructor_title: str | None = None
    instructor_avatar: str | None = None
    thumbnail_url: str | None = None
    promo_video_url: str | None = None
    promo_video_provider: str | None = None
    price: float | None = None
    mrp: float | None = None
    is_published: bool | None = None
    is_featured: bool | None = None
    certificate_enabled: bool | None = None
    what_you_will_learn: list[str] | None = None
    prerequisites: list[str] | None = None
    tags: list[str] | None = None


# Order & Payment Schemas
class CourseOrderCreateResponse(BaseModel):
    free_enrolled: bool = False
    order_id: str | None = None
    amount_paise: int = 0
    amount_inr: float = 0.0
    currency: str = "INR"
    key_id: str | None = None
    course_id: str
    course_title: str
    course_slug: str


class CoursePaymentVerifyRequest(BaseModel):
    razorpay_order_id: str = Field(..., min_length=4)
    razorpay_payment_id: str = Field(..., min_length=4)
    razorpay_signature: str = Field(..., min_length=16)


# Admin Section & Lesson CRUD Schemas
class CourseSectionCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    order: int = Field(default=1, ge=1)
    description: str | None = None


class CourseSectionUpdateRequest(BaseModel):
    title: str | None = None
    order: int | None = None
    description: str | None = None


class CourseLessonCreateRequest(BaseModel):
    section_id: str
    title: str = Field(..., min_length=2, max_length=250)
    order: int = Field(default=1, ge=1)
    duration_minutes: int = Field(default=0, ge=0)
    video_provider: str = Field(default="bunny_stream")  # bunny_stream, youtube_unlisted
    video_id: str = Field(..., min_length=1)  # Bunny video GUID or YouTube ID
    library_id: str | None = None
    is_free_preview: bool = False
    summary: str | None = None
    notes_markdown: str | None = None
    resources: list[LessonResourceOut] = Field(default_factory=list)


class CourseLessonUpdateRequest(BaseModel):
    section_id: str | None = None
    title: str | None = None
    order: int | None = None
    duration_minutes: int | None = None
    video_provider: str | None = None
    video_id: str | None = None
    library_id: str | None = None
    is_free_preview: bool | None = None
    summary: str | None = None
    notes_markdown: str | None = None
    resources: list[LessonResourceOut] | None = None
    is_published: bool | None = None


class BunnyCreateVideoRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=250)


class BunnyCreateVideoResponse(BaseModel):
    video_id: str
    library_id: str
    title: str
    upload_url: str | None = None
